"""Presentation ranks must never upgrade evidence or relabel unit proxies."""
import pandas as pd
from backtest.scoring.weak_render import short_rank_view,ranked_short_lines
def test_ranks_separate_accuracy_from_returns_and_samples():
 s=pd.DataFrame([
 {"model":"tiny","profile":"p","valid_6h":1,"onsets":1,"windows_with_onsets":1,"total_windows":25,"precision_6h":1.,"precision_6h_lower90":.1,"minimum_onsets_met":False,"window_mean_proxy_net_6h":.01},
 {"model":"broad","profile":"p","valid_6h":50,"onsets":50,"windows_with_onsets":15,"total_windows":25,"precision_6h":.6,"precision_6h_lower90":.4,"minimum_onsets_met":True,"window_mean_proxy_net_6h":.002},
 {"model":"none","profile":"p","valid_6h":0,"onsets":0,"windows_with_onsets":0,"total_windows":25,"precision_6h":float("nan"),"precision_6h_lower90":float("nan"),"minimum_onsets_met":False,"window_mean_proxy_net_6h":float("nan")}])
 before=s.copy(deep=True);r=short_rank_view(s)
 assert r.set_index("model").loc["broad","accuracy_rank"]==1
 assert r.set_index("model").loc["tiny","return_proxy_rank"]==1
 assert pd.isna(r.set_index("model").loc["none","accuracy_rank"])
 assert r.set_index("model").loc["tiny","evidence_label"]=="INSUFFICIENT"
 pd.testing.assert_frame_equal(s,before)
 t="\n".join(ranked_short_lines(s,pd.DataFrame({"model":["broad"],"return_mean":[-.01],"CS":[.1]})))
 assert "unit proxy" in t and "Full portfolio" in t and "INSUFFICIENT" in t
