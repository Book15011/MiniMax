"""Unchanged Book public RFC6455 frame helpers from latency/stream.py."""
import os,struct

def read_frame(stream):
    def exact(n):
        data=b""
        while len(data)<n:
            chunk=stream.read(n-len(data))
            if not chunk:raise EOFError("truncated public frame")
            data+=chunk
        return data
    a,b=exact(2);fin=bool(a&128);opcode=a&15
    if a&112 or b&128:raise ValueError("unsupported or masked server frame")
    size=b&127
    if size==126:size=struct.unpack("!H",exact(2))[0]
    elif size==127:size=struct.unpack("!Q",exact(8))[0]
    if size>1_000_000 or (opcode>=8 and (size>125 or not fin)):raise ValueError("invalid public frame size")
    return fin,opcode,exact(size)

def client_frame(opcode,payload,mask=None):
    if len(payload)>125:raise ValueError("control frame too large")
    mask=os.urandom(4) if mask is None else mask
    return bytes([128|opcode,128|len(payload)])+mask+bytes(x^mask[i%4] for i,x in enumerate(payload))
