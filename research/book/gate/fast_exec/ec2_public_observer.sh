#!/usr/bin/env bash
# Public observation only. No bot service commands, credentials or orders.
set -euo pipefail
task_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$task_dir"
task_python="${MM_FAST_PYTHON:-python3}"
export MM_FAST_RESULTS="${MM_FAST_RESULTS:-$task_dir/results/$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$MM_FAST_RESULTS"
nice -n 10 "$task_python" -B -m fast_exec.observe_ec2 --out "$MM_FAST_RESULTS/observer" --seconds 600
