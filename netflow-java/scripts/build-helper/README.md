# Maven Proxy Build Helper

This directory contains scripts to automate Maven builds in restricted network environments (e.g., containers or corporate networks with proxy-only access).

## Problem Solved

Maven has known issues with HTTPS proxy authentication that cause builds to fail with `407 Proxy Authentication Required` or DNS resolution errors in network-isolated environments. This script suite bypasses these issues by:

1. **Starting a local HTTP server** that acts as a Maven repository proxy
2. **Using `curl`** (which handles proxy auth correctly) to download artifacts transparently
3. **Caching artifacts locally** to avoid repeated network calls
4. **Configuring Maven** to use the local proxy instead of connecting directly to Maven Central

## Quick Start

### Prerequisites

- Python 3.6+
- `curl` command-line tool
- Maven 3.6.0+
- Java 11+
- Environment variable `https_proxy` set (if behind a corporate proxy)

### Building

From the project root, run:

```bash
# Using the bash wrapper (simplest)
./scripts/build-helper/build.sh clean compile

# Or using Python directly
python3 scripts/build-helper/maven-proxy-build.py clean compile
```

### Common Maven Goals

```bash
# Compile only
./scripts/build-helper/build.sh clean compile

# Build JAR
./scripts/build-helper/build.sh clean package

# Run tests
./scripts/build-helper/build.sh clean test

# Full build with integration tests
./scripts/build-helper/build.sh clean install
```

## How It Works

### Architecture

```
Your Maven Build
       ↓
settings.xml (configured)
       ↓
Maven looks for artifacts at http://127.0.0.1:18080
       ↓
Local Python HTTP Server
       ├─ [Cache HIT] → Serve from ~/.m2/repository
       └─ [Cache MISS] →
          ├─ curl --proxy $https_proxy
          ├─ Download from https://repo.maven.apache.org/maven2
          └─ Cache locally + serve
       ↓
Build continues with artifacts
```

### Why This Approach Works

| Issue | Maven Default | This Script |
|-------|---------------|-------------|
| **HTTPS CONNECT auth (407)** | Apache HttpClient fails | curl handles it correctly |
| **DNS resolution** | Java's DNS may fail | curl resolves through proxy |
| **Proxy credentials** | Passed via Java system properties | Passed via curl env var |
| **Auth scheme support** | Limited by Java version | Full support via curl |
| **Proxy bypass/auth conflict** | Can occur with JAVA_TOOL_OPTIONS | Avoided by using localhost |

## Command-Line Options

```
python3 maven-proxy-build.py [OPTIONS] [MAVEN_GOALS]

Options:
  --port PORT              Local proxy server port (default: 18080)
  --no-clean-cache         Don't clear .lastUpdated files
  --verbose                Show proxy server request logs
  -h, --help              Show this help message

Examples:
  python3 maven-proxy-build.py clean compile
  python3 maven-proxy-build.py --port 19090 clean package
  python3 maven-proxy-build.py --verbose clean test
  python3 maven-proxy-build.py --no-clean-cache clean compile
```

## Troubleshooting

### Build fails with "artifacts cannot be found"

**Check 1: Is your proxy set?**
```bash
echo $https_proxy
```

If empty and you're behind a corporate proxy, set it:
```bash
export https_proxy=http://username:password@proxy.company.com:8080
```

**Check 2: Is Python running?**
```bash
# In another terminal, verify the proxy server is responding
curl -s http://127.0.0.1:18080/org/apache/maven/maven-core/3.9.0/maven-core-3.9.0.pom
```

**Check 3: Check settings.xml was created**
```bash
cat ~/.m2/settings.xml | head -20
```

### Build hangs or times out

**Solution:** Increase the timeout or use `--verbose`:
```bash
./scripts/build-helper/build.sh --verbose clean compile
```

The `--verbose` flag shows proxy requests, helping diagnose slow network issues.

### "Port already in use" error

