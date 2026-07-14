# Itemization Explorer

> **Live demo:** [league-sf-item-browser.streamlit.app](https://league-sf-item-browser.streamlit.app/)

> **Parent pipeline:** [github.com/TotoriYoyori/league-snowflake](https://github.com/TotoriYoyori/league-snowflake)

----
## What This App Can Do

* Browse full item build stats for any champion: purchase rate, raw win rate, KDA, first-purchase
  timing.
* See an adjusted win rate per item, shrunk toward the champion's own baseline win rate.
* Try to discover **hidden gems** (winning, under-bought) and **trap items** (popular, underperforming) per
  champion.
* Click any item to see what it's commonly built alongside (Recommendations tab)
* Tune the shrinkage strength and minimum sample size live, from the sidebar.

> **Info:** Like the other apps in this pipeline, this one runs two ways from the same code:
> against the live warehouse inside Snowflake, or fully offline against a sample CSV for demos.

## How it's built

- `src/query.py` (`ItemStatsQuery`, `ChampionOverviewQuery`): frozen pydantic models with a `.build()`
  method, run only when deployed against Snowflake.
- `src/data.py`: owns all data procurement, caching item stats and champion overview separately with
  TTLs matched to each gold table's own refresh lag, and reads mock CSVs locally via `mock.py`.
- `src/stats.py`: plain pandas/numpy functions with no Streamlit or Snowflake dependency: effective-n
  reconstruction, empirical-Bayes shrinkage, gem/trap flagging, and the Best-in-Slot scoring and
  recommendation build.
- `src/ui/`: renders the 2 tabs, one module per tab plus a shared `components.py` (header/hero/section
  chrome) and `theme.py` (color palette + CSS).
- `settings.py`: pydantic `Settings` built once at import, holding the shrinkage strength, sample
  floor, and Best-in-Slot weight knobs users adjust from the sidebar.

## Project structure

```
LeagueSnowflakeItemBrowser/
├── streamlit_app.py     # entry point
├── settings.py          # validated config
├── src/
│   ├── query.py         # live Snowflake query
│   ├── data.py          # all data procurement for ui display, and caching
│   ├── mock.py          # local CSV loaders, mirrors query.py's join
│   ├── stats.py         # pure shrinkage / gem-trap / BIS scoring functions
│   └── ui/               # renders: theme (palette + CSS) and components (shared chrome)
├── assets/
│   └── sample_data/     # placeholder champion/item CSVs, used whenever running locally
└── snowflake.yml         # deploy on Snowflake
```

## What can it answer?

| Question | Answered by |
|----------|-------------|
| What's this champion's full item pool actually doing, stat-wise? | **Item builds** table |
| Is this popular item's win rate real, or noise from prior patches? | **Win (adj)** column |
| What's underrated on this champion right now? | **Hidden gems** panel |
| What's overrated, bought a lot but winning less? | **Trap items** panel |
| What do good players build after this item? | Click a row → **Commonly built with** |

## Method, in short

* **Effective n:** reconstructed per item from `purchase_rate × champion games played`, since the
  gold table only exposes rates.
* **Shrinkage:** each item's win rate is pulled toward its champion's pooled baseline by `k` games'
  worth of "benefit of the doubt." High-n items barely move; low-n items collapse toward what's
  typical for that champion.
* **Gem / trap flags:** only assigned to items clearing the minimum sample floor, using
  within-champion purchase-rate and adjusted-win-rate quantiles, so a flag is never just noise from
  one unlucky (or lucky) game.

> Both `k` (shrinkage strength) and the minimum sample floor are sidebar controls. Turn them down to
> see raw signal, turn them up to see only what's well-established.

## Data sources

Local/demo mode runs against a small placeholder sample under `assets/sample_data`. Swap in a
fresher export any time, no code changes required.

For the production version (Streamlit-in-Snowflake), the following gold tables are sourced from my
pipeline.

| Source | Grain |
|--------|-------|
| `ITEM_STATS_AND_RECOMMENDATIONS` | 1 row per champion, per item |
| `CHAMPION_OVERVIEW` | 1 row per champion |

> This is [my ELT pipeline](https://github.com/TotoriYoyori/league-snowflake) to see the full works.

Getting started
----------------

```bash
uv sync
uv run streamlit run streamlit_app.py
```

Runs against the bundled sample CSVs by default. If you want to see the schema directly, the CSVs
are under `assets/sample_data`.

This repo is attached as a subfolder under the parent [`league-snowflake`](https://github.com/TotoriYoyori/league-snowflake).
Running from the parent repo will automatically register this app to query live from the database.

Known limitations
------------------
- No persisted history: every session recomputes fresh off the same static gold tables. Nothing
  snapshots a champion's gem/trap flags or recommended build for later comparison, so "patch over
  patch" tracking today means re-running this app on each patch's data and comparing manually.
- Gem/trap thresholds and the Best-in-Slot weights are hand-set, not fit or validated against actual
  win-rate lift (future additions).

Original source: [LoL Match Intervals: 2 Million In-Game Snapshots](https://www.kaggle.com/datasets/nathansmallcalder/league-of-legends-match-interval-snapshots-2026)
