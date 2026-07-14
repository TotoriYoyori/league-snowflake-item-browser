import os

import pandas as pd


# --------------- FILE CONSTANTS ---------------
SAMPLE_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "assets",
    "sample_data"
)
ITEM_STATS_CSV = "sf_item_stats_and_recommendations"
CHAMPION_OVERVIEW_CSV = "sf_champion_overview"


# --------------- MOCK SAMPLE DATA ---------------
def _read(sample_data_dir: str, name: str) -> pd.DataFrame:
    path = os.path.join(sample_data_dir, f"{name}.csv")
    return pd.read_csv(path)


def item_stats_and_recommendations() -> pd.DataFrame:
    """Item stats joined to each champion's GLOBAL_GAMES_PLAYED (mirrors the live query's join)."""
    items = _read(SAMPLE_DATA_DIR, ITEM_STATS_CSV)
    overview = _read(SAMPLE_DATA_DIR, CHAMPION_OVERVIEW_CSV)

    games = overview[["CHAMPION_NAME", "GLOBAL_GAMES_PLAYED"]].rename(
        columns={"CHAMPION_NAME": "CHAMPION"}
    )
    return items.merge(games, on="CHAMPION", how="left")


def champion_overview() -> pd.DataFrame:
    overview = _read(SAMPLE_DATA_DIR, CHAMPION_OVERVIEW_CSV)
    return overview.rename(columns={"CHAMPION_NAME": "CHAMPION"}).sort_values("CHAMPION")
