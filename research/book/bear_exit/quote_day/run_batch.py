from pathlib import Path
import json,subprocess,sys,yaml
def main():
 c=yaml.safe_load(Path("research/book/bear_exit/quote_day/config.yaml").read_text());out=Path(c["output"]);out.mkdir(parents=True,exist_ok=True)
 if (out/"batch_status.json").exists():raise RuntimeError("Preserve existing batch")
 with (out/"batch.log").open("w") as f:code=subprocess.call([sys.executable,"-B","-m","research.book.bear_exit.quote_day.run"],stdout=f,stderr=subprocess.STDOUT)
 (out/"batch_status.json").write_text(json.dumps(dict(returncode=code),indent=2))
 raise SystemExit(code)
if __name__=="__main__":main()
