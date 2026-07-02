"""Statistical core — pure pandas, no Streamlit and no Snowflake imports.

This is the only module with real logic, so it is deliberately isolated and
unit-testable on a plain DataFrame.

The method, in one line: item win rates are smoothed with empirical-Bayes
shrinkage (a Beta-binomial estimator) toward each champion's pooled win rate,
which stabilises the long tail of low-sample items. Gems and traps are then the
two interesting corners of (adjusted win rate) vs (purchase rate).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Strength of the prior, in units of games. k games of "benefit of the doubt"
# are handed to the baseline. Median item sits near n=7 here, so k in 20-50
# corrects the noisy tail while leaving well-sampled items essentially untouched.
DEFAULT_K = 20.0


def add_effective_n(df: pd.DataFrame) -> pd.DataFrame:
    """Reconstruct the sample size behind each win rate.

    The gold table only exposes a purchase *rate*, so we recover the count:
        effective n = purchase_rate * champion games played
        wins        = win_rate * effective n
    """
    out = df.copy()
    out["EFF_N"] = (out["PLAYER_PURCHASE_RATE"] * out["GLOBAL_GAMES_PLAYED"]).round()
    out["WINS"] = (out["WIN_RATE"] * out["EFF_N"]).round()
    return out


def shrink_winrate(df: pd.DataFrame, k: float = DEFAULT_K) -> pd.DataFrame:
    """Add ADJ_WIN_RATE via empirical-Bayes shrinkage toward the champion mean.

        baseline_c = sum(wins) / sum(n)          per champion
        adjusted_i = (wins_i + k * baseline_c) / (n_i + k)

    High-n items barely move; low-n items collapse toward the champion's own
    typical win rate (not a flat 50%, so strong/weak champions are judged
    against themselves).
    """
    out = df.copy()
    grp = out.groupby("CHAMPION")
    champ_wins = grp["WINS"].transform("sum")
    champ_n = grp["EFF_N"].transform("sum")
    baseline = np.where(champ_n > 0, champ_wins / champ_n, 0.5)

    out["CHAMPION_BASELINE"] = baseline
    out["ADJ_WIN_RATE"] = (out["WINS"] + k * baseline) / (out["EFF_N"] + k)
    return out


def flag_gems_traps(
    df: pd.DataFrame,
    min_n: int = 20,
    margin: float = 0.02,
    low_q: float = 0.33,
    high_q: float = 0.66,
) -> pd.DataFrame:
    """Label each item 'gem', 'trap', or '' within its champion.

    Only items clearing `min_n` are eligible, so a flag is never just noise.

        gem  = adjusted win rate above champion median + margin,
               AND purchase rate in the champion's bottom third  (winning, ignored)
        trap = purchase rate in the champion's top third,
               AND adjusted win rate below champion median - margin (popular, losing)
    """
    out = df.copy()
    out["FLAG"] = ""
    eligible = out["EFF_N"] >= min_n

    for champ, idx in out.groupby("CHAMPION").groups.items():
        rows = out.loc[idx]
        elig = rows[eligible.loc[idx]]
        if len(elig) < 3:
            continue

        adj_median = elig["ADJ_WIN_RATE"].median()
        buy_low = elig["PLAYER_PURCHASE_RATE"].quantile(low_q)
        buy_high = elig["PLAYER_PURCHASE_RATE"].quantile(high_q)

        is_gem = (
            (elig["ADJ_WIN_RATE"] >= adj_median + margin)
            & (elig["PLAYER_PURCHASE_RATE"] <= buy_low)
        )
        is_trap = (
            (elig["PLAYER_PURCHASE_RATE"] >= buy_high)
            & (elig["ADJ_WIN_RATE"] <= adj_median - margin)
        )
        out.loc[elig.index[is_gem], "FLAG"] = "gem"
        out.loc[elig.index[is_trap], "FLAG"] = "trap"

    return out


def add_bis_score(
    df: pd.DataFrame,
    w_win: float = 0.50,
    w_kda: float = 0.25,
    w_pop: float = 0.15,
    w_conf: float = 0.10,
    conf_scale: float = 20.0,
) -> pd.DataFrame:
    """Add BIS_SCORE — a composite 'how good is this item, really' signal used
    to rank the Flex slots in `build_recommendation`. Requires `prepare()` to
    have already run (needs ADJ_WIN_RATE and EFF_N).

    Blends four percentile-ranked signals, each computed *within* the
    champion so the mix is comparable across champions regardless of scale:

        win  = adjusted win rate rank        (is it actually winning more?)
        kda  = average KDA rank              (is it performing well individually?)
        pop  = purchase rate rank            (does the playerbase already trust it?)
        conf = 1 - exp(-EFF_N / conf_scale)  (how much sample backs this up?)

    `conf` is saturating rather than a raw percentile, so an item doesn't
    need effectively infinite purchases to be considered "well-established" —
    it just needs enough (conf_scale games) to mostly stop moving.
    """
    out = df.copy()
    grp = out.groupby("CHAMPION")

    p_win = grp["ADJ_WIN_RATE"].rank(pct=True)
    p_kda = grp["AVG_KDA"].rank(pct=True)
    p_pop = grp["PLAYER_PURCHASE_RATE"].rank(pct=True)
    p_conf = 1 - np.exp(-out["EFF_N"] / conf_scale)

    out["BIS_SCORE"] = w_win * p_win + w_kda * p_kda + w_pop * p_pop + w_conf * p_conf
    return out


def top_by_purchase_rate(df: pd.DataFrame, category: str, n: int, slot_label: str) -> pd.DataFrame:
    """Top `n` items in `category` by raw purchase rate — used for the
    "mandatory" slots (Starter, Trinket, Boots, Core) where the point isn't
    "is this the best performing item," it's "this is what everyone buys
    regardless of matchup," which purchase rate answers directly.

    Returns rows with a SLOT column attached ("Starter", "Core 1", "Core 2", ...).
    """
    rows = (
        df[df["ITEM_CATEGORY"] == category]
        .sort_values("PLAYER_PURCHASE_RATE", ascending=False)
        .head(n)
        .copy()
    )
    rows["SLOT"] = [slot_label if n == 1 else f"{slot_label} {i+1}" for i in range(len(rows))]
    return rows


def flex_slots(df: pd.DataFrame, exclude_items: set[str], n: int = 3) -> pd.DataFrame:
    """Top `n` Legendary items by BIS_SCORE, excluding whatever's already
    claimed by the Core slots — these are the situational picks the formula
    (win rate / KDA / purchase rate / sample confidence) is actually suited
    to rank, as opposed to the mandatory items where "most purchased" is
    already the right answer on its own.

    Requires `add_bis_score()` to have already run on `df`.
    """
    pool = df[(df["ITEM_CATEGORY"] == "Legendary") & (~df["ITEM"].isin(exclude_items))]
    rows = pool.sort_values("BIS_SCORE", ascending=False).head(n).copy()
    rows["SLOT"] = [f"Flex {i+1}" for i in range(len(rows))]
    return rows


def build_recommendation(df_scored: pd.DataFrame, core_n: int = 2, flex_n: int = 3) -> dict:
    """Assemble the full recommendation: two separate groups, not one
    undifferentiated "best 6" list — conflating "everyone buys this" with
    "this is the best performing pick" overstates how settled a build is.

        early:  Starter (1) + Trinket (1)      — situational, early game
        build:  Boots (1) + Core (core_n)      — purchase-rate, "must buy"
                + Flex (flex_n)                — formula-ranked, situational

    `df_scored` must already have ADJ_WIN_RATE, EFF_N (from `prepare()`) and
    BIS_SCORE (from `add_bis_score()`). Any slot gracefully returns fewer
    rows than requested if the champion doesn't have enough items in that
    category — never errors (e.g. Fiddlesticks has 0 Trinket rows).
    """
    starter = top_by_purchase_rate(df_scored, "Starter", 1, "Starter")
    trinket = top_by_purchase_rate(df_scored, "Trinket", 1, "Trinket")
    boots = top_by_purchase_rate(df_scored, "Boots", 1, "Boots")
    core = top_by_purchase_rate(df_scored, "Legendary", core_n, "Core")

    flex = flex_slots(df_scored, exclude_items=set(core["ITEM"]), n=flex_n)

    return {
        "early": pd.concat([starter, trinket], ignore_index=True),
        "build": pd.concat([boots, core, flex], ignore_index=True),
    }


def prepare(df: pd.DataFrame, k: float = DEFAULT_K, min_n: int = 20) -> pd.DataFrame:
    """Convenience pipeline: effective n -> shrinkage -> gem/trap flags."""
    return flag_gems_traps(shrink_winrate(add_effective_n(df), k=k), min_n=min_n)
