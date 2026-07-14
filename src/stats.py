import numpy as np
import pandas as pd

# --------------- SHRINKING CONSTANTS k (k games of benefit of the doubt) ---------------
DEFAULT_K = 20.0


# --------------- STATS ---------------
def add_effective_n(df: pd.DataFrame) -> pd.DataFrame:
    """Reconstruct the sample size behind each win rate.
        effective n = purchase_rate * champion games played
        wins        = win_rate * effective n
    """
    return (df
        .assign(EFF_N=lambda d: (d["PLAYER_PURCHASE_RATE"] * d["GLOBAL_GAMES_PLAYED"]).round())
        .assign(WINS=lambda d: (d["WIN_RATE"] * d["EFF_N"]).round())
    )


def shrink_winrate(df: pd.DataFrame, k: float = DEFAULT_K) -> pd.DataFrame:
    """Add ADJ_WIN_RATE via empirical-Bayes shrinkage toward the champion mean.
        baseline_c = sum(wins) / sum(n)          per champion
        adjusted_i = (wins_i + k * baseline_c) / (n_i + k)
    """
    return (df
        .assign(_CHAMP_WINS=lambda d: d.groupby("CHAMPION")["WINS"].transform("sum"))
        .assign(_CHAMP_N=lambda d: d.groupby("CHAMPION")["EFF_N"].transform("sum"))
        .assign(CHAMPION_BASELINE=lambda d:
            np.where(d["_CHAMP_N"] > 0, d["_CHAMP_WINS"] / d["_CHAMP_N"], 0.5)
        )
        .assign(ADJ_WIN_RATE=lambda d: (d["WINS"] + k * d["CHAMPION_BASELINE"]) / (d["EFF_N"] + k))
        .drop(columns=["_CHAMP_WINS", "_CHAMP_N"])
    )


def _gem_trap_flags(
    df: pd.DataFrame,
    min_n: int,
    margin: float,
    low_q: float,
    high_q: float,
) -> pd.Series:
    """Label each row 'gem', 'trap', or '' within its champion."""
    flags = pd.Series("", index=df.index)
    eligible = df["EFF_N"] >= min_n

    for champ, idx in df.groupby("CHAMPION").groups.items():
        rows = df.loc[idx]
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
        flags.loc[elig.index[is_gem]] = "gem"
        flags.loc[elig.index[is_trap]] = "trap"

    return flags


def flag_gems_traps(
    df: pd.DataFrame,
    min_n: int = 20,
    margin: float = 0.02,
    low_q: float = 0.33,
    high_q: float = 0.66,
) -> pd.DataFrame:
    return df.assign(
        FLAG=lambda d: _gem_trap_flags(d, min_n, margin, low_q, high_q)
    )


def add_bis_score(
    df: pd.DataFrame,
    w_win: float = 0.30,
    w_kda: float = 0.05,
    w_pop: float = 0.35,
    w_conf: float = 0.30,
    conf_scale: float = 100.0,
) -> pd.DataFrame:
    """Blends four percentile-ranked signals, each computed within a champion.
        win  = adjusted win rate rank        (is it actually winning more?)
        kda  = average KDA rank              (is it performing well individually?)
        pop  = purchase rate rank            (does the playerbase already trust it?)
        conf = 1 - exp(-EFF_N / conf_scale)  (how much sample backs this up?)
    """
    grp = df.groupby("CHAMPION")
    p_win = grp["ADJ_WIN_RATE"].rank(pct=True)
    p_kda = grp["AVG_KDA"].rank(pct=True)
    p_pop = grp["PLAYER_PURCHASE_RATE"].rank(pct=True)

    return df.assign(
        BIS_SCORE=lambda d: (
            w_win * p_win + w_kda * p_kda + w_pop * p_pop
            + w_conf * (1 - np.exp(-d["EFF_N"] / conf_scale))
        )
    )


def top_by_purchase_rate(
    df: pd.DataFrame,
    category: str,
    n: int,
    slot_label: str
) -> pd.DataFrame:
    """Top `n` items in `category` by raw purchase rate become core and starter items.
    Returns rows with a SLOT column attached ("Starter", "Core 1", "Core 2", ...).
    """
    return (df
        [df["ITEM_CATEGORY"] == category]
        .sort_values("PLAYER_PURCHASE_RATE", ascending=False)
        .head(n)
        .assign(SLOT=lambda d: [slot_label if n == 1 else f"{slot_label} {i+1}" for i in range(len(d))])
    )


def flex_slots(df: pd.DataFrame, exclude_items: set[str], n: int = 3) -> pd.DataFrame:
    """Top `n` Legendary items by BIS_SCORE become flex items."""
    return (df
        [(df["ITEM_CATEGORY"] == "Legendary") & (~df["ITEM"].isin(exclude_items))]
        .sort_values("BIS_SCORE", ascending=False)
        .head(n)
        .assign(SLOT=lambda d: [f"Flex {i+1}" for i in range(len(d))])
    )


def build_recommendation(df_scored: pd.DataFrame, core_n: int = 2, flex_n: int = 3) -> dict:
    """Assemble the full recommendation: starter + trinkets + boot + core + flex."""
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
    return (df
        .pipe(add_effective_n)
        .pipe(shrink_winrate, k=k)
        .pipe(flag_gems_traps, min_n=min_n)
    )
