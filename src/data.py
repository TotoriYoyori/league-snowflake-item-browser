"""Data access — the ONLY module that talks to Snowflake.

Mode is decided once via `IS_LOCAL`: live Snowflake queries in SiS, mock
CSVs (`mock.py`) locally. Every public function returns a plain DataFrame.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src import mock, query

# --------------- CONSTANTS ---------------
SAMPLE_DATA_DIR = os.environ.get(
    "LOCAL_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sample_data"),
)

# SiS session token file only exists inside Snowflake -> use Snowflake live data.
IS_LOCAL: bool = not os.path.isfile("/snowflake/session/token")

# TTLs in seconds, aligned to the gold tables' TARGET_LAG.
# Item table lags ~7 days; overview ~1.
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
        return mock.item_stats_and_recommendations(SAMPLE_DATA_DIR)

    return _run(get_session(), query.ItemStatsQuery().build())


@st.cache_data(ttl=OVERVIEW_TTL, show_spinner="Loading champions…")
def load_overview() -> pd.DataFrame:
    if IS_LOCAL:
        return mock.champion_overview(SAMPLE_DATA_DIR)

    return _run(get_session(), query.ChampionOverviewQuery().build())


def data_health(items: pd.DataFrame, overview: pd.DataFrame) -> dict:
    """Small diagnostics surfaced in the UI (source/size/mode)."""
    return {
        "mode": "Snowflake (live)" if not IS_LOCAL else "Local / Mock",
        "item_rows": len(items),
        "champions": items["CHAMPION"].nunique(),
    }
