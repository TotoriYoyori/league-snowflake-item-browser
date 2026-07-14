import os

import pandas as pd


def _read(sample_data_dir: str, name: str) -> pd.DataFrame:
    path = os.path.join(sample_data_dir, f"{name}.csv")
    return pd.read_csv(path)


def item_stats_and_recommendations(dir_: str) -> pd.DataFrame:
    """Item stats joined to each champion's GLOBAL_GAMES_PLAYED (mirrors the live query's join)."""
    items = _read(dir_, "sf_item_stats_and_recommendations")
    overview = _read(dir_, "sf_champion_overview")

    games = overview[["CHAMPION_NAME", "GLOBAL_GAMES_PLAYED"]].rename(
        columns={"CHAMPION_NAME": "CHAMPION"}
    )
    return items.merge(games, on="CHAMPION", how="left")


def champion_overview(dir_: str) -> pd.DataFrame:
    overview = _read(dir_, "sf_champion_overview")
    return overview.rename(columns={"CHAMPION_NAME": "CHAMPION"}).sort_values("CHAMPION")
