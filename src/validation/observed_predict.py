"""Run frozen inferred baseline WITHOUT reading any observed transaction log."""
from pathlib import Path
import argparse
import yaml
from src.validation.observed_study import load_market
from src.validation.observed_baseline import broker_replay,weights_from_hourly

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);ap.add_argument("--prefix",default="prediction_only")
    a=ap.parse_args();cfg=yaml.safe_load(Path(a.config).read_text())
    q,p,h=load_market(cfg)
    ev,path,_=broker_replay(p.loc[p.index>=__import__("pandas").Timestamp(cfg["start"])],cfg,q,weights_from_hourly(h,cfg))
    out=Path(cfg["output"]);ev.to_csv(out/(a.prefix+"_events.csv"),index=False)
    path.to_csv(out/(a.prefix+"_equity.csv"),index=False)
    print("Predicted",len(ev),"events without loading a transaction log.")
if __name__=="__main__":main()
