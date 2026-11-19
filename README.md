# The Family Coin & Currency Collection

A virtual binder of Mom's coins and paper money: each item photographed, identified, explained, and given an estimated value.

**Site:** https://fg-collectionshowcase.github.io/currency/

Values are estimates for family reference, not appraisals. Grades are estimated from photos unless an item is in a certified holder.

## How it works
- `data/coins.db` (SQLite) holds the catalog; `data/coins.csv` is a readable copy.
- `images/` holds front/back photos.
- `python scripts/build.py` turns those into a static site; GitHub Actions runs it and publishes to Pages on every push to `main`.
