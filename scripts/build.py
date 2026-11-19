#!/usr/bin/env python3
"""Build the static site into _site/ from data/coins.db, data/spot.json and images/."""
import html
import json
import re
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
SITE = json.loads((ROOT / "site.json").read_text())
SPOT = json.loads((ROOT / "data" / "spot.json").read_text())
POCKETS = 20  # 4 x 5 binder page
TROY_OZ_G = 31.1035

esc = html.escape


def money(x, cents=None):
    if x is None:
        return "—"
    if cents is None:
        cents = x < 100
    return f"${x:,.2f}" if cents else f"${x:,.0f}"


def load():
    con = sqlite3.connect(ROOT / "data" / "coins.db")
    con.row_factory = sqlite3.Row
    con.executescript((ROOT / "data" / "schema.sql").read_text())
    rows = [dict(r) for r in con.execute("SELECT * FROM coins ORDER BY binder_page, slot, id")]
    coins = []
    for c in rows:
        c["year_disp"] = c["year_text"] or (str(c["year"]) if c["year"] else "")
        mm = f"-{c['mint_mark']}" if c["mint_mark"] else ""
        c["title"] = c["title"] or " ".join(x for x in [f"{c['year_disp']}{mm}", c["series"], c["denomination"]] if x)
        metal = (c["precious_metal"] or "").lower()
        if metal and c["weight_g"] and c["fineness"] and SPOT.get(metal):
            c["metal_oz"] = c["weight_g"] * c["fineness"] / TROY_OZ_G
            c["melt"] = c["metal_oz"] * SPOT[metal]
        else:
            c["metal_oz"] = c["melt"] = None
        melt = c["melt"] or 0
        lo = c["value_low"] if c["value_low"] is not None else c["value_high"]
        hi = c["value_high"] if c["value_high"] is not None else c["value_low"]
        c["eff_low"] = max(lo or 0, melt)
        c["eff_high"] = max(hi or 0, melt)
        c["melt_driven"] = melt > 0 and melt >= (hi or 0)
        coins.append(c)
    # assign binder positions to coins without one, after the last used pocket
    used = [(c["binder_page"], c["slot"]) for c in coins if c["binder_page"] and c["slot"]]
    nxt = max((p - 1) * POCKETS + s for p, s in used) if used else 0
    for c in coins:
        if not (c["binder_page"] and c["slot"]):
            c["binder_page"], c["slot"] = divmod(nxt, POCKETS)[0] + 1, nxt % POCKETS + 1
            nxt += 1
    coins.sort(key=lambda c: (c["binder_page"], c["slot"]))
    return coins


def coin_img(c, side, prefix, cls="coin"):
    f = c.get(f"photo_{side}")
    if c.get("item_type") == "note":
        cls += " note"
    if f and (ROOT / "images" / f).exists():
        return f'<img class="{cls}" src="{prefix}images/{esc(f)}" alt="{esc(c["title"])} — {side_name(c, side).lower()}" loading="lazy">'
    label = esc((c["denomination"] or "?")[:14])
    yr = esc(c["year_disp"])
    return (f'<svg class="{cls} ph" viewBox="0 0 100 100" role="img" aria-label="{esc(c["title"])} (no photo yet)">' +
            (f'<rect x="2" y="30" width="96" height="40" rx="2"/>' if "note" in cls else f'<circle cx="50" cy="50" r="46"/><circle cx="50" cy="50" r="38" class="ring"/>') +
            f'<text x="50" y="47">{label}</text><text x="50" y="62" class="yr">{yr}</text></svg>')


def side_name(c, side):
    if c.get("item_type") == "note":
        return "Front" if side == "obv" else "Back"
    return "Obverse" if side == "obv" else "Reverse"


def paragraphs(text):
    if not text:
        return ""
    out = []
    for para in re.split(r"\n\s*\n", text.strip()):
        p = esc(para.strip()).replace("\n", "<br>")
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        out.append(f"<p>{p}</p>")
    return "\n".join(out)


def page(title, body, prefix, desc=""):
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or SITE['tagline'])}">
<link rel="stylesheet" href="{prefix}assets/style.css">
<link rel="icon" href="{prefix}assets/favicon.svg">
</head><body>
<header class="top"><a class="brand" href="{prefix}index.html">{esc(SITE['title'])}</a>
<nav><a href="{prefix}index.html">Binder</a><a href="{prefix}index.html#list">List</a><a href="{prefix}about.html">About the values</a></nav></header>
<main>{body}</main>
<footer>Values are estimates for family reference, not appraisals.
<a href="{prefix}coins.csv">Download data (CSV)</a> · <a href="{prefix}coins.db">SQLite</a></footer>
<script src="{prefix}assets/app.js"></script>
</body></html>"""


def build_index(coins):
    total_lo = sum(c["eff_low"] * c["quantity"] for c in coins)
    total_hi = sum(c["eff_high"] * c["quantity"] for c in coins)
    melt = sum((c["melt"] or 0) * c["quantity"] for c in coins)
    count = sum(c["quantity"] for c in coins)
    review = sum(1 for c in coins if c["needs_review"])
    stats = f"""<section class="hero">
