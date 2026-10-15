# Installed ABI sources

This standalone C++17 process uses installed libcurl4, json-c5 and OpenSSL3. It does not implement TLS, HMAC, SHA or JSON parsing. abi.hpp contains only the subset of documented public declarations needed here, with opaque pointers; no private structs or library sources are copied. The link uses versioned runtime sonames because development packages could not be downloaded on this host. Deployment portability is limited to those ABI majors; the binary must be rebuilt/tested on EC2 rather than assumed portable.

References checked for this implementation:
- libcurl stable ABI policy: https://curl.se/libcurl/abi.html
- curl 7.81 public header/constants: https://github.com/curl/curl/blob/curl-7_81_0/include/curl/curl.h
- connect-only TLS/proxy setup: https://curl.se/libcurl/c/CURLOPT_CONNECT_ONLY.html
- nonblocking send/receive, including draining TLS internal buffers before polling: https://curl.se/libcurl/c/curl_easy_recv.html and https://curl.se/libcurl/c/curl_easy_send.html
- json-c0.15 object functions/types: https://json-c.github.io/json-c/json-c-0.15/doc/html/json__object_8h.html
- strict/UTF8 tokener and trailing parse position: https://json-c.github.io/json-c/json-c-0.15/doc/html/json__tokener_8h.html
- OpenSSL3 HMAC: https://docs.openssl.org/3.0/man3/HMAC/
- WebSocket framing/handshake: https://www.rfc-editor.org/rfc/rfc6455.html
- Binance combined bookTicker stream: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams

Installed packages at initial build: libcurl4 7.81.0-1ubuntu1.29; libjson-c5 0.15-3~ubuntu1.22.04.2; libssl3 3.0.2-0ubuntu1.30.
The existing curl lacks built-in WebSocket support (added7.86); a deliberately narrow RFC6455 framing adapter uses libcurl's verified TLS connection. It supports text fragments and ping/pong, rejects compressed/binary/masked-server/oversized/nonminimal frames and malformed handshakes. It is not claimed to be a general WebSocket implementation. Loopback tests cover actual TLS-free transport/framing and negative cases; remote TLS/public tests are separate.

No dynamic headers or keys are logged. NETRC is disabled, TLS host/peer verification required, redirects disabled and public URLs allowlisted. Mock network tests allow only http://127.0.0.1:PORT/fixture. No signed competition endpoint or credential loader exists in this process. Dummy HMAC tests always use the public fixture string Jefe.
