"""Fetch the latest USD exchange rates and write rates.json.

Run by GitHub Actions three times a day (see .github/workflows/update-rates.yml).
Source: fawazahmed0/exchange-api (CC0 1.0, public domain), with a second
mirror if the first is down. The file is only rewritten when rates change,
and an update is refused if it looks broken (missing currencies or wild jumps).
"""
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCES = [
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json",
    "https://latest.currency-api.pages.dev/v1/currencies/usd.json",
]

# Active ISO 4217 currency codes (fiat only; the source also lists crypto).
ISO = set("""
AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL BSD BTN BWP BYN BZD
CAD CDF CHF CLP CNY COP CRC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD
GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT
LAK LBP LKR LRD LSL LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MYR MZN NAD NGN NIO NOK NPR
NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SOS SRD SSP
STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD UYU UZS VES VND VUV WST XAF XCD XOF
XPF YER ZAR ZMW ZWL
""".split())

# Currencies the Ginti app shows — all must be present.
REQUIRED = set("""
USD EUR INR GBP JPY CNY AED SAR AUD CAD CHF SGD HKD KRW BRL MXN ZAR RUB TRY SEK NOK DKK NZD THB IDR
MYR PHP PKR BDT LKR NPR EGP NGN VND
""".split())

OUT = Path(__file__).resolve().parent.parent / "rates.json"


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "ginti-rates-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status}")
        return json.loads(r.read(2_000_000))


def load_source() -> tuple[str, dict]:
    last_err = None
    for url in SOURCES:
        for attempt in range(3):
            try:
                data = fetch(url)
                usd = data["usd"]
                rates = {
                    k.upper(): float(v)
                    for k, v in usd.items()
                    if k.upper() in ISO and isinstance(v, (int, float)) and v > 0
                }
                rates["USD"] = 1.0
                return data.get("date", ""), rates
            except Exception as e:  # noqa: BLE001 — try the next attempt/mirror
                last_err = e
                time.sleep(5)
    raise SystemExit(f"all sources failed: {last_err}")


def main() -> int:
    date, rates = load_source()

    missing = REQUIRED - rates.keys()
    if missing:
        raise SystemExit(f"refusing update, missing: {sorted(missing)}")

    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8")).get("rates", {})
        except Exception:  # noqa: BLE001
            old = {}

    # Sanity check: real markets don't move 20%+ between runs for many currencies.
    if old:
        jumps = [c for c in REQUIRED if c in old and old[c] and abs(rates[c] / old[c] - 1) > 0.20]
        if len(jumps) > 3:
            raise SystemExit(f"refusing update, suspicious jumps: {jumps}")

    rounded = {k: float(f"{v:.8g}") for k, v in sorted(rates.items())}
    if rounded == old:
        print("rates unchanged, nothing to do")
        return 0

    now = datetime.now(timezone.utc)
    doc = {
        "base": "USD",
        "date": date,                       # market date of the source data
        "updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_unix": int(now.timestamp()),
        "source": "fawazahmed0/exchange-api (CC0 1.0)",
        "count": len(rounded),
        "rates": rounded,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(rounded)} rates for {date}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
