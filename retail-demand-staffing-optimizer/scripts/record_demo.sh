#!/usr/bin/env bash
# Terminal demo recording using asciinema (install: brew install asciinema)
set -euo pipefail
asciinema rec -c "./scripts/demo.sh" docs/demo.cast
echo "Recorded to docs/demo.cast"
