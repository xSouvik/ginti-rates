# ginti-rates

Exchange rates for the currency converter in **Ginti: All Purpose Calculator**.

A GitHub Actions bot refreshes [`rates.json`](rates.json) three times a day
(00:20, 08:20 and 16:20 UTC) and commits it only when the rates change.

- Base currency: USD (`1 USD = rates[X] X`)
- Source: [fawazahmed0/exchange-api](https://github.com/fawazahmed0/exchange-api), CC0 1.0
- Fiat (ISO 4217) currencies only
- The bot refuses an update if required currencies are missing or many rates jump by more than 20% at once.

The app reads:

```
https://raw.githubusercontent.com/xSouvik/ginti-rates/main/rates.json
```

with `https://cdn.jsdelivr.net/gh/xSouvik/ginti-rates@main/rates.json` as a fallback,
and keeps the last good copy on the phone so it works offline.

Rates are for information only and may differ from bank or card rates.
