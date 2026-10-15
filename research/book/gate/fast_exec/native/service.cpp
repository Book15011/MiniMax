#include "engine.hpp"
#include "transport.hpp"
#include <thread>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <filesystem>
#include <iostream>
#include <numeric>
using namespace fast;
namespace fs=std::filesystem;
class Audit {
 std::ofstream out;std::mutex lock;std::condition_variable ready;std::deque<std::string> queue;
 bool done=false;std::thread worker;std::atomic<bool> failed{false};
 public:
 explicit Audit(const fs::path& path):out(path){if(!out)throw std::runtime_error("audit open");worker=std::thread([this]{
  for(;;){std::string line;{std::unique_lock<std::mutex> l(lock);ready.wait(l,[&]{return done||!queue.empty();});if(done&&queue.empty())break;line=std::move(queue.front());queue.pop_front();}
   out<<line<<'\n';if(!out)failed=true;
  }out.flush();if(!out)failed=true;
 });}
 ~Audit(){finish();}
 void append(json_object* p){auto line=dump(p);std::lock_guard<std::mutex> l(lock);if(failed||done||queue.size()>=8192){failed=true;throw std::runtime_error("audit unavailable");}queue.push_back(std::move(line));ready.notify_one();}
 void finish(){if(worker.joinable()){{std::lock_guard<std::mutex> l(lock);done=true;}ready.notify_one();worker.join();}}
 bool ok()const{return !failed;}
};
static void save(const fs::path& f,json_object* p){std::ofstream o(f);if(!o)throw std::runtime_error("output");o<<dump(p)<<'\n';if(!o)throw std::runtime_error("output");}
static J error_row(const std::string& value){auto r=object();add(r.get(),"error",value);return r;}
static void protocol(const Config& cfg){
 Protocol engine(cfg);std::string line;
 while(std::getline(std::cin,line)){
  J r=object();try{auto input=parse_json(line);r=engine.process(input.get());}
  catch(const std::exception& e){r=error_row(e.what());}
  std::cout<<dump(r.get())<<'\n'<<std::flush;
 }
}
static void cpu(const Config& cfg,const fs::path& output,int iterations){
 if(iterations<1000||iterations>1000000)throw std::invalid_argument("iterations");
 if(fs::exists(output))throw std::invalid_argument("existing output");fs::create_directories(output);
 const std::string message=R"({"cmd":"decision","now_ms":1000,"feed_ms":990,"quote_ms":995,"quote_rtt_ms":187,"uncertainty_ms":10,"order_p95_ms":187,"order_samples":30,"verified_order_stats":true,"opportunity_ms":500,"equity":"100000","cash":"100000","gross":"0","budget":"10","price":"1","external_bid":"1.004","precision":4,"account_ms":1000})";
 const std::string prep=R"({"cmd":"prepare","pair":"AVNT/USD","quantity":"9.99000000","timestamp":"1792000000000"})";
 Protocol engine(cfg);std::vector<I> samples;samples.reserve(iterations);I failures=0;volatile size_t bytes=0;
 for(int i=0;i<iterations+1000;++i){
  std::string book_message=R"({"cmd":"book","now_ms":)"+std::to_string(i)+R"(,"packet":{"s":"AVNTUSDT","u":)"+std::to_string(i+1)+R"(,"b":"1.00400000","a":"1.00410000","B":"100","A":"100"}})";
  I start=mono();auto book_input=parse_json(book_message);auto book_result=engine.process(book_input.get());bytes+=dump(book_result.get()).size();
  auto parsed=parse_json(message);auto r=engine.process(parsed.get());
  if(!b(r.get(),"allowed"))++failures;auto parsed_prepare=parse_json(prep);auto result=engine.process(parsed_prepare.get());bytes+=dump(result.get()).size();
  I elapsed=mono()-start;if(i>=1000)samples.push_back(elapsed);
 }
 std::sort(samples.begin(),samples.end());auto r=object();add(r.get(),"iterations",static_cast<I>(iterations));add(r.get(),"failures",failures);
 add(r.get(),"median_ns",samples[samples.size()/2]);add(r.get(),"p95_ns",samples[(samples.size()*95+99)/100-1]);add(r.get(),"p99_ns",samples[(samples.size()*99+99)/100-1]);
 add(r.get(),"maximum_ns",samples.back());add(r.get(),"over_1ms",static_cast<I>(std::count_if(samples.begin(),samples.end(),[](I x){return x>=1000000;})));
 add(r.get(),"network_or_fill_measured",false);add(r.get(),"pipeline",std::string("native book JSON decode/validation, pure burst detector, timing/risk/fee gate, sizing, serialization, OpenSSL dummy HMAC"));
 save(output/"cpu.json",r.get());std::cout<<dump(r.get())<<'\n';(void)bytes;
}
static void shadow(const Config& cfg,const fs::path& output,int seconds){
 if(seconds<60||seconds>1800||fs::exists(output))throw std::invalid_argument("new bounded shadow output required");
 fs::create_directories(output);Audit audit(output/"events.jsonl");
 std::atomic<bool> stop{false};std::atomic<I> requests{0},failures{0},books{0},episodes{0},feed_errors{0};
 struct Quotes {std::mutex mutex;std::string data;I received=0,rtt=0,offset=0,uncertainty=1000000;};Quotes quotes;
 I started=mono(),deadline=started+static_cast<I>(seconds)*1000000000;std::mutex sleep_mutex;std::condition_variable sleep_cv;
 auto wait_until=[&](I until){std::unique_lock<std::mutex> l(sleep_mutex);sleep_cv.wait_until(l,std::chrono::steady_clock::time_point(std::chrono::nanoseconds(until)),[&]{return stop.load();});};
 std::thread quote_worker([&]{
  try{
   Http http;I last=-1000000000000;int clocks=0;
   while(!stop&&mono()<deadline){
    wait_until(std::max(started,last+cfg.get("public_sample_interval_ms")*1000000));if(stop||mono()>=deadline)break;
    std::string path;if(clocks<3)path="/v3/serverTime";else {std::lock_guard<std::mutex> g(quotes.mutex);path="/v3/ticker?timestamp="+std::to_string(unixms()+quotes.offset);}
    last=mono();++requests;auto row=object();add(row.get(),"kind",std::string("public_request"));add(row.get(),"path",path.substr(0,path.find('?')));
    try{
     auto reply=http.get("https://mock-api.roostoo.com"+path);add(row.get(),"send_mono_ns",reply.begin);add(row.get(),"receive_mono_ns",reply.end);
     add(row.get(),"send_unix_ms",reply.wall);add(row.get(),"rtt_ns",reply.end-reply.begin);add(row.get(),"http_status",static_cast<I>(reply.status));add(row.get(),"curl_code",static_cast<I>(reply.code));
     bool ok=reply.code==0&&reply.status==200;
     if(ok){
      auto body=parse_json(reply.data);
      if(clocks<3){I server=n(body.get(),"ServerTime");std::lock_guard<std::mutex> g(quotes.mutex);I uncertainty=(reply.end-reply.begin+1999999)/2000000;
       if(uncertainty<quotes.uncertainty){quotes.offset=server-(reply.wall+(reply.end-reply.begin)/2000000);quotes.uncertainty=uncertainty;}
      }else{
       ok=b(body.get(),"Success")&&json_object_get_type(field(body.get(),"Data"))==4;
       if(ok){std::lock_guard<std::mutex> g(quotes.mutex);quotes.data=reply.data;quotes.received=reply.end;quotes.rtt=(reply.end-reply.begin+999999)/1000000;}
      }
      json_object_object_add(row.get(),"body",body.release());
     }
     if(!ok)++failures;add(row.get(),"success",ok);
    }catch(const std::exception& e){++failures;add(row.get(),"success",false);add(row.get(),"error",std::string(e.what()));}
    if(clocks<3)++clocks;audit.append(row.get());
   }
  }catch(const std::exception& e){++failures;try{auto r=error_row(e.what());add(r.get(),"kind",std::string("quote_worker_error"));audit.append(r.get());}catch(...){}stop=true;sleep_cv.notify_all();}
 });
 try{
  std::vector<std::string> ordered(cfg.symbols.begin(),cfg.symbols.end());std::sort(ordered.begin(),ordered.end());
  std::string path="/stream?streams=";for(size_t i=0;i<ordered.size();++i){if(i)path+="/";path+=lowercase(ordered[i])+"@bookTicker";}
  for(int attempt=0;attempt<3&&!stop&&mono()<deadline;++attempt){
   Detector detector;std::unordered_map<std::string,I> ids;
   try{
    websocket("https://data-stream.binance.vision:443"+path,"data-stream.binance.vision",path,deadline,[&](const std::string& text){
     I received=mono();auto p=parse_json(text);Book x=decode_book(p.get(),received,cfg);
     if(x.id<=ids[x.symbol])return;ids[x.symbol]=x.id;++books;bool signal=detector.update(x,cfg);
     auto event=object();add(event.get(),"kind",std::string("book"));add(event.get(),"receive_mono_ns",received);add(event.get(),"receive_unix_ms",unixms());
     add(event.get(),"burst_episode",signal);json_object_object_add(event.get(),"packet",p.release());audit.append(event.get());
     if(signal){
      ++episodes;auto decision_row=object();add(decision_row.get(),"kind",std::string("decision"));add(decision_row.get(),"symbol",x.symbol);
      add(decision_row.get(),"receive_mono_ns",received);add(decision_row.get(),"allowed",false);
      add(decision_row.get(),"model_function",std::string("Detector::update"));
      auto inputs=object();add(inputs.get(),"now_ms",received/1000000);add(inputs.get(),"feed_ms",received/1000000);
      add(inputs.get(),"account_ms",received/1000000);add(inputs.get(),"verified_order_stats",false);
      {std::lock_guard<std::mutex> g(quotes.mutex);
       add(inputs.get(),"quote_ms",quotes.received/1000000);
       add(decision_row.get(),"quote_age_ms",quotes.received?(received-quotes.received)/1000000:-1);
       add(decision_row.get(),"quote_rtt_ms",quotes.rtt);add(decision_row.get(),"clock_uncertainty_ms",quotes.uncertainty);}
      auto permission=decision(inputs.get(),cfg,false);add(decision_row.get(),"reason",s(permission.get(),"reason"));
      add(decision_row.get(),"account_is_paper_assumption",true);
      json_object_object_add(decision_row.get(),"permission",permission.release());
      audit.append(decision_row.get());
     }
    });
   }catch(const std::exception& e){++feed_errors;auto r=error_row(e.what());add(r.get(),"kind",std::string("feed_error"));add(r.get(),"attempt",static_cast<I>(attempt));audit.append(r.get());wait_until(std::min<I>(deadline,mono()+1000000000LL*(attempt+1)));}
  }
 }catch(const std::exception& e){++feed_errors;try{auto r=error_row(e.what());audit.append(r.get());}catch(...){}}
 stop=true;sleep_cv.notify_all();quote_worker.join();audit.finish();
 auto summary=object();add(summary.get(),"runtime",std::string("C++17"));add(summary.get(),"elapsed_ns",mono()-started);add(summary.get(),"books",books.load());
 add(summary.get(),"burst_episodes",episodes.load());add(summary.get(),"public_requests",requests.load());add(summary.get(),"request_failures",failures.load());
 add(summary.get(),"feed_errors",feed_errors.load());add(summary.get(),"audit_ok",audit.ok());add(summary.get(),"orders",I(0));add(summary.get(),"signed_calls",I(0));
 add(summary.get(),"eligible_entries",I(0));add(summary.get(),"actual_fill_latency_verified",false);add(summary.get(),"net_realized_pnl",std::string("0.00000000"));
 add(summary.get(),"production_eligible",false);add(summary.get(),"status",std::string(audit.ok()&&books>0?"PUBLIC_SHADOW_COMPLETED_LIVE_GATE_CLOSED":"SHADOW_FAILED"));
 save(output/"summary.json",summary.get());std::cout<<dump(summary.get())<<'\n';
}
int main(int argc,char** argv){
 if(curl_global_init(3))return 2;
 try{
  if(argc<3)throw std::invalid_argument("mode and configuration required");
  std::string mode=argv[1];Config config(argv[2]);
  if(mode=="protocol")protocol(config);
  else if(mode=="cpu"&&argc==5)cpu(config,argv[3],std::stoi(argv[4]));
  else if(mode=="shadow"&&argc==5)shadow(config,argv[3],std::stoi(argv[4]));
  else if(mode=="http-fixture"&&argc==4){
   if(!Http::loopback(argv[3]))throw std::invalid_argument("fixture is loopback only");Http h(true);auto x=h.get(argv[3],true);
   auto r=object();add(r.get(),"curl_code",I(x.code));add(r.get(),"http_status",I(x.status));add(r.get(),"elapsed_ns",x.end-x.begin);add(r.get(),"body",x.data);std::cout<<dump(r.get())<<'\n';
  }else if(mode=="ws-fixture"&&argc==4){
   std::string url=argv[3];if(!Http::loopback(url))throw std::invalid_argument("fixture is loopback only");
   auto slash=url.find('/',7);std::string host=url.substr(7,slash-7);I count=0;
   try{websocket(url,host,"/fixture",mono()+1000000000LL,[&](const std::string& data){auto p=parse_json(data);++count;std::cout<<dump(p.get())<<'\n'<<std::flush;},true);}
   catch(const std::exception& e){auto r=error_row(e.what());add(r.get(),"messages",count);std::cout<<dump(r.get())<<'\n';}
  }else throw std::invalid_argument("unsupported mode or arguments");
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';curl_global_cleanup();return 2;}
 curl_global_cleanup();return 0;
}
