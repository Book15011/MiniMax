"""Wrap a Python script so it runs on EC2 in the background under the bot's venv and keeps running after the
session (or the temporary keys) end. Writes two small shell scripts next to this file:

    run_<name>.sh   decode the script to /tmp/<name>.py and start it with nohup; output goes to /tmp/<name>.out
    read_<name>.sh  say whether it is still running and print /tmp/<name>.out

    python make_bg_runner.py path/to/job.py [name]
    python sess.py script run_<name>.sh
    python sess.py script read_<name>.sh      (later, with fresh keys if the old ones expired)
"""
import base64
import gzip
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
src = pathlib.Path(sys.argv[1])
name = sys.argv[2] if len(sys.argv) > 2 else src.stem
b64 = base64.b64encode(gzip.compress(src.read_bytes().replace(b"\r\n", b"\n"))).decode()
run = (f"echo {b64} | base64 -d | gunzip > /tmp/{name}.py\n"
       f"cd /opt/minimax && setsid nohup sudo -u ec2-user env PYTHONPATH=/opt/minimax "
       f"/opt/minimax/.venv/bin/python /tmp/{name}.py > /tmp/{name}.out 2>&1 < /dev/null &\n"
       f"echo launched {name}\n")
read = (f'echo "== $(pgrep -f /tmp/{name}.py >/dev/null && echo running || echo finished)"\n'
        f"cat /tmp/{name}.out\n")
(HERE / f"run_{name}.sh").write_text(run, newline="\n")
(HERE / f"read_{name}.sh").write_text(read, newline="\n")
size = len(base64.b64encode(gzip.compress(run.encode())))
print(f"run_{name}.sh and read_{name}.sh written; launcher is {size} chars after sess.py encoding (limit ~3400)")
if size >= 3400:
    print("too large for one session: send the script with upload.py first, then launch it from /tmp")
