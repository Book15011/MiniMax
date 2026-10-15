#pragma once
// Opaque declarations for installed public C ABIs, not private layouts.
// See ABI_SOURCES.md. HTTP/TLS, JSON and crypto are provided by maintained libraries.
#include <cstdint>
#include <cstddef>
#include <string>
#include <memory>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <cctype>
#include <chrono>
extern "C" {
void* curl_easy_init();
void curl_easy_cleanup(void*);
int curl_global_init(long);
void curl_global_cleanup();
int curl_easy_setopt(void*,int,...);
int curl_easy_getinfo(void*,int,...);
int curl_easy_perform(void*);
int curl_easy_send(void*,const void*,size_t,size_t*);
int curl_easy_recv(void*,void*,size_t,size_t*);
const char* curl_version();
struct json_object;struct json_tokener;
json_object* json_object_new_object();
json_object* json_object_new_array();
json_object* json_object_new_string(const char*);
json_object* json_object_new_int64(int64_t);
json_object* json_object_new_boolean(int);
int json_object_object_add(json_object*,const char*,json_object*);
int json_object_array_add(json_object*,json_object*);
int json_object_object_get_ex(const json_object*,const char*,json_object**);
int json_object_get_type(const json_object*);
int64_t json_object_get_int64(const json_object*);
int json_object_get_boolean(const json_object*);
const char* json_object_get_string(json_object*);
const char* json_object_to_json_string_ext(json_object*,int);
size_t json_object_array_length(const json_object*);
json_object* json_object_array_get_idx(const json_object*,size_t);
int json_object_put(json_object*);
json_tokener* json_tokener_new_ex(int);
void json_tokener_free(json_tokener*);
void json_tokener_set_flags(json_tokener*,int);
json_object* json_tokener_parse_ex(json_tokener*,const char*,int);
int json_tokener_get_error(json_tokener*);
size_t json_tokener_get_parse_end(json_tokener*);
struct evp_md_st;
const evp_md_st* EVP_sha256();
unsigned char* HMAC(const evp_md_st*,const void*,int,const unsigned char*,size_t,unsigned char*,unsigned int*);
unsigned char* SHA1(const unsigned char*,size_t,unsigned char*);
int EVP_EncodeBlock(unsigned char*,const unsigned char*,int);
int RAND_bytes(unsigned char*,int);
}
namespace fast {
using I=int64_t;
using J=std::unique_ptr<json_object,decltype(&json_object_put)>;
inline J own(json_object* p){if(!p)throw std::runtime_error("json allocation");return J(p,json_object_put);}
inline J object(){return own(json_object_new_object());}
inline void add(json_object* o,const char* k,const std::string& v){json_object_object_add(o,k,json_object_new_string(v.c_str()));}
inline void add(json_object* o,const char* k,I v){json_object_object_add(o,k,json_object_new_int64(v));}
inline void add(json_object* o,const char* k,bool v){json_object_object_add(o,k,json_object_new_boolean(v));}
inline json_object* field(json_object* p,const char* k){json_object* r=nullptr;if(!p||json_object_get_type(p)!=4||!json_object_object_get_ex(p,k,&r)||!r)throw std::invalid_argument("missing field");return r;}
inline std::string str(json_object* p){if(!p||json_object_get_type(p)!=6)throw std::invalid_argument("string required");const char* s=json_object_get_string(p);return s?s:"";}
inline std::string s(json_object* p,const char* k){return str(field(p,k));}
inline I n(json_object* p,const char* k){auto r=field(p,k);if(json_object_get_type(r)!=3)throw std::invalid_argument("integer required");return json_object_get_int64(r);}
inline bool b(json_object* p,const char* k){auto r=field(p,k);if(json_object_get_type(r)!=1)throw std::invalid_argument("boolean required");return json_object_get_boolean(r);}
inline std::string dump(json_object* p){return json_object_to_json_string_ext(p,0);}
inline J parse_json(const std::string& x){
 if(x.empty()||x.size()>1000000)throw std::invalid_argument("json length");
 auto* t=json_tokener_new_ex(32);if(!t)throw std::runtime_error("json tokener");
 json_tokener_set_flags(t,1|16); // STRICT | VALIDATE_UTF8, json-c 0.15 public flags.
 auto* o=json_tokener_parse_ex(t,x.c_str(),static_cast<int>(x.size()));
 int err=json_tokener_get_error(t);size_t end=json_tokener_get_parse_end(t);json_tokener_free(t);
 bool trailing=false;for(size_t i=end;i<x.size();++i)if(!std::isspace(static_cast<unsigned char>(x[i])))trailing=true;
 if(err||trailing||!o){if(o)json_object_put(o);throw std::invalid_argument("invalid JSON");}
 return own(o);
}
inline J load(const std::string& f){std::ifstream in(f);if(!in)throw std::runtime_error("configuration unavailable");std::ostringstream ss;ss<<in.rdbuf();return parse_json(ss.str());}
inline I mono(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
inline I unixms(){return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();}
inline std::string base64(const unsigned char* p,int n){std::string r(4*((n+2)/3)+1,'\0');int z=EVP_EncodeBlock(reinterpret_cast<unsigned char*>(&r[0]),p,n);if(z<0)throw std::runtime_error("base64");r.resize(z);return r;}
inline std::string hmac_fixture(const std::string& body){unsigned char out[32];unsigned int z=0;if(!HMAC(EVP_sha256(),"Jefe",4,reinterpret_cast<const unsigned char*>(body.data()),body.size(),out,&z)||z!=32)throw std::runtime_error("hmac");std::string r;for(unsigned char c:out){r+="0123456789abcdef"[c>>4];r+="0123456789abcdef"[c&15];}return r;}
}
