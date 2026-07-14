import os

import pandas as pd
import streamlit as st

from src import mock, query

# --------------- CONSTANTS ---------------
# SiS session token file only exists inside Snowflake -> use Snowflake live data.
IS_LOCAL: bool = not os.path.isfile("/snowflake/session/token")
ITEM_STATS_TTL = 6 * 60 * 60
OVERVIEW_TTL = 60 * 60


@st.cache_resource
def get_session():
    if IS_LOCAL:
        return None
    conn = st.connection("snowflake", ttl=None)
    return conn.session()


def _run(session, sql: str) -> pd.DataFrame:
    return session.sql(sql).to_pandas()


@st.cache_data(ttl=ITEM_STATS_TTL, show_spinner="Loading item stats…")
def load_item_stats() -> pd.DataFrame:
    if IS_LOCAL:
        return mock.item_stats_and_recommendations()

    return _run(get_session(), query.ItemStatsQuery().build())


@st.cache_data(ttl=OVERVIEW_TTL, show_spinner="Loading champions…")
def load_overview() -> pd.DataFrame:
    if IS_LOCAL:
        return mock.champion_overview()

    return _run(get_session(), query.ChampionOverviewQuery().build())


def data_health(items: pd.DataFrame, overview: pd.DataFrame) -> dict:
    """Small diagnostics surfaced in the UI (source/size/mode)."""
    return {
        "mode": "Snowflake (live)" if not IS_LOCAL else "Local / Mock",
        "item_rows": len(items),
        "champions": items["CHAMPION"].nunique(),
    }