**Solution:** Use a different port:
```bash
python3 scripts/build-helper/maven-proxy-build.py --port 19090 clean compile
```

### Proxy authentication fails (407 errors)

**Check 1: Verify proxy credentials in https_proxy**
```bash
# Should show: http://username:password@host:port
echo $https_proxy
```

**Check 2: Test proxy with curl directly**
```bash
curl -s --proxy $https_proxy https://repo.maven.apache.org/maven2/org/apache/maven/maven-core/3.9.0/maven-core-3.9.0.pom | head
```

If curl works but the script fails, try with `--verbose` flag.

### Maven can't find Java/Maven

**Solution:** Ensure Maven and Java are in PATH:
```bash
mvn --version
java --version
```

If these fail, install them or update PATH.

## How to Integrate Into CI/CD

### Docker Example

```dockerfile
FROM maven:3.9-eclipse-temurin-17

WORKDIR /app
COPY . .

# Set proxy (or pass via build args)
ENV https_proxy=http://proxy:8080

# Run the build helper
RUN python3 scripts/build-helper/maven-proxy-build.py clean package
```

### GitHub Actions Example

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      https_proxy: ${{ secrets.CORPORATE_PROXY }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Build with Maven Proxy Helper
        run: python3 scripts/build-helper/maven-proxy-build.py clean package
```

### Jenkins Example

```groovy
pipeline {
    agent any
    environment {
        HTTPS_PROXY = credentials('corporate-proxy')
    }
    stages {
        stage('Build') {
            steps {
                sh 'python3 scripts/build-helper/maven-proxy-build.py clean package'
            }
        }
    }
}
```

## Files

- **maven-proxy-build.py** - Main Python script implementing the proxy server and Maven orchestration
- **build.sh** - Bash wrapper script for convenience (runs maven-proxy-build.py)
- **README.md** - This file

## Performance Considerations

- **First build:** Slower (downloads all dependencies via proxy)
- **Subsequent builds:** Faster (artifacts cached in `~/.m2/repository`)
- **Network-intensive operations:** Building large projects downloads hundreds of MB

To clear the cache and start fresh:
```bash
rm -rf ~/.m2/repository
```

## Security Notes

⚠️ **The `settings.xml` created by this script contains your proxy credentials in plaintext in `~/.m2/settings.xml`.**

Safeguard this file and ensure:
- `~/.m2/` is not world-readable: `chmod 700 ~/.m2`
- Don't commit `~/.m2/settings.xml` to version control
- Use environment variables for proxy credentials when possible

## Advanced Usage

### Using a Custom Maven Home

```bash
export MAVEN_HOME=/custom/path/to/maven
export PATH=$MAVEN_HOME/bin:$PATH
python3 scripts/build-helper/maven-proxy-build.py clean compile
```

### Monitoring Network Activity

```bash
# Terminal 1: Start build with verbose logging
python3 scripts/build-helper/maven-proxy-build.py --verbose clean compile

# Terminal 2: Monitor requests
watch -n 0.5 'lsof -i :18080'
```

### Debugging Artifact Resolution

```bash
# Show Maven's full dependency tree
./scripts/build-helper/build.sh dependency:tree

# Show which artifacts are missing/downloading
./scripts/build-helper/build.sh --verbose clean compile 2>&1 | grep "proxy"
```

## Contributing

Found an issue or have a suggestion? Please:
1. Document the problem with proxy details (sanitized)
2. Include Maven/Java/Python versions
3. Share proxy server logs (with `--verbose`)

## Related Documentation

- [Maven Proxy Configuration](https://maven.apache.org/guides/mini/guide-proxies.html)
- [Maven Settings Reference](https://maven.apache.org/ref/3.9.0/maven-settings/settings.html)
- [Apache HttpClient Proxy Authentication](https://hc.apache.org/httpcomponents-client-5.1.x/current/httpclient5/apidocs/org/apache/hc/client5/http/auth/AuthScope.html)

## License

This script is part of the netflow-java project and uses the same license.
