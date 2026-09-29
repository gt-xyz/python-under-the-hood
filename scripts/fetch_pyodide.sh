#!/usr/bin/env bash
# Download the Pyodide runtime into site/py/.
#   scripts/fetch_pyodide.sh            # default version
#   scripts/fetch_pyodide.sh 314.0.7    # a specific version
# After upgrading, re-run scripts/record_outputs.py with the matching CPython version
# (Pyodide 314.x = CPython 3.14), then scripts/build.py.
set -euo pipefail
VERSION="${1:-314.0.7}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$TMP"
npm pack "pyodide@${VERSION}" --silent
tar xzf "pyodide-${VERSION}.tgz"
mkdir -p "$ROOT/site/py"
cp package/pyodide.js package/pyodide.mjs package/pyodide.asm.mjs package/pyodide.asm.wasm \
   package/pyodide-lock.json "$ROOT/site/py/"
# The standard library ships as a .zip. It is stored as base64 text because some hosts
# (including the claude.ai artifact viewer) refuse to serve .zip files; the page decodes it.
base64 -w0 package/python_stdlib.zip > "$ROOT/site/py/python_stdlib.b64.txt" 2>/dev/null \
  || base64 -i package/python_stdlib.zip | tr -d '\n' > "$ROOT/site/py/python_stdlib.b64.txt"
python3 - "$ROOT/site/py/pyodide-lock.json" <<'EOF'
import json, sys
print("Installed Pyodide for Python", json.load(open(sys.argv[1]))["info"]["python"])
EOF
