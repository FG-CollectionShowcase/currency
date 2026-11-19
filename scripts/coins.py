#!/usr/bin/env python3
"""Catalog maintenance.

  python scripts/coins.py init                     create data/coins.db from schema.sql
  python scripts/coins.py import FILE.json [...]   upsert coins from JSON (object or list of objects)
  python scripts/coins.py export                   write data/coins.csv (human-readable diff of the db)
  python scripts/coins.py spot                     refresh data/spot.json from a public spot-price API
  python scripts/coins.py list                     print a short table of the catalog
"""
import csv
import json
import sqlite3
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "coins.db"
SCHEMA = ROOT / "data" / "schema.sql"
SPOT = ROOT / "data" / "spot.json"
CSV = ROOT / "data" / "coins.csv"


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA.read_text())
    return con


def columns(con):
    return [r[1] for r in con.execute("PRAGMA table_info(coins)")]


def cmd_init(_):
    connect().close()
    print(f"ready: {DB.relative_to(ROOT)}")


def cmd_import(paths):
    con = connect()
    cols = set(columns(con))
    n = 0
    for p in paths:
        data = json.loads(Path(p).read_text())
        for row in data if isinstance(data, list) else [data]:
            unknown = set(row) - cols
            if unknown:
                sys.exit(f"{p}: unknown fields {sorted(unknown)}")
            if "id" not in row:
                sys.exit(f"{p}: every coin needs an 'id'")
            row.setdefault("added_date", date.today().isoformat())
            for side in ("obv", "rev"):
                key = f"photo_{side}"
                if not row.get(key) and (ROOT / "images" / f"{row['id']}-{side}.jpg").exists():
                    row[key] = f"{row['id']}-{side}.jpg"
            existing = con.execute("SELECT 1 FROM coins WHERE id=?", (row["id"],)).fetchone()
            if existing:
                sets = ", ".join(f"{k}=?" for k in row if k != "id")
                con.execute(f"UPDATE coins SET {sets} WHERE id=?",
                            [v for k, v in row.items() if k != "id"] + [row["id"]])
            else:
                keys = list(row)
                con.execute(f"INSERT INTO coins ({','.join(keys)}) VALUES ({','.join('?' * len(keys))})",
                            [row[k] for k in keys])
            n += 1
    con.commit()
    print(f"upserted {n} coin(s)")
    cmd_export([])


def cmd_export(_):
    con = connect()
    cols = columns(con)
    with CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in con.execute("SELECT * FROM coins ORDER BY id"):
            w.writerow([r[c] for c in cols])
    print(f"wrote {CSV.relative_to(ROOT)}")


def fetch_price(symbol):
    req = urllib.request.Request(f"https://api.gold-api.com/price/{symbol}",
                                 headers={"User-Agent": "coin-catalog/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return float(json.load(r)["price"])


def cmd_spot(_):
    spot = json.loads(SPOT.read_text()) if SPOT.exists() else {}
    got = {}
    for metal, sym in (("silver", "XAG"), ("gold", "XAU"), ("platinum", "XPT")):
        try:
            got[metal] = round(fetch_price(sym), 2)
        except Exception as e:  # keep last known price on failure
            print(f"spot {metal}: fetch failed ({e}); keeping {spot.get(metal)}")
    if got:
        spot.update(got)
        spot["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        spot["source"] = "gold-api.com"
        SPOT.write_text(json.dumps(spot, indent=2) + "\n")
    print(json.dumps(spot))


def cmd_list(_):
    con = connect()
    for r in con.execute("SELECT id, year, mint_mark, denomination, series, value_low, value_high FROM coins ORDER BY id"):
        print(f"{r['id']:>5}  {r['year'] or '':>4}{r['mint_mark'] or '':<3} {r['denomination'] or '':<14} "
              f"{r['series'] or '':<24} ${r['value_low'] or 0:,.2f}–${r['value_high'] or 0:,.2f}")


if __name__ == "__main__":
    cmds = {"init": cmd_init, "import": cmd_import, "export": cmd_export, "spot": cmd_spot, "list": cmd_list}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](sys.argv[2:])
