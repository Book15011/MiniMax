import pandas as pd,pytest
from research.book.short_compare13.combine import merge_all
def cohort(name):
 return pd.DataFrame([dict(model="book_bear_guard",case="a",scenario="original",hours=228,return_value=.01),dict(model=name,case="a",scenario="original",hours=228,return_value=.02)])
def test_four_parents_count_guard_once():
 f=merge_all([cohort("a"),cohort("b"),cohort("c"),cohort("d")])
 assert len(f)==5 and (f.model=="book_bear_guard").sum()==1 and set(f.model)=={"a","b","c","d","book_bear_guard"}
def test_fourth_parent_changed_control_is_rejected():
 frames=[cohort("a"),cohort("b"),cohort("c"),cohort("d")];frames[3].loc[0,"return_value"]=.011
 with pytest.raises(ValueError,match="Control differs"):merge_all(frames)
def test_repeated_noncontrol_model_is_rejected():
 with pytest.raises(ValueError,match="shared model"):merge_all([cohort("a"),cohort("b"),cohort("a")])
