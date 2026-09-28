# MiniMax

Automated spot trading bot for the Roostoo trading hackathon.

**Strategy:** TBD

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in ROOSTOO_API_KEY / ROOSTOO_SECRET_KEY
pytest
```

## Layout

- `src/api` – Roostoo REST client
- `src/data` – market data loading / features
- `src/strategy` – signal generation
- `src/risk` – position sizing and limits
- `backtest/` – offline backtesting
- `tests/` – unit tests
- `data/`, `logs/` – local only, gitignored
