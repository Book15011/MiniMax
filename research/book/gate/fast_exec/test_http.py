import json,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
import pytest
from research.book.gate.fast_exec.native_http import NativeHTTP
def test_native_transport_forbids_orders_secrets_and_other_hosts():
    h=NativeHTTP()
    try:
        for u in ['https://mock-api.roostoo.com/v3/place_order','https://mock-api.roostoo.com/v3/balance','https://evil.test/v3/serverTime','file:///etc/passwd','https://x@mock-api.roostoo.com/v3/serverTime']:
            with pytest.raises(ValueError):h.get(u)
    finally:h.close()
def test_native_transport_reuses_connection_and_exposes_actual_protocol():
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def do_GET(self):
            b=b'{"Success":true,"Data":{}}'
            self.send_response(200);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    h=NativeHTTP(loopback_port=server.server_port)
    try:
        u=f'http://127.0.0.1:{server.server_port}/fixture'
        a=h.get(u);b=h.get(u)
        assert a['curl_code']==b['curl_code']==0
        assert a['http_status']==b['http_status']==200
        assert a['new_connections']==1 and b['new_connections']==0
        assert b['http_version']==2 # libcurl enum2 means HTTP1.1
        assert b['body']['Success'] is True
    finally:h.close();server.shutdown();server.server_close()
