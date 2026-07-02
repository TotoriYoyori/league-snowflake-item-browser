# Itemization Explorer

## Which items are actually worth building — and which just look good?

Purchase rate tells you what's popular. It doesn't tell you what's *working*. My app separates the
two, per champion, so a heavily-bought item with a mediocre win rate and a rarely-bought item that
quietly overperforms don't get treated the same way.

*Is this item popular because it's good, or just because everyone else is buying it?*

Item win rates are smoothed with empirical-Bayes shrinkage toward each champion's own baseline —
not a flat 50% — so low-sample items don't get over-trusted and well-sampled items aren't dragged
around by noise.

> **Info**: This app is a standalone deployment of a larger League of Legends ELT Snowflake
> Pipeline, visit this [link here](https://github.com/TotoriYoyori/league-snowflake) to see more ~

----
## What This App Can Do

* Browse full item build stats for any champion — purchase rate, raw win rate, KDA, first-purchase
  timing.
* See an adjusted win rate per item, shrunk toward the champion's own baseline win rate.
* Surface **hidden gems** (winning, under-bought) and **trap items** (popular, underperforming) per
  champion.
* Click any item to see what it's commonly built alongside.
* Tune the shrinkage strength and minimum sample size live, from the sidebar.

> **Info:** Like the other apps in this pipeline, this one runs two ways from the same code —
> against the live warehouse inside Snowflake, or fully offline against a sample CSV for demos.

----
## What can it answer?

Built with internal teams in mind — balance/design, data science, data engineering — so the method
(shrinkage target, sample floor, thresholds) is visible and tunable, not just a black-box flag.

| Question | Answered by |
|----------|-------------|
| What's this champion's full item pool actually doing, stat-wise? | **Item builds** table |
| Is this popular item's win rate real, or noise from prior patches? | **Win (adj)** column |
| What's underrated on this champion right now? | **Hidden gems** panel |
| What's overrated — bought a lot, winning less? | **Trap items** panel |
| What do good players build after this item? | Click a row → **Commonly built with** |

----
## Method, in short

* **Effective n:** reconstructed per item from `purchase_rate × champion games played`, since the
  gold table only exposes rates.
* **Shrinkage:** each item's win rate is pulled toward its champion's pooled baseline by `k` games'
  worth of "benefit of the doubt" — high-n items barely move, low-n items collapse toward what's
  typical for that champion.
* **Gem / trap flags:** only assigned to items clearing the minimum sample floor, using
  within-champion purchase-rate and adjusted-win-rate quantiles — so a flag is never just noise from
  one unlucky (or lucky) game.

> Both `k` (shrinkage strength) and the minimum sample floor are sidebar controls — turn them down to
> see raw signal, turn them up to see only what's well-established.

----
## Data sources

Local/demo mode runs against a small placeholder sample under `assets/sample_data` — swap in a
fresher export any time, no code changes required.

For the production version (Streamlit-in-Snowflake), the following gold tables are sourced from my
pipeline.

| Source | Grain |
|--------|-------|
| `ITEM_STATS_AND_RECOMMENDATIONS` | 1 row per champion, per item |
| `CHAMPION_OVERVIEW` | 1 row per champion |

> This is [my ELT pipeline](https://github.com/TotoriYoyori/league-snowflake) to see the full works.

----
Original source: [LoL Match Intervals: 2 Million In-Game Snapshots](https://www.kaggle.com/datasets/nathansmallcalder/league-of-legends-match-interval-snapshots-2026)
