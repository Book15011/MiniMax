"""Run a bash script on the bot's EC2 instance through a Session Manager session:
region ap-southeast-2, document AWS-StartInteractiveCommand, the script sent gzip+base64 inside `bash -c`.
Keys from session.json (this PC only, never printed); the Session Manager plugin from plugin_dl/pkg/bin.

    python sess.py script <file>    run the script file (it must print something, or the session hangs)
    python sess.py raw "<cmd>"      run one short command line
"""
import base64
import gzip
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
INSTANCE = "i-0fcf5ff7472a15e52"
c = json.loads((HERE / "session.json").read_text())
env = dict(os.environ, AWS_ACCESS_KEY_ID=c["key"], AWS_SECRET_ACCESS_KEY=c["secret"], AWS_SESSION_TOKEN=c["token"],
           AWS_DEFAULT_REGION=c["region"],
           PATH=str(HERE / "plugin_dl" / "pkg" / "bin") + os.pathsep + os.environ.get("PATH", ""))


def start(cmd: str, timeout: int = 900) -> int:
    assert "'" not in cmd, "the command goes inside bash -c '...'"
    params = json.dumps({"command": [f"bash -c '{cmd}'"]})
    cli = [sys.executable, "-m", "awscli", "ssm", "start-session", "--region", c["region"], "--target", INSTANCE,
           "--document-name", "AWS-StartInteractiveCommand", "--parameters", params]
    r = subprocess.run(cli, env=env, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    out = r.stdout.replace("\r\n", "\n")
    print(out, end="" if out.endswith("\n") else "\n")
    if r.stderr.strip():
        print("--- stderr ---\n" + r.stderr[-2000:])
    print(f"--- session exit {r.returncode}")
    return r.returncode


if __name__ == "__main__":
    kind, arg = sys.argv[1], sys.argv[2]
    if kind == "script":
        b64 = base64.b64encode(gzip.compress(pathlib.Path(arg).read_bytes().replace(b"\r\n", b"\n"))).decode()
        assert len(b64) < 3400, f"script too large for one session ({len(b64)} chars)"
        sys.exit(start(f"echo {b64} | base64 -d | gunzip > /tmp/book_run.sh && bash /tmp/book_run.sh; rm -f /tmp/book_run.sh"))
    sys.exit(start(arg))
