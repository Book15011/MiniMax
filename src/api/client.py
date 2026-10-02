"""Roostoo REST client (https://github.com/roostoo/Roostoo-API-Documents).

- Signed calls: sort parameters by key, join as k=v&..., HMAC-SHA256 with the secret (lowercase hex), headers
  RST-API-KEY and MSG-SIGNATURE. POST bodies are sent as exactly the signed string.
- Timestamps come from the local clock plus a measured offset to /v3/serverTime (the server rejects > 60 s skew).
- Every call passes a token bucket (default 20 calls/min; the documented limit is 30).
- Read-only calls retry transport errors, 429 and 5xx with backoff. Order-changing calls NEVER retry: a timeout
  raises OrderStateUnknown and the caller must reconcile with query_order before doing anything else.
- Errors arrive as HTTP 200 with Success=false; "no pending order" / "no order matched" mean empty, not failure.
- Keys are never logged or printed.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import requests

EMPTY_MESSAGES = ("no pending order", "no order matched")


class RoostooError(Exception):
    """The exchange answered Success=false (message in args[0])."""


class OrderStateUnknown(RoostooError):
    """An order-changing request may or may not have executed. Reconcile with query_order; never resend blindly."""


@dataclass(frozen=True)
class Credentials:
    api_key: str = field(repr=False)
    secret: str = field(repr=False)
    env: str = "test"          # "test" or "competition" (ROOSTOO_ENV)

    def __repr__(self) -> str:
        return f"Credentials(env={self.env!r}, api_key=***)"


def load_credentials(env_file: str | Path | None = None) -> Credentials:
    """Read ROOSTOO_API_KEY, ROOSTOO_SECRET_KEY and ROOSTOO_ENV from the environment or a .env file."""
    if env_file is not None and Path(env_file).exists():
        from dotenv import dotenv_values
        vals = {k: v for k, v in dotenv_values(env_file).items() if v}
    else:
        vals = {}
    key = os.environ.get("ROOSTOO_API_KEY") or vals.get("ROOSTOO_API_KEY", "")
    secret = os.environ.get("ROOSTOO_SECRET_KEY") or vals.get("ROOSTOO_SECRET_KEY", "")
    env = (os.environ.get("ROOSTOO_ENV") or vals.get("ROOSTOO_ENV", "")).strip().lower()
    if not key or not secret:
        raise RoostooError("ROOSTOO_API_KEY / ROOSTOO_SECRET_KEY are not set (.env)")
    if env not in ("test", "competition"):
        raise RoostooError("ROOSTOO_ENV must be 'test' or 'competition' in .env")
    return Credentials(key, secret, env)


def sign(params: dict, secret: str) -> tuple[str, str]:
    """Return (totalParams, signature) exactly as the documentation defines them."""
    total = "&".join(f"{k}={params[k]}" for k in sorted(params))
    return total, hmac.new(secret.encode(), total.encode(), hashlib.sha256).hexdigest()


class RateLimiter:
    """At most `per_minute` calls in any rolling 60-second span (blocks until a slot is free)."""

    def __init__(self, per_minute: int, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep):
        self.per_minute, self.clock, self.sleep = per_minute, clock, sleep
        self.calls: deque[float] = deque()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        with self.lock:
            while True:
                now = self.clock()
                while self.calls and now - self.calls[0] >= 60.0:
                    self.calls.popleft()
                if len(self.calls) < self.per_minute:
                    self.calls.append(now)
                    return
                self.sleep(60.0 - (now - self.calls[0]) + 0.01)


class RoostooClient:
    def __init__(self, base_url: str, creds: Credentials | None = None, calls_per_minute: int = 20,
                 timeout_s: float = 10.0, session: requests.Session | None = None,
                 clock: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep,
                 log: logging.Logger | None = None):
        self.base = base_url.rstrip("/")
        self.creds = creds
        self.timeout = timeout_s
        self.http = session or requests.Session()
        self.clock, self.sleep = clock, sleep
        self.limiter = RateLimiter(calls_per_minute, sleep=sleep)
        self.offset_ms = 0.0
        self.log = log or logging.getLogger(__name__)

    # ---------------- plumbing ----------------
    def timestamp(self) -> str:
        return str(int(self.clock() * 1000 + self.offset_ms))

    def _send(self, method: str, path: str, params: dict, signed: bool, order: bool) -> dict:
        headers = {}
        body = None
        query = params
        if signed:
            if self.creds is None:
                raise RoostooError("this call needs API credentials")
            total, sig = sign(params, self.creds.secret)
            headers = {"RST-API-KEY": self.creds.api_key, "MSG-SIGNATURE": sig}
            if method == "POST":
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                body, query = total, None
        attempts = 1 if order else 3
        for attempt in range(1, attempts + 1):
            self.limiter.acquire()
            try:
                r = self.http.request(method, self.base + path, params=query, data=body, headers=headers,
                                      timeout=self.timeout)
            except requests.RequestException as e:
                if order:
                    raise OrderStateUnknown(f"{path}: transport error ({type(e).__name__}); reconcile before retrying")
                if attempt == attempts:
                    raise RoostooError(f"{path}: {type(e).__name__} after {attempts} attempts") from e
                self.sleep(2 ** attempt)
                continue
            if r.status_code == 429 or r.status_code >= 500:
                if order:
                    raise OrderStateUnknown(f"{path}: HTTP {r.status_code}; reconcile before retrying")
                if attempt == attempts:
                    raise RoostooError(f"{path}: HTTP {r.status_code} after {attempts} attempts")
                self.sleep(2 ** attempt)
                continue
            if r.status_code != 200:
                raise RoostooError(f"{path}: HTTP {r.status_code}: {r.text[:200]}")
            return r.json()
        raise RoostooError(f"{path}: no response")

    def _call(self, method: str, path: str, params: dict | None = None, signed: bool = False,
              order: bool = False, stamp: bool = True, empty_ok: bool = False) -> dict:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        if stamp or signed:
            params["timestamp"] = self.timestamp()
        data = self._send(method, path, params, signed, order)
        if data.get("Success", True) is False:
            msg = str(data.get("ErrMsg", ""))
            if empty_ok and any(m in msg.lower() for m in EMPTY_MESSAGES):
                return {**data, "_empty": True}
            raise RoostooError(f"{path}: {msg or 'Success=false'}")
        return data

    # ---------------- public ----------------
    def server_time(self) -> int:
        return int(self._call("GET", "/v3/serverTime", stamp=False)["ServerTime"])

    def sync_clock(self) -> float:
        """Measure server - local time (ms), using the midpoint of the round trip."""
        t0 = self.clock()
        server = self.server_time()
        t1 = self.clock()
        self.offset_ms = server - (t0 + t1) / 2 * 1000
        return self.offset_ms

    def exchange_info(self) -> dict:
        return self._call("GET", "/v3/exchangeInfo", stamp=False)

    def ticker(self, pair: str | None = None) -> dict:
        return self._call("GET", "/v3/ticker", {"pair": pair}).get("Data", {})

    # ---------------- signed, read-only ----------------
    def balance(self) -> dict:
        """{coin: {"Free": float, "Lock": float, ...}}. The live API answers with `SpotWallet` (plus an empty
        `MarginWallet`), not the `Wallet` of the docs: reading only `Wallet` showed a funded account as empty
        (TEST account, 2026-10-02: SpotWallet USD Free 50000). Both are accepted."""
        d = self._call("GET", "/v3/balance", signed=True)
        return d.get("SpotWallet") or d.get("Wallet") or {}

    def pending_count(self) -> dict:
        d = self._call("GET", "/v3/pending_count", signed=True, empty_ok=True)
        return {"TotalPending": 0, "OrderPairs": {}} if d.get("_empty") else d

    def query_order(self, order_id: str | int | None = None, pair: str | None = None,
                    pending_only: bool | None = None, offset: int | None = None, limit: int | None = None) -> list[dict]:
        if order_id is not None:
            params = {"order_id": str(order_id)}          # no other optional parameter allowed with order_id
        else:
            params = {"pair": pair, "offset": offset, "limit": limit,
                      "pending_only": None if pending_only is None else ("TRUE" if pending_only else "FALSE")}
        d = self._call("POST", "/v3/query_order", params, signed=True, empty_ok=True)
        return [] if d.get("_empty") else list(d.get("OrderMatched") or [])

    def short_positions(self) -> list[dict]:
        return list(self._call("GET", "/v6/short_positions", signed=True).get("Positions") or [])

    # ---------------- signed, order-changing (never retried) ----------------
    def place_order(self, pair: str, side: str, quantity: str, order_type: str = "MARKET",
                    price: str | None = None) -> dict:
        if order_type == "LIMIT" and price is None:
            raise ValueError("LIMIT orders need a price")
        params = {"pair": pair, "side": side.upper(), "type": order_type.upper(), "quantity": quantity,
                  "price": price if order_type == "LIMIT" else None}
        return self._call("POST", "/v3/place_order", params, signed=True, order=True).get("OrderDetail", {})

    def cancel_order(self, order_id: str | int | None = None, pair: str | None = None,
                     allow_cancel_all: bool = False) -> list:
        if order_id is None and pair is None and not allow_cancel_all:
            raise ValueError("cancel_order with no order_id or pair cancels EVERY pending order; pass allow_cancel_all=True")
        if order_id is not None and pair is not None:
            raise ValueError("send order_id or pair, not both")
        params = {"order_id": None if order_id is None else str(order_id), "pair": pair}
        return list(self._call("POST", "/v3/cancel_order", params, signed=True, order=True).get("CanceledList") or [])

    def short_open(self, pair: str, collateral: str, price: str | None = None) -> dict:
        params = {"pair": pair, "collateral": collateral, "order_type": "LIMIT" if price else None, "price": price}
        return self._call("POST", "/v6/short_open", params, signed=True, order=True)

    def short_close(self, pair: str, close_qty: str | None = None, close_pct: str | None = None) -> dict:
        params = {"pair": pair, "close_qty": close_qty, "close_pct": None if close_qty else close_pct}
        return self._call("POST", "/v6/short_close", params, signed=True, order=True)
