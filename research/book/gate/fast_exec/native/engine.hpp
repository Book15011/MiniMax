#pragma once
#include "abi.hpp"
#include "../core.cpp"
#include <unordered_map>
#include <unordered_set>
#include <vector>
namespace fast {
inline I money(const std::string& s){I v=0;if(money_parse(s.c_str(),&v))throw std::invalid_argument("exact decimal");return v;}
inline std::string plain(I v){if(v<0)throw std::invalid_argument("negative money");return std::to_string(v/100000000)+"."+std::to_string(100000000+v%100000000).substr(1);}
inline J size_result(const Sized& z){auto r=object();add(r.get(),"quantity",plain(z.quantity));add(r.get(),"notional",plain(z.notional));add(r.get(),"fee",plain(z.fee));return r;}
struct Config {
 J root;std::unordered_set<std::string> symbols;
 explicit Config(const std::string& path):root(load(path)){
  auto* a=field(root.get(),"symbols");if(json_object_get_type(a)!=5)throw std::invalid_argument("symbols");
  for(size_t i=0;i<json_object_array_length(a);++i)symbols.insert(str(json_object_array_get_idx(a,i))+"USDT");
 }
 I get(const char* k)const{return n(root.get(),k);}
};
struct OrderState {
 std::string id,state="READY";I requested=0,filled=0,sends=0;std::unordered_set<std::string> sent;
 bool blocked()const{return state=="SUBMITTED"||state=="PENDING"||state=="PARTIAL"||state=="UNKNOWN";}
 J snapshot(bool accepted=false,bool duplicate=false)const{
  auto r=object();add(r.get(),"accepted",accepted);add(r.get(),"duplicate",duplicate);add(r.get(),"state",state);
  add(r.get(),"filled",plain(filled));add(r.get(),"sends",sends);return r;
 }
 J begin(json_object* p){
  auto next=s(p,"id");I q=money(s(p,"quantity")),now=n(p,"now_ms"),exp=n(p,"expiry_ms");
  if(blocked()||next.empty()||next.size()>128||sent.count(next)||q<=0||now<0||exp<=now||sent.size()>=10000)return snapshot();
  id=next;requested=q;filled=0;state="SUBMITTED";sent.insert(next);++sends;return snapshot(true);
 }
 J timeout(json_object* p){if(s(p,"id")==id&&blocked())state="UNKNOWN";return snapshot();}
 J ack(json_object* p){
  if(id.empty())return snapshot();
  auto incoming=s(p,"id");auto next=s(p,"status");I q=money(s(p,"filled"));
  if(incoming!=id||!b(p,"success")||q<filled||q>requested||(next=="FILLED"&&q!=requested)||
    (next=="PARTIAL"&&(q<=0||q>=requested))||(next=="PENDING"&&q!=0)||
    (next=="REJECTED"&&q!=0)||(next!="FILLED"&&next!="PARTIAL"&&next!="PENDING"&&next!="CANCELED"&&next!="REJECTED")){
   state="UNKNOWN";return snapshot();
  }
  if(!blocked()){
   if(next==state&&q==filled)return snapshot(false,true);
   state="UNKNOWN";return snapshot();
  }
  filled=q;state=next;return snapshot(true);
 }
};
struct Book {std::string symbol;I bid=0,ask=0,bidq=0,askq=0,id=0,received=0;};
struct Detector {
 struct History {std::deque<std::pair<I,I>> values;I id=0,last=-1;bool active=false;};
 std::unordered_map<std::string,History> history;
 bool update(const Book& x,const Config& cfg){
  auto& h=history[x.symbol];
  if(x.id<=h.id||x.received<h.last)return false;
  h.id=x.id;h.last=x.received;
  auto& v=h.values;
  while(!v.empty()&&x.received-v.front().first>cfg.get("burst_max_reference_age_ms")*1000000)v.pop_front();
  I reference=0;
  for(const auto& a:v){if(x.received-a.first>=cfg.get("burst_horizon_ms")*1000000)reference=a.second;else break;}
  if(v.size()>=100000){v.clear();h.active=false;return false;}v.push_back({x.received,x.bid});
  bool on=reference>0&&static_cast<__int128>(x.bid-reference)*10000>=static_cast<__int128>(reference)*cfg.get("burst_min_bps");
  bool signal=on&&!h.active;h.active=on;return signal;
 }
 void reset(){history.clear();}
};
inline Book decode_book(json_object* p,I now,const Config& c){
 json_object* d=nullptr;if(!json_object_object_get_ex(p,"data",&d))d=p;
 Book x;x.symbol=s(d,"s");x.id=n(d,"u");x.received=now;
 if(!c.symbols.count(x.symbol)||x.id<=0||now<0)throw std::invalid_argument("unsupported book");
 x.bid=money(s(d,"b"));x.ask=money(s(d,"a"));x.bidq=money(s(d,"B"));x.askq=money(s(d,"A"));
 if(x.bid<=0||x.ask<x.bid||x.bidq<=0||x.askq<=0)throw std::invalid_argument("invalid book");
 return x;
}
inline J decision(json_object* p,const Config& c,bool unresolved){
 auto r=object();add(r.get(),"allowed",false);
 auto reject=[&](const std::string& why){add(r.get(),"reason",why);return std::move(r);};
 I now=n(p,"now_ms"),feed=n(p,"feed_ms"),qt=n(p,"quote_ms"),account=n(p,"account_ms");
 if(now<0||feed<0||qt<0||account<0||feed>now||qt>now||account>now||now-account>c.get("feed_max_receipt_age_ms"))return reject("stale_or_future_snapshot");
 if(!b(p,"verified_order_stats"))return reject("actual_order_timing_unverified");
 int h=health_permission(now-feed,0,0,n(p,"order_p95_ms"),n(p,"uncertainty_ms"),n(p,"order_samples"),unresolved?1:0,
 n(p,"opportunity_ms"),c.get("target_filled_ms"),c.get("health_local_budget_ms"),c.get("health_safety_margin_ms"),c.get("health_min_samples"),c.get("feed_max_receipt_age_ms"),c.get("clock_max_uncertainty_ms"));
 if(h)return reject("latency_permission_"+std::to_string(h));
 I ask=money(s(p,"price")),bid=money(s(p,"external_bid"));
 if(ask<=0||bid<=0||static_cast<__int128>(bid-ask)*10000<static_cast<__int128>(ask)*c.get("gap_min_bps")||
 static_cast<__int128>(bid)*(1000000-c.get("exit_fee_ppm"))<=static_cast<__int128>(ask)*(1000000+c.get("entry_fee_ppm")+c.get("extra_cost_ppm")))
 return reject("insufficient_fee_room");
 Sized z{};
 auto equity=s(p,"equity"),cash=s(p,"cash"),gross=s(p,"gross"),budget=s(p,"budget"),price=s(p,"price");I precision=n(p,"precision");
 if(precision<0||precision>8)return reject("unsupported_precision");
 int g=gate_order(now,feed,qt,n(p,"quote_rtt_ms"),n(p,"uncertainty_ms"),c.get("feed_max_receipt_age_ms"),c.get("quote_max_receipt_age_ms"),
 c.get("quote_max_rtt_ms"),c.get("clock_max_uncertainty_ms"),equity.c_str(),cash.c_str(),gross.c_str(),budget.c_str(),price.c_str(),
 static_cast<int>(precision),c.get("entry_fee_ppm"),&z);
 if(g)return reject("risk_or_freshness_"+std::to_string(g));
 add(r.get(),"allowed",true);add(r.get(),"reason",std::string("simulated_gateway_intent"));add(r.get(),"quantity",plain(z.quantity));add(r.get(),"fee",plain(z.fee));
 return r;
}
struct Protocol {
 const Config& cfg;OrderState order;Detector detector;void* rate=rate_new();std::unordered_map<std::string,I> last;
 explicit Protocol(const Config& c):cfg(c){if(!rate)throw std::bad_alloc();}
 ~Protocol(){rate_free(rate);}
 J process(json_object* p){
  auto cmd=s(p,"cmd");
  if(cmd=="version"){auto r=object();add(r.get(),"runtime",std::string("C++17"));add(r.get(),"transport",std::string(curl_version()));add(r.get(),"orders_network_enabled",false);return r;}
  if(cmd=="size"){
   Sized z{};I pr=n(p,"precision");if(pr<0||pr>8||size_order(s(p,"price").c_str(),s(p,"budget").c_str(),static_cast<int>(pr),n(p,"fee_ppm"),&z)||z.quantity<=0)throw std::invalid_argument("invalid size");
   return size_result(z);
  }
  if(cmd=="prepare"){
   auto pair=s(p,"pair"),q=s(p,"quantity"),t=s(p,"timestamp");
   if(pair.size()<5||pair.substr(pair.size()-4)!="/USD"||pair.size()>32||t.size()!=13||money(q)<=0)throw std::invalid_argument("request");
   for(char a:pair.substr(0,pair.size()-4))if(!((a>='A'&&a<='Z')||(a>='0'&&a<='9')))throw std::invalid_argument("pair");
   for(char a:t)if(a<'0'||a>'9')throw std::invalid_argument("timestamp");
   std::string body="pair="+pair+"&quantity="+q+"&side=BUY&timestamp="+t+"&type=MARKET";
   auto r=object();add(r.get(),"body",body);add(r.get(),"dummy_signature",hmac_fixture(body));return r;
  }
  if(cmd=="begin")return order.begin(p);
  if(cmd=="timeout")return order.timeout(p);
  if(cmd=="ack")return order.ack(p);
  if(cmd=="decision")return decision(p,cfg,order.blocked());
  if(cmd=="quota"){
   I used=n(p,"account_used");if(used<0||used>30)throw std::invalid_argument("account quota");
   bool ok=rate_take(rate,n(p,"now_ms"),static_cast<int>(cfg.get("process_calls_per_minute")),b(p,"exit")?0:static_cast<int>(cfg.get("reserve_exit_calls")),static_cast<int>(used),static_cast<int>(cfg.get("account_calls_per_minute")));
   auto r=object();add(r.get(),"accepted",ok);return r;
  }
  if(cmd=="book"){
   auto r=object();try{I stamp=n(p,"now_ms");if(stamp<0||stamp>9223372036854LL)throw std::invalid_argument("timestamp");Book x=decode_book(field(p,"packet"),stamp*1000000,cfg);
    if(x.id<=last[x.symbol]){add(r.get(),"valid",false);return r;}last[x.symbol]=x.id;
    bool signal=detector.update(x,cfg);add(r.get(),"valid",true);add(r.get(),"signal",signal);add(r.get(),"symbol",x.symbol);
   }catch(const std::invalid_argument&){add(r.get(),"valid",false);}return r;
  }
  throw std::invalid_argument("unknown command");
 }
};
}
