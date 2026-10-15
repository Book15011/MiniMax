// Exact native money/risk core. No networking, credential access or order sending.
#include <cstdint>
#include <cstring>
#include <limits>
#include <deque>
#include <algorithm>
#include <stdexcept>
using i64=std::int64_t;using i128=__int128_t;
constexpr i64 SCALE=100000000, PPM=1000000;
static i64 parse(const char* s) {
    if(!s||!*s||std::strlen(s)>128)throw std::invalid_argument("decimal");
    i128 whole=0,frac=0;int digits=0;bool dot=false,any=false,after=false;
    for(const char* p=s;*p;++p){
        if(*p=='.'&&!dot&&any){dot=true;continue;}
        if(*p<'0'||*p>'9')throw std::invalid_argument("decimal");
        any=true;
        if(dot){after=true;if(++digits>8)throw std::invalid_argument("precision");frac=frac*10+(*p-'0');}
        else {whole=whole*10+(*p-'0');if(whole>std::numeric_limits<i64>::max()/SCALE)throw std::overflow_error("money");}
    }
    if(dot&&!after)throw std::invalid_argument("decimal");
    while(digits++<8)frac*=10;
    i128 n=whole*SCALE+frac;
    if(n>std::numeric_limits<i64>::max())throw std::overflow_error("money");
    return static_cast<i64>(n);
}
static i64 checked(i128 n){if(n<0||n>std::numeric_limits<i64>::max())throw std::overflow_error("arithmetic");return static_cast<i64>(n);}
static i64 ceildiv(i128 a,i128 b){return checked((a+b-1)/b);}
struct Sized {i64 quantity,notional,fee;int status;};
extern "C" int money_parse(const char* s,i64* out){try{*out=parse(s);return 0;}catch(...){return -1;}}
extern "C" int size_order(const char* price,const char* budget,int precision,i64 fee,Sized* out){
    *out={0,0,0,-1};
    try{
        const i64 px=parse(price),b=parse(budget);
        if(px<=0||precision<0||precision>8||fee<0||fee>PPM)throw std::invalid_argument("sizing");
        i64 step=1;for(int i=precision;i<8;++i)step*=10;
        i64 q=checked(static_cast<i128>(b)*SCALE*PPM/(static_cast<i128>(px)*(PPM+fee)));
        q=q/step*step;
        i64 n=ceildiv(static_cast<i128>(q)*px,SCALE),f=ceildiv(static_cast<i128>(n)*fee,PPM);
        while(q>0&&static_cast<i128>(n)+f>b){q-=step;n=ceildiv(static_cast<i128>(q)*px,SCALE);f=ceildiv(static_cast<i128>(n)*fee,PPM);}
        *out={q,n,f,0};return 0;
    }catch(...){return -1;}
}
extern "C" int gate_order(i64 now,i64 feed,i64 quote,i64 rtt,i64 uncertainty,i64 feed_limit,i64 quote_limit,i64 rtt_limit,i64 clock_limit,
 const char* equity,const char* cash,const char* gross,const char* budget,const char* price,int precision,i64 fee,Sized* out){
    try{
        if(feed>now||quote>now||now-feed>feed_limit||now-quote>quote_limit||rtt<0||rtt>rtt_limit||uncertainty<0||uncertainty>clock_limit)return 1;
        i64 e=parse(equity),c=parse(cash),g=parse(gross),b=parse(budget);
        if(e<=0||g>e)return 2;
        b=std::min({b,c,e-g});
        char buf[64]; // Convert exact native scaled budget without floating point.
        i64 w=b/SCALE,f=b%SCALE;
        auto integer=[](i64 v,char* p){char tmp[32];int n=0;do{tmp[n++]=char('0'+v%10);v/=10;}while(v);for(int i=n-1;i>=0;--i)*p++=tmp[i];return p;};
        char* p=integer(w,buf);*p++='.';i64 div=10000000;for(int i=0;i<8;++i){*p++=char('0'+f/div);f%=div;div/=10;}*p=0;
        if(size_order(price,buf,precision,fee,out)!=0)return 3;
        if(out->notional<SCALE||out->quantity<=0||static_cast<i128>(out->notional)+out->fee>c||static_cast<i128>(g)+out->notional>e-out->fee)return 4;
        return 0;
    }catch(...){return 5;}
}
struct Rate {std::deque<i64> calls;i64 previous=-1;};
extern "C" void* rate_new(){try{return new Rate;}catch(...){return nullptr;}}
extern "C" void rate_free(void* h){delete static_cast<Rate*>(h);}
extern "C" int rate_take(void* h,i64 now,int limit,int reserve,int account,int account_limit){
    auto* r=static_cast<Rate*>(h);
    if(!r||now<r->previous||limit<=0||reserve<0||account<0)return 0;
    r->previous=now;
    while(!r->calls.empty()&&now-r->calls.front()>=60000)r->calls.pop_front();
    if(static_cast<int>(r->calls.size())+1+reserve>limit||std::max(account,static_cast<int>(r->calls.size()))+1+reserve>account_limit)return 0;
    r->calls.push_back(now);return 1;
}
extern "C" int state_event(int* state,int event){
    // 0 ready,1 submitted,2 unknown,3 pending,4 filled. Terminal states require explicit reconciliation outside this prototype.
    if(event==0){if(*state!=0)return 0;*state=1;return 1;}
    if(*state!=1)return -1;
    *state=event==1?2:(event==2?3:4);return 1;
}
