#!/bin/bash
# Maven Proxy Build Wrapper
# Convenience script to run maven-proxy-build.py with proper working directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "$PROJECT_ROOT"

# Run the Python proxy build script with all arguments
python3 "${SCRIPT_DIR}/maven-proxy-build.py" "$@"
