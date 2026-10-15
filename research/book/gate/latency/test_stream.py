import io,struct
import pytest
from research.book.gate.latency.stream import read_frame,client_frame
def test_reads_short_and_extended_server_frames():
    assert read_frame(io.BytesIO(b"\x81\x02{}"))==(True,1,b"{}")
    p=b"x"*200
    assert read_frame(io.BytesIO(b"\x81\x7e"+struct.pack("!H",len(p))+p))==(True,1,p)
def test_client_control_frame_is_masked_and_roundtrips():
    wire=client_frame(10,b"abc",mask=b"1234")
    assert wire[0]==0x8a and wire[1]==0x83
    assert bytes(x^wire[2+i%4] for i,x in enumerate(wire[6:]))==b"abc"
def test_rejects_masked_server_payload_and_large_control_frames():
    with pytest.raises(ValueError):read_frame(io.BytesIO(b"\x81\x80"))
    with pytest.raises(ValueError):client_frame(10,b"x"*126)
def test_truncated_frame_does_not_invent_a_message():
    with pytest.raises(EOFError):read_frame(io.BytesIO(b"\x81\x04ab"))
