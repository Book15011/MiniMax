"""Copy a local file of any size to EC2 through Session Manager: base64, sent in 3000-character pieces (one session
each), decoded on EC2, then size and sha256 printed on both sides so you can compare. Writes only the remote path.

    python upload.py local_file /tmp/remote_name
"""
import base64
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from sess import start  # noqa: E402

local, remote = pathlib.Path(sys.argv[1]), sys.argv[2]
data = local.read_bytes()
b64 = base64.b64encode(data).decode()
parts = [b64[i:i + 3000] for i in range(0, len(b64), 3000)]
print(f"local: {len(data)} bytes, sha256 {hashlib.sha256(data).hexdigest()}, {len(parts)} parts")
assert start(f"rm -f {remote}.b64 {remote}; echo cleared") == 0
for k, p in enumerate(parts, 1):
    assert start(f"echo {p} >> {remote}.b64; echo part {k}/{len(parts)} saved") == 0
assert start(f"base64 -d {remote}.b64 > {remote} && rm -f {remote}.b64 && chmod 644 {remote} && "
             f"wc -c < {remote} && sha256sum {remote}") == 0
