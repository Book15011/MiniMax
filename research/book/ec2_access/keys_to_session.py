"""Turn the temporary-credentials block copied from the AWS access portal into session.json next to this file.
Paste the block, then end input (Ctrl+Z then Enter on Windows, Ctrl+D elsewhere). Accepts the bash (`export X="..."`),
PowerShell (`$Env:X="..."`) and cmd (`set X=...`) forms. Prints nothing secret.

    python keys_to_session.py            then paste
    python keys_to_session.py --region ap-southeast-2
"""
import json
import pathlib
import re
import sys

region = sys.argv[sys.argv.index("--region") + 1] if "--region" in sys.argv else "ap-southeast-2"
text = sys.stdin.read()
vals = {}
for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
    m = re.search(rf'{name}\s*=\s*"?([^"\s]+)"?', text)
    if not m:
        sys.exit(f"{name} not found in the pasted text")
    vals[name] = m.group(1)
out = pathlib.Path(__file__).parent / "session.json"
out.write_text(json.dumps({"key": vals["AWS_ACCESS_KEY_ID"], "secret": vals["AWS_SECRET_ACCESS_KEY"],
                           "token": vals["AWS_SESSION_TOKEN"], "region": region}))
print(f"session.json written (region {region}). Delete it when done; it is gitignored.")
