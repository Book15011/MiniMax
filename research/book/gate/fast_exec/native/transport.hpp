#pragma once
#include "abi.hpp"
#include <algorithm>
#include <poll.h>
#include <cstring>
#include <map>
#include <functional>
namespace fast {
class Http {
 void* h=nullptr;std::string body;bool overflow=false;
 static size_t write(char* p,size_t z,size_t n,void* ctx){
  auto* self=static_cast<Http*>(ctx);if(z&&n>1000000/z)return 0;size_t total=z*n;
  if(total>1000000-self->body.size()){self->overflow=true;return 0;}
  try{self->body.append(p,total);return total;}catch(...){return 0;}
 }
 public:
 explicit Http(bool fixture=false){
  h=curl_easy_init();if(!h)throw std::bad_alloc();
  try{
   set(84,2L);set(64,1L);set(81,2L);set(52,0L);set(99,1L);set(51,0L);
   set(121,1L);set(213,1L);set(155,4000L);set(156,2000L);set(181,fixture?3L:2L);
   set(20011,&Http::write);set(10001,this);
   if(fixture)set(10177,"127.0.0.1");
  }catch(...){curl_easy_cleanup(h);h=nullptr;throw;}
 }
 ~Http(){if(h)curl_easy_cleanup(h);}
 Http(const Http&)=delete;Http& operator=(const Http&)=delete;
 template<class T>void set(int k,T v){if(curl_easy_setopt(h,k,v))throw std::runtime_error("curl option");}
 template<class T>T info(int k){T x{};if(curl_easy_getinfo(h,k,&x))throw std::runtime_error("curl info");return x;}
 static bool loopback(const std::string& url){
  const std::string prefix="http://127.0.0.1:";if(url.rfind(prefix,0))return false;
  auto slash=url.find('/',prefix.size());if(slash==std::string::npos||url.substr(slash)!="/fixture")return false;
  auto port=url.substr(prefix.size(),slash-prefix.size());if(port.empty()||port.size()>5)return false;int n=0;
  for(char c:port){if(c<'0'||c>'9')return false;n=n*10+c-'0';}return n>0&&n<=65535;
 }
 struct Reply {int code=0;long status=0;I begin=0,end=0,wall=0;std::string data;};
 Reply get(const std::string& url,bool fixture=false){
  if(fixture?!loopback(url):!(url=="https://mock-api.roostoo.com/v3/serverTime"||
    url=="https://mock-api.roostoo.com/v3/exchangeInfo"||
    (url.rfind("https://mock-api.roostoo.com/v3/ticker?timestamp=",0)==0&&url.size()==62)))
   throw std::invalid_argument("public GET allowlist");
  // Validate every ticker timestamp digit separately.
  if(!fixture&&url.find("?")!=std::string::npos)for(char c:url.substr(url.find('=')+1))if(c<'0'||c>'9')throw std::invalid_argument("timestamp");
  body.clear();overflow=false;set(10002,url.c_str());Reply r;r.begin=mono();r.wall=unixms();
  r.code=curl_easy_perform(h);r.end=mono();r.status=info<long>(0x200002);r.data=body;
  if(overflow)r.code=23;return r;
 }
 void connect(const std::string& url){set(10002,url.c_str());set(141,1L);int c=curl_easy_perform(h);if(c)throw std::runtime_error("feed_connect_"+std::to_string(c));}
 bool wait(short events,I deadline){
  I left=(deadline-mono())/1000000;if(left<=0)return false;
  int fd=info<int>(0x50002c);pollfd p{fd,events,0};
  int r=poll(&p,1,static_cast<int>(std::min<I>(left,100)));
  if(r<0)throw std::runtime_error("feed poll");return r>0;
 }
 void send(const std::string& data,I deadline){
  size_t at=0;while(at<data.size()){
   if(mono()>=deadline)throw std::runtime_error("feed send timeout");
   size_t wrote=0;int c=curl_easy_send(h,data.data()+at,data.size()-at,&wrote);
   if(c==81){wait(POLLOUT,deadline);continue;}if(c||!wrote)throw std::runtime_error("feed send");at+=wrote;
  }
 }
 std::string receive(I deadline){
  for(;;){if(mono()>=deadline)return {};
   char data[65536];size_t got=0;int c=curl_easy_recv(h,data,sizeof(data),&got);
   if(c==81){if(!wait(POLLIN,deadline))return {};continue;}
   if(c||!got)throw std::runtime_error("feed disconnected");return std::string(data,got);
  }
 }
};
inline std::string lowercase(std::string v){for(char& c:v)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));return v;}
inline std::string trim(std::string v){auto a=v.find_first_not_of(" \t\r\n"),b=v.find_last_not_of(" \t\r\n");return a==std::string::npos?"":v.substr(a,b-a+1);}
inline bool token(const std::string& v,const std::string& wanted){
 std::istringstream in(lowercase(v));std::string p;while(std::getline(in,p,','))if(trim(p)==wanted)return true;return false;
}
inline std::string accept_key(const std::string& key){
 auto x=key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11";unsigned char out[20];
 if(!SHA1(reinterpret_cast<const unsigned char*>(x.data()),x.size(),out))throw std::runtime_error("sha1");return base64(out,20);
}
inline void handshake(const std::string& headers,const std::string& key){
 std::istringstream in(headers);std::string line;std::getline(in,line);
 if(line.rfind("HTTP/1.1 101 ",0))throw std::runtime_error("websocket status");
 std::map<std::string,std::string> fields;
 while(std::getline(in,line)){
  if(trim(line).empty())break;size_t pos=line.find(':');if(pos==std::string::npos)throw std::runtime_error("websocket header");
  auto name=lowercase(trim(line.substr(0,pos))),value=trim(line.substr(pos+1));
  if(fields.count(name))throw std::runtime_error("duplicate websocket header");fields[name]=value;
 }
 if(lowercase(fields["upgrade"])!="websocket"||!token(fields["connection"],"upgrade")||
 fields["sec-websocket-accept"]!=accept_key(key)||!fields["sec-websocket-extensions"].empty())throw std::runtime_error("websocket validation");
}
class Frames {
 std::string input,fragment;bool fragmented=false;
 public:
 std::function<void(const std::string&)> text,ping;
 void feed(const std::string& bytes){
  if(bytes.size()>1100000-input.size())throw std::runtime_error("websocket buffer limit");input+=bytes;
  size_t at=0;
  while(input.size()-at>=2){
   unsigned char a=input[at],b=input[at+1];bool fin=a&128;int op=a&15;uint64_t len=b&127;size_t header=2;
   if((a&112)||(b&128))throw std::runtime_error("websocket flags");
   if(len==126){if(input.size()-at<4)break;len=(static_cast<unsigned char>(input[at+2])<<8)|static_cast<unsigned char>(input[at+3]);header=4;if(len<126)throw std::runtime_error("nonminimal frame");}
   else if(len==127){
    if(input.size()-at<10)break;if(static_cast<unsigned char>(input[at+2])&128)throw std::runtime_error("frame sign bit");len=0;
    for(size_t i=2;i<10;++i)len=(len<<8)|static_cast<unsigned char>(input[at+i]);header=10;if(len<65536)throw std::runtime_error("nonminimal frame");
   }
   if(len>1000000||(op>=8&&(!fin||len>125)))throw std::runtime_error("websocket length");
   if(input.size()-at<header+len)break;
   std::string payload=input.substr(at+header,static_cast<size_t>(len));at+=header+len;
   if(op==8){if(len==1)throw std::runtime_error("close length");throw std::runtime_error("feed closed");}
   if(op==9){if(ping)ping(payload);continue;}if(op==10)continue;
   if(op==1){if(fragmented)throw std::runtime_error("overlapping fragment");fragment=payload;fragmented=true;}
   else if(op==0){if(!fragmented)throw std::runtime_error("unexpected continuation");fragment+=payload;}
   else throw std::runtime_error("unsupported opcode");
   if(fragment.size()>1000000)throw std::runtime_error("fragment limit");
   if(fin){if(text)text(fragment);fragment.clear();fragmented=false;}
  }
  input.erase(0,at);
 }
};
inline std::string control(int op,const std::string& data){
 if(data.size()>125)throw std::invalid_argument("control length");
 unsigned char mask[4];if(RAND_bytes(mask,4)!=1)throw std::runtime_error("random mask");
 std::string out;out+=static_cast<char>(128|op);out+=static_cast<char>(128|data.size());
 out.append(reinterpret_cast<char*>(mask),4);
 for(size_t i=0;i<data.size();++i)out+=static_cast<char>(static_cast<unsigned char>(data[i])^mask[i%4]);return out;
}
inline void websocket(const std::string& url,const std::string& host,const std::string& path,I deadline,
 const std::function<void(const std::string&)>& receive,bool fixture=false){
 Http socket(fixture);socket.connect(url);unsigned char random[16];
 if(RAND_bytes(random,16)!=1)throw std::runtime_error("random key");std::string key=base64(random,16);
 socket.send("GET "+path+" HTTP/1.1\r\nHost: "+host+"\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: "+key+"\r\nSec-WebSocket-Version: 13\r\n\r\n",std::min<I>(deadline,mono()+3000000000LL));
 std::string input;I handshake_deadline=std::min<I>(deadline,mono()+3000000000LL);
 size_t end=std::string::npos;
 while((end=input.find("\r\n\r\n"))==std::string::npos){
  if(mono()>=handshake_deadline)throw std::runtime_error("websocket handshake timeout");
  input+=socket.receive(handshake_deadline);if(input.size()>65536)throw std::runtime_error("websocket header limit");
 }
 handshake(input.substr(0,end+4),key);Frames frames;frames.text=receive;
 frames.ping=[&](const std::string& p){socket.send(control(10,p),std::min<I>(deadline,mono()+1000000000LL));};
 frames.feed(input.substr(end+4));
 while(mono()<deadline){auto next=socket.receive(std::min<I>(deadline,mono()+100000000LL));if(!next.empty())frames.feed(next);}
}
}
