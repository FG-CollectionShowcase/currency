# Coin & currency catalog — working notes for Claude

Static site (GitHub Pages) cataloging a family coin and paper-money collection.
Pure Python stdlib, no dependencies. Push to `main` → Actions builds `_site/` and deploys.

## Layout
- `data/coins.db` — SQLite, **source of truth**. Schema in `data/schema.sql`.
- `data/coins.csv` — regenerated on every import; readable diff of the db. Don't hand-edit.
- `data/spot.json` — silver/gold spot for melt values. Manual only (`coins.py spot`); no automation by owner's choice.
- `images/NNNN-obv.jpg`, `images/NNNN-rev.jpg` — front/back photos, resized to ~1200px long edge, JPEG q≈85.
- `site.json` — site title and tagline.
- `scripts/coins.py` — init / import JSON / export / list.
- `scripts/build.py` — generates the site into `_site/`.

## Cataloging a batch
1. Photos arrive in chat or a Google Drive folder. Pair front/back, assign the next free 4-digit ids, resize into `images/`.
2. Identify each item from the photos: country, denomination, series, year, mint mark, variety, catalog ref
   (KM# / Red Book for coins, Friedberg/Pick for notes), composition, weight/fineness for silver/gold.
3. Write `collectible_reason`: 1–3 short paragraphs, plain language for family readers — what it is,
   historical context, what makes it scarce or not. Be honest when an item is common.
4. Value: `grade_est` as a range; `value_low`/`value_high` per item in USD; `value_source` and `value_date`.
   Web-search price guides / sold listings when unsure. Set `id_confidence`. Set `needs_review=1` for possible
   key dates, errors, varieties, high grades or anything the photos can't settle.
5. Write the batch to a JSON file (list of objects, keys = column names), then
   `python scripts/coins.py import batch.json`. Don't commit the JSON (`incoming/` is ignored).
6. `python scripts/build.py`, spot-check pages, commit db + csv + images, push.

Binder position (`binder_page`, `slot`) is auto-assigned in id order if left empty; 20 pockets per page.
Displayed value is never below melt.
