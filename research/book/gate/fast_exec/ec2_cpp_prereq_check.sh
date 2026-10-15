#!/usr/bin/env bash
# Read-only C++ prerequisite check; no installation, trading or service changes.
set -u
command -v g++ >/dev/null || { echo "MISSING: g++"; exit 2; }
g++ --version | head -n 1
status=0
for header in curl/curl.h openssl/evp.h boost/beast.hpp nlohmann/json.hpp; do
  if printf "#include <%s>\nint main(){}\n" "$header" | g++ -std=c++17 -x c++ -fsyntax-only - >/dev/null 2>&1; then
    printf "OK: %s\n" "$header"
  else
    printf "MISSING: %s\n" "$header"; status=2
  fi
done
exit "$status"
