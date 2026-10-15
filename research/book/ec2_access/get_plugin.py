"""Download AWS's Session Manager plugin for Windows (official S3 bucket) into its own folder and unpack it there,
without running any installer."""
import pathlib
import urllib.request
import zipfile

URL = "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/windows/SessionManagerPlugin.zip"
OUT = pathlib.Path(__file__).parent / "plugin_dl"
OUT.mkdir(exist_ok=True)
z = OUT / "SessionManagerPlugin.zip"
urllib.request.urlretrieve(URL, z)
print("downloaded", z.stat().st_size, "bytes")
with zipfile.ZipFile(z) as f:
    f.extractall(OUT / "outer")
inner = list((OUT / "outer").rglob("*.zip"))
for p in inner:
    with zipfile.ZipFile(p) as f:
        f.extractall(OUT / "pkg")
for p in sorted(OUT.rglob("*")):
    if p.is_file() and p.suffix.lower() in (".exe", ".bat", ".zip"):
        print(p.relative_to(OUT), p.stat().st_size)