<h1>{esc(SITE['title'])}</h1><p class="tag">{esc(SITE['tagline'])}</p>
<div class="stats">
<div><span>{count:,}</span>items</div>
<div><span>{money(total_lo, False)}–{money(total_hi, False)}</span>estimated value</div>
{f'<div><span>{money(melt, False)}</span>silver/gold melt</div>' if melt else ''}
<div><span>{review}</span>flagged for a closer look</div>
</div></section>"""

    if not coins:
        return page(SITE["title"], stats + '<p class="empty">Nothing cataloged yet — the binder is waiting for its first page.</p>', "")

    countries = sorted({c["country"] for c in coins if c["country"]})
    filters = f"""<div class="filters">
<input id="q" type="search" placeholder="Search year, series, country…" aria-label="Search">
<select id="country" aria-label="Country"><option value="">All countries</option>{''.join(f'<option>{esc(x)}</option>' for x in countries)}</select>
<select id="metal" aria-label="Metal"><option value="">Any metal</option><option value="silver">Silver</option><option value="gold">Gold</option><option value="none">Base metal / paper</option></select>
<select id="type" aria-label="Type"><option value="">Coins &amp; notes</option><option value="coin">Coins</option><option value="note">Paper money</option></select>
<label><input id="flag" type="checkbox"> Flagged only</label>
<span id="shown"></span></div>"""

    pages = {}
    for c in coins:
        pages.setdefault(c["binder_page"], {})[c["slot"]] = c
    binder = ['<section id="binder" class="binder">']
    for pno in sorted(pages):
        binder.append(f'<div class="bpage"><div class="pno">Page {pno}</div><div class="pockets">')
        for s in range(1, POCKETS + 1):
            c = pages[pno].get(s)
            if not c:
                binder.append('<div class="pocket empty"></div>')
                continue
            binder.append(
                f'<a class="pocket" href="coin/{esc(c["id"])}.html" {attrs(c)}>'
                f'{coin_img(c, "obv", "")}<span class="lbl">{esc(c["title"])}</span>'
                f'<span class="val">{money(c["eff_low"])}{"–" + money(c["eff_high"]) if c["eff_high"] != c["eff_low"] else ""}</span>'
                f'{"<i class=flag title=\"Worth a closer look\">★</i>" if c["needs_review"] else ""}</a>')
        binder.append("</div></div>")
    binder.append("</section>")

    rows = []
    for c in coins:
        rows.append(f'<tr {attrs(c)}><td>{esc(c["id"])}</td><td><a href="coin/{esc(c["id"])}.html">{esc(c["title"])}</a></td>'
                    f'<td>{esc(c["country"] or "")}</td><td data-v="{c["year"] or 0}">{esc(c["year_disp"])}</td>'
                    f'<td>{esc(c["grade_est"] or c["certified"] or "")}</td><td class="n">{c["quantity"]}</td>'
                    f'<td class="n" data-v="{c["eff_low"]:.2f}">{money(c["eff_low"])}–{money(c["eff_high"])}</td>'
                    f'<td class="n" data-v="{c["melt"] or 0:.2f}">{money(c["melt"]) if c["melt"] else ""}</td></tr>')
    table = f"""<section id="list" class="list"><h2>Full list</h2><table id="tbl">
<thead><tr><th>#</th><th>Coin</th><th>Country</th><th>Year</th><th>Grade (est.)</th><th class="n">Qty</th><th class="n">Value each</th><th class="n">Melt each</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></section>"""
    return page(SITE["title"], stats + filters + "".join(binder) + table, "")


def attrs(c):
    text = " ".join(str(c[k] or "") for k in ("id", "title", "country", "series", "variety", "denomination", "year_disp")).lower()
    return (f'data-text="{esc(text)}" data-country="{esc(c["country"] or "")}" '
            f'data-metal="{esc((c["precious_metal"] or "none").lower())}" data-type="{esc(c["item_type"] or "coin")}" data-flag="{1 if c["needs_review"] else 0}"')


