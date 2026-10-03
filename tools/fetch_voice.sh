#!/usr/bin/env bash
# Download the Piper "lessac" (en-US, medium) voice into models/.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f models/en-us-lessac-medium.onnx ] && exit 0
mkdir -p models
curl -fsSL https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-lessac-medium.tar.gz | tar xz -C models
