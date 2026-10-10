import pandas as pd,pytest
from research.book.bear_exit.combine import merge_cohorts
def frame(model,value):
 return pd.DataFrame([dict(model=model,case='x',scenario='original',hours=228,return_=value)]).rename(columns={'return_':'return'})
def test_control_is_counted_once_and_new_models_remain():
 a=pd.concat([frame('book_bear_guard',.1),frame('old',.2)],ignore_index=True)
 b=pd.concat([frame('book_bear_guard',.1),frame('new',.3)],ignore_index=True)
 z=merge_cohorts(a,b)
 assert set(z.model)=={'book_bear_guard','old','new'} and len(z)==3
def test_changed_control_result_blocks_combined_rank():
 with pytest.raises(ValueError,match='Control differs'):
  merge_cohorts(frame('book_bear_guard',.1),frame('book_bear_guard',.2))