def build_coin(c, prev, nxt):
    facts = [("Country", c["country"]), ("Denomination", c["denomination"]), ("Series", c["series"]),
             ("Year", c["year_disp"]), ("Mint mark", c["mint_mark"] or None),
             ("Variety", c["variety"]), ("Catalog ref", c["catalog_ref"]), ("Serial", c["serial"]),
             ("Composition", c["composition"]),
             ("Weight", f'{c["weight_g"]:g} g' if c["weight_g"] else None),
             ("Metal content", f'{c["metal_oz"]:.4f} troy oz {c["precious_metal"]}' if c["metal_oz"] else None),
             ("Quantity", c["quantity"] if c["quantity"] != 1 else None),
             ("Certified", c["certified"]), ("Grade (estimated)", c["grade_est"]),
             ("ID confidence", c["id_confidence"]), ("Binder", f'page {c["binder_page"]}, pocket {c["slot"]}')]
    dl = "".join(f"<dt>{esc(k)}</dt><dd>{esc(str(v))}</dd>" for k, v in facts if v not in (None, ""))
    val = f"""<div class="valuebox"><div class="big">{money(c['eff_low'])}{'–' + money(c['eff_high']) if c['eff_high'] != c['eff_low'] else ''}</div>
<div class="sub">estimated value{' each' if c['quantity'] > 1 else ''}</div>
<ul>
<li>Collector value: {money(c['value_low'])}{'–' + money(c['value_high']) if c['value_high'] not in (None, c['value_low']) else ''}{' — ' + esc(c['value_source']) if c['value_source'] else ''}{' (checked ' + esc(c['value_date']) + ')' if c['value_date'] else ''}</li>
{f"<li>Melt value: {money(c['melt'])} at ${SPOT[c['precious_metal'].lower()]:,.2f}/oz {esc(c['precious_metal'])} ({esc(SPOT.get('updated') or 'date not set')})</li>" if c['melt'] else ''}
{"<li><strong>Value is driven by metal content</strong> — it moves with the spot price.</li>" if c['melt_driven'] else ''}
{"<li class='flagline'>★ Flagged for a closer look — could be worth more than the photos show; consider in-person inspection or professional grading.</li>" if c['needs_review'] else ''}
</ul></div>"""
    navl = f'<a href="{esc(prev["id"])}.html">← {esc(prev["title"])}</a>' if prev else "<span></span>"
    navr = f'<a href="{esc(nxt["id"])}.html">{esc(nxt["title"])} →</a>' if nxt else "<span></span>"
    body = f"""<article class="coinpage">
<p class="crumb"><a href="../index.html">Binder</a> / page {c['binder_page']} / #{esc(c['id'])}</p>
<h1>{esc(c['title'])}</h1>
<div class="pics"><figure>{coin_img(c, 'obv', '../', 'coin lg')}<figcaption>{side_name(c, 'obv')}</figcaption></figure>
<figure>{coin_img(c, 'rev', '../', 'coin lg')}<figcaption>{side_name(c, 'rev')}</figcaption></figure></div>
<div class="cols"><div>
<h2>Why it's collectible</h2>{paragraphs(c['collectible_reason']) or '<p class="muted">Not written up yet.</p>'}
{('<h2>Notes</h2>' + paragraphs(c['notes'])) if c['notes'] else ''}
</div><aside>{val}<dl>{dl}</dl></aside></div>
<nav class="prevnext">{navl}{navr}</nav></article>"""
    return page(f"{c['title']} — {SITE['title']}", body, "../", (c["collectible_reason"] or "")[:150])


def build_about():
    body = f"""<article class="prose"><h1>About the values</h1>
<p>Every coin and note here was photographed and identified (country, date, mint mark or series, variety), then given an estimated value range. A few things to keep in mind:</p>
<p><strong>Grades are estimates.</strong> Condition matters enormously — the same date and mint can be worth a few dollars worn or hundreds uncirculated. Unless a coin is in a certified holder (PCGS, NGC, ANACS), its grade was estimated from photos and should be read as a range.</p>
<p><strong>Collector values</strong> come from published price guides (PCGS CoinFacts, NGC, the Greysheet) and recent sold listings, and are dated. They're refreshed periodically, not live.</p>
<p><strong>Melt values</strong> apply only to coins that contain silver or gold, using the spot price noted below. An item's estimated value is never shown below its melt value.</p>
<p><strong>★ Flagged coins</strong> are items where the photos leave real doubt — a possible rare variety, an error, or a high-grade example — and that are worth an in-person look or professional grading before anyone decides anything.</p>
{f"<p>Spot prices used for melt values: silver ${SPOT['silver']:,.2f}/oz (as of {esc(SPOT.get('updated') or '—')}).</p>" if SPOT.get('silver') else ''}
<p>These figures are for family reference only and are not a formal appraisal for insurance, estate or tax purposes.</p></article>"""
    return page(f"About the values — {SITE['title']}", body, "")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "coin").mkdir(parents=True)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    if (ROOT / "images").exists():
        shutil.copytree(ROOT / "images", OUT / "images")
    for f in ("coins.db", "coins.csv"):
        if (ROOT / "data" / f).exists():
            shutil.copy(ROOT / "data" / f, OUT / f)
    coins = load()
    (OUT / "index.html").write_text(build_index(coins))
    (OUT / "about.html").write_text(build_about())
    for i, c in enumerate(coins):
        prev = coins[i - 1] if i else None
        nxt = coins[i + 1] if i + 1 < len(coins) else None
        (OUT / "coin" / f"{c['id']}.html").write_text(build_coin(c, prev, nxt))
    pub = [{k: c[k] for k in c if not k.startswith("photo")} for c in coins]
    (OUT / "coins.json").write_text(json.dumps(pub, indent=1, default=str))
    (OUT / ".nojekyll").write_text("")
    print(f"built {len(coins)} coin page(s) into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
