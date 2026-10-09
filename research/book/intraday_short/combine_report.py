from pathlib import Path
from research.book.intraday_short import report
report.OUT=report.ROOT/"results/book/20261010-intraday-short-v3"
if __name__=="__main__":report.main(report.ROOT/"results/book/20261010-intraday-short-v2")
