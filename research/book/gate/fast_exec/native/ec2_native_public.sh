#!/usr/bin/env bash
# Public-only native EC2 test. No credentials, bot imports, signed requests or service changes.
set -euo pipefail
task_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${MM_NATIVE_RESULTS:?Set MM_NATIVE_RESULTS to a new absolute output directory}"
case "$MM_NATIVE_RESULTS" in /*) ;; *) echo 'Use an absolute output directory' >&2; exit 2;; esac
if [ -e "$MM_NATIVE_RESULTS" ]; then echo 'Output already exists; preserve previous evidence' >&2; exit 2; fi
task_mode=${1:-cpu}
case "$task_mode" in cpu|shadow) ;; *) echo 'Only cpu or public shadow mode is allowed' >&2; exit 2;; esac
mkdir -p -- "$MM_NATIVE_RESULTS/build"
g++ -std=c++17 -O3 -Wall -Wextra -Werror -Wno-misleading-indentation -pthread "$task_dir/native/service.cpp" -Wl,-z,relro,-z,now -l:libcurl.so.4 -l:libjson-c.so.5 -l:libcrypto.so.3 -o "$MM_NATIVE_RESULTS/build/fast_exec_native"
sha256sum "$MM_NATIVE_RESULTS/build/fast_exec_native" > "$MM_NATIVE_RESULTS/binary.sha256"
if [ "$task_mode" = cpu ]; then
  exec nice -n 10 "$MM_NATIVE_RESULTS/build/fast_exec_native" cpu "$task_dir/config.json" "$MM_NATIVE_RESULTS/cpu" 50000
fi
exec nice -n 10 "$MM_NATIVE_RESULTS/build/fast_exec_native" shadow "$task_dir/config.json" "$MM_NATIVE_RESULTS/public_shadow" 600
