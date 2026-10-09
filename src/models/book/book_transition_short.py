from src.contracts import ModelSpec
from src.models.book import _transition_short as helper
class TransitionShort:
 spec=ModelSpec(name="book_transition_short",method="momentum",author="book",rebalance_hours=4,band=.02,uses_shorts=True,
  description="research: halve long risk in confirmed48h BTC/breadth weakness and add capped4h-confirmed shorts")
 def targets(self,view):return helper.targets(view)
MODEL=TransitionShort()
