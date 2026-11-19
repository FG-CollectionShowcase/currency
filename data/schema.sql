-- Coin & currency collection catalog. data/coins.db is the source of truth;
-- this file defines its structure and is applied by scripts/coins.py init.

CREATE TABLE IF NOT EXISTS coins (
    id                 TEXT PRIMARY KEY,      -- inventory number, e.g. '0001' (matches photo file names)
    item_type          TEXT NOT NULL DEFAULT 'coin',  -- 'coin' | 'note' (paper money) | 'token' | 'set'
    binder_page        INTEGER,               -- virtual binder page (20 pockets per page)
    slot               INTEGER,               -- pocket 1-20 on that page
    country            TEXT NOT NULL DEFAULT 'United States',
    denomination       TEXT,                  -- 'Half Dollar', '1 Cent', '5 Francs'
    series             TEXT,                  -- 'Walking Liberty', 'Lincoln Wheat'
    year               INTEGER,               -- for sorting; NULL if undated
    year_text          TEXT,                  -- display form if not a plain year ('ND', '1941-45')
    mint_mark          TEXT,                  -- 'D', 'S', 'P', 'O', 'CC', '' for none
    variety            TEXT,
    catalog_ref        TEXT,                  -- KM#, Pick#, Friedberg#, Red Book ref
    serial             TEXT,                  -- banknote serial number (notes only)                  -- 'Doubled Die Obverse', 'Proof', 'Type 2'
    composition        TEXT,                  -- '90% silver, 10% copper'
    precious_metal     TEXT,                  -- 'silver' | 'gold' | 'platinum' | NULL
    fineness           REAL,                  -- 0.900
    weight_g           REAL,                  -- gross weight in grams
    quantity           INTEGER NOT NULL DEFAULT 1,
    grade_est          TEXT,                  -- 'VF-30 to XF-40' (estimated from photos unless certified)
    certified          TEXT,                  -- 'PCGS MS-64 #12345678' if slabbed
    value_low          REAL,                  -- collector value range, USD, per coin
    value_high         REAL,
    value_source       TEXT,                  -- 'PCGS price guide', 'eBay sold comps', 'face value'
    value_date         TEXT,                  -- YYYY-MM-DD the value was checked
    id_confidence      TEXT,                  -- 'high' | 'medium' | 'low'
    needs_review       INTEGER NOT NULL DEFAULT 0,  -- 1 = worth an in-person look / professional grading
    title              TEXT,                  -- short display name; generated if NULL
    collectible_reason TEXT,                  -- why it matters to collectors (markdown-lite paragraphs)
    notes              TEXT,                  -- condition notes, family history, provenance
    photo_obv          TEXT,                  -- path under images/, e.g. '0001-obv.jpg'
    photo_rev          TEXT,
    added_date         TEXT
);
