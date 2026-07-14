"""Query builders — each is a frozen pydantic model with a `.build()` method.
No query is executed here; that's `src/data.py`'s job.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ItemStatsQuery(BaseModel):
    """One row per champion-item; GLOBAL_GAMES_PLAYED lets `stats.py` reconstruct effective n."""

    model_config = ConfigDict(frozen=True)

    def build(self) -> str:
        return """
            SELECT
                i.CHAMPION,
                i.ITEM,
                i.ITEM_CATEGORY,
                i.PLAYER_PURCHASE_RATE,
                i.WIN_RATE,
                i.AVG_KDA,
                i.MOST_COMMON_FIRST_PURCHASE_MINUTE,
                i.TOP_ITEM_1,
                i.TOP_ITEM_2,
                i.TOP_ITEM_3,
                o.GLOBAL_GAMES_PLAYED
            FROM LEAGUE_RECORDS.GOLD.ITEM_STATS_AND_RECOMMENDATIONS AS i
            LEFT JOIN LEAGUE_RECORDS.GOLD.CHAMPION_OVERVIEW AS o
                ON o.CHAMPION_NAME = i.CHAMPION
        """


class ChampionOverviewQuery(BaseModel):
    """Champion-level meta used for the picker and the hero header."""

    model_config = ConfigDict(frozen=True)

    def build(self) -> str:
        return """
            SELECT
                CHAMPION_NAME      AS CHAMPION,
                MOST_PICKED_LANE,
                PRIMARY_LANE_SHARE,
                GLOBAL_GAMES_PLAYED,
                GLOBAL_PICK_RATE,
                GLOBAL_WIN_RATE,
                GLOBAL_BAN_RATE
            FROM LEAGUE_RECORDS.GOLD.CHAMPION_OVERVIEW
            ORDER BY CHAMPION_NAME
        """
