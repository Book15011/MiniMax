from pathlib import Path
import pytest
from research.book.bear_exit.control_audit import compare_pairs

def test_identical_control_artifacts_pass(tmp_path):
 a=tmp_path/'a';b=tmp_path/'b';a.write_bytes(b'unchanged');b.write_bytes(b'unchanged')
 assert len(compare_pairs([(a,b)]))==1

def test_repriced_or_changed_control_is_rejected(tmp_path):
 a=tmp_path/'a';b=tmp_path/'b';a.write_bytes(b'fee:0.001');b.write_bytes(b'fee:0.002')
 with pytest.raises(ValueError,match='Control artifact differs'):compare_pairs([(a,b)])
