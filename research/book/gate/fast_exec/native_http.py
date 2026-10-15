"""Installed native libcurl via its stable C ABI; public GET allowlist only.
ABI values checked against curl7.81.0/include/curl/curl.h. No signed/order method.
"""
import ctypes as C,ctypes.util,json,time,re
from urllib.parse import urlsplit,parse_qsl
from .driver import CFG
L=C.CDLL(ctypes.util.find_library('curl'))
L.curl_global_init.argtypes=[C.c_long];L.curl_global_init.restype=C.c_int
if L.curl_global_init(3):raise RuntimeError('libcurl initialization failed')
L.curl_easy_init.restype=C.c_void_p
L.curl_easy_cleanup.argtypes=[C.c_void_p]
L.curl_easy_setopt.argtypes=[C.c_void_p,C.c_int];L.curl_easy_setopt.restype=C.c_int
L.curl_easy_getinfo.argtypes=[C.c_void_p,C.c_int];L.curl_easy_getinfo.restype=C.c_int
L.curl_easy_perform.argtypes=[C.c_void_p];L.curl_easy_perform.restype=C.c_int
L.curl_version.restype=C.c_char_p
CALLBACK=C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t,C.c_size_t,C.c_void_p)
class NativeHTTP:
    def __init__(self,http2=False,cold=False,loopback_port=None):
        self.h=L.curl_easy_init()
        if not self.h:raise MemoryError()
        self.loopback_port=loopback_port;self.chunks=[];self.size=0;self.callback_error=False
        def write(ptr,size,n,_):
            count=size*n
            try:
                if self.size+count>1_000_000:return 0
                self.chunks.append(C.string_at(ptr,count));self.size+=count;return count
            except Exception:self.callback_error=True;return 0
        self.callback=CALLBACK(write)
        self.set(20011,self.callback)
        for key,value in [(84,4 if http2 else 2),(121,1),(213,1),(155,CFG['request_timeout_ms']),(156,CFG['connect_timeout_ms']),
                (64,1),(81,2),(52,0),(99,1),(80,1),(74,int(cold)),(75,int(cold)),(181,3 if loopback_port else 2)]:
            self.set(key,C.c_long(value))
        if loopback_port:self.set(10177,C.c_char_p(b'127.0.0.1'))
    def set(self,opt,value):
        if L.curl_easy_setopt(self.h,opt,value):raise RuntimeError('Unsupported libcurl option')
    def validate(self,url):
        p=urlsplit(url)
        if self.loopback_port and p.scheme=='http' and p.hostname=='127.0.0.1' and p.port==self.loopback_port and p.path=='/fixture' and not p.query:return
        if p.scheme!='https' or p.hostname!='mock-api.roostoo.com' or p.port not in [None,443] or p.username or p.password or p.fragment:
            raise ValueError('Public target not allowed')
        if p.path in ['/v3/serverTime','/v3/exchangeInfo'] and not p.query:return
        if p.path=='/v3/ticker':
            q=parse_qsl(p.query,keep_blank_values=True)
            if len(q)==1 and q[0][0]=='timestamp' and re.fullmatch(r'\d{13}',q[0][1]):return
        raise ValueError('Only public server time and timestamped ticker are allowed')
    def info(self,opt,typ):
        x=typ()
        if L.curl_easy_getinfo(self.h,opt,C.byref(x)):return None
        return x.value
    def get(self,url):
        self.validate(url);self.chunks=[];self.size=0;self.callback_error=False
        data=url.encode();self.set(10002,C.c_char_p(data))
        start=time.monotonic_ns();wall=time.time_ns();code=L.curl_easy_perform(self.h);end=time.monotonic_ns()
        row={'curl_code':code,'http_status':self.info(0x200002,C.c_long),'http_version':self.info(0x20002e,C.c_long),
             'new_connections':self.info(0x20001a,C.c_long),'start_mono_ns':start,'end_mono_ns':end,'send_unix_ns':wall,
             'receive_unix_ns':time.time_ns(),'elapsed_ms':(end-start)/1e6,'callback_error':self.callback_error}
        for name,n in [('dns',4),('connect',5),('tls',33),('ttfb',17),('total',3)]:
            value=self.info(0x300000+n,C.c_double);row[name+'_ms']=value*1000 if value is not None else None
        try:row['body']=json.loads(b''.join(self.chunks))
        except (ValueError,UnicodeDecodeError):row['body']=None
        row['success']=code==0 and row['http_status']==200 and isinstance(row['body'],dict) and row['body'].get('Success',True) is not False
        return row
    def close(self):
        if self.h:L.curl_easy_cleanup(self.h);self.h=None
