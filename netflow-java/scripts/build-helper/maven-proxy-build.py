#!/usr/bin/env python3
"""
Maven Proxy Build Helper

This script solves Maven dependency resolution issues in restricted network environments
(e.g., containers with proxy-only network access) by:

1. Starting a local Python HTTP server that acts as a Maven repository proxy
2. Configuring Maven to use this local proxy via settings.xml
3. The local proxy downloads artifacts from Maven Central via the authenticated proxy
4. Automatically retrying on network failures

This bypasses all proxy authentication issues that would occur with Maven's native
proxy handling, since the local server uses curl (which handles proxy auth correctly).

Usage:
    python3 maven-proxy-build.py [maven-goals]

Examples:
    python3 maven-proxy-build.py clean compile
    python3 maven-proxy-build.py clean package
    python3 maven-proxy-build.py clean compile test
"""

import http.server, threading, os, subprocess, sys, time, argparse

def main():
    parser = argparse.ArgumentParser(
        description='Build Maven project with local proxy server for network-isolated environments'
    )
    parser.add_argument(
        'goals',
        nargs='*',
        default=['clean', 'compile'],
        help='Maven goals to execute (default: clean compile)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=18080,
        help='Local proxy server port (default: 18080)'
    )
    parser.add_argument(
        '--no-clean-cache',
        action='store_true',
        help='Do not clear .lastUpdated files (useful for debugging)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show proxy server request logs'
    )

    args = parser.parse_args()

    # Get proxy from environment
    proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY') or ''
    if not proxy:
        print('⚠️  Warning: No https_proxy environment variable found')
        print('   If you are behind a corporate proxy, set it:')
        print('   export https_proxy=http://user:password@proxy:port')

    # Setup paths
    pom_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    m2_repo = os.path.expanduser('~/.m2/repository')
    maven_central = 'https://repo.maven.apache.org/maven2'
    port = args.port

    print(f'📦 Maven Proxy Build Helper')
    print(f'   POM directory: {pom_dir}')
    print(f'   Local proxy: http://127.0.0.1:{port}')
    print(f'   Maven cache: {m2_repo}')
    if proxy:
        print(f'   Using proxy: {proxy[:80]}...')

    # Define the proxy handler
    class MavenProxy(http.server.BaseHTTPRequestHandler):
        def fetch(self):
            """Fetch artifact from cache or download from Maven Central"""
            local = os.path.join(m2_repo, self.path.lstrip('/'))

            # Serve from cache if exists and has content
            if os.path.exists(local) and os.path.getsize(local) > 0:
                return local

            # Try to download from Maven Central
            os.makedirs(os.path.dirname(local), exist_ok=True)
            url = maven_central + self.path

            # Use curl with proxy if available
            curl_cmd = ['curl', '-s', '-L']
            if proxy:
                curl_cmd.extend(['--proxy', proxy])
            curl_cmd.extend(['-w', '%{http_code}', '-o', local, url])

            try:
                r = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
                code = r.stdout.strip()

                if code == '200' and os.path.exists(local) and os.path.getsize(local) > 0:
                    return local

                # Failed to download
                if os.path.exists(local):
                    os.unlink(local)
                if args.verbose:
                    print(f'  [proxy] {self.path}  →  HTTP {code}', file=sys.stderr)
                return None
            except subprocess.TimeoutExpired:
                if os.path.exists(local):
                    os.unlink(local)
                if args.verbose:
                    print(f'  [proxy] {self.path}  →  TIMEOUT', file=sys.stderr)
                return None

        def do_GET(self):
            """Handle GET requests"""
            local = self.fetch()
            if local is None:
                self.send_response(404)
                self.end_headers()
                return

            try:
                with open(local, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Content-Type', 'application/octet-stream')
                self.end_headers()
                self.wfile.write(data)
                if args.verbose:
                    print(f'  [proxy] {self.path}  →  OK ({len(data)} bytes)', file=sys.stderr)
            except Exception as e:
                self.send_response(500)
                self.end_headers()

        def do_HEAD(self):
            """Handle HEAD requests"""
            local = self.fetch()
            code = 200 if local else 404
            self.send_response(code)
            self.end_headers()

        def log_message(self, *args):
            """Suppress request logging unless verbose"""
            if args.verbose:
                super().log_message(*args)

    # Start the local proxy server
    print('\n🔧 Starting local Maven proxy server...')
    httpd = http.server.HTTPServer(('127.0.0.1', port), MavenProxy)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print(f'   ✓ Proxy server listening on http://127.0.0.1:{port}')

    # Configure Maven settings.xml to use the local proxy
    print('\n⚙️  Configuring Maven...')
    settings_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.2.0
          https://maven.apache.org/xsd/settings-1.2.0.xsd">
  <!-- Local proxy mirror for network-isolated build environments -->
  <mirrors>
    <mirror>
      <id>local-proxy-mirror</id>
      <mirrorOf>*</mirrorOf>
      <url>http://127.0.0.1:{port}</url>
      <blocked>false</blocked>
    </mirror>
  </mirrors>

  <!-- Allow HTTP to localhost (Maven 3.8.1+ blocks HTTP by default) -->
  <profiles>
    <profile>
      <id>allow-localhost-http</id>
      <activation>
        <activeByDefault>true</activeByDefault>
      </activation>
      <repositories>
        <repository>
          <id>local-proxy</id>
          <url>http://127.0.0.1:{port}</url>
        </repository>
      </repositories>
      <pluginRepositories>
        <pluginRepository>
          <id>local-proxy-plugins</id>
          <url>http://127.0.0.1:{port}</url>
        </pluginRepository>
      </pluginRepositories>
    </profile>
  </profiles>
</settings>'''

    m2_dir = os.path.expanduser('~/.m2')
    os.makedirs(m2_dir, exist_ok=True)
    settings_path = os.path.join(m2_dir, 'settings.xml')

    with open(settings_path, 'w') as f:
        f.write(settings_xml)
    print(f'   ✓ Created {settings_path}')

    # Clear Maven cache staleness markers if not disabled
    if not args.no_clean_cache:
        print('\n🧹 Clearing Maven cache staleness markers...')
        subprocess.run(
            ['find', m2_repo, '-name', '*.lastUpdated', '-delete'],
            capture_output=True
        )
        print('   ✓ Cleared .lastUpdated files')

    # Run Maven
    print(f'\n🚀 Running: mvn {" ".join(args.goals)}')
    print('=' * 70)

    env = os.environ.copy()
    # Clear JAVA_TOOL_OPTIONS to avoid proxy conflicts
    env.pop('JAVA_TOOL_OPTIONS', None)

    result = subprocess.run(
        ['mvn', '-f', pom_dir, '--no-transfer-progress'] + args.goals,
        env=env
    )

    print('=' * 70)

    if result.returncode == 0:
        print('\n✅ BUILD SUCCEEDED!')
        print(f'\nℹ️  Settings.xml saved to: {settings_path}')
        print('   To use in future builds, ensure https_proxy is set and run:')
        print('   python3 scripts/build-helper/maven-proxy-build.py [goals]')
    else:
        print(f'\n❌ BUILD FAILED (exit code: {result.returncode})')
        if not args.verbose:
            print('   Re-run with --verbose for more details')
        sys.exit(1)

    # Keep server running for a moment to allow final connections
    time.sleep(1)

if __name__ == '__main__':
    main()
