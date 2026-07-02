"""Data access — the ONLY module that talks to Snowflake.

Mode is decided once via `running_in_snowflake()` (presence of the SiS
session token), same pattern as `pipeline_monitor` / `role_importance`:

* In Streamlit-in-Snowflake: queries run through `st.connection("snowflake")`
  (thread-safe, required on container/SPCS runtimes — `get_active_session`
  is not safe there). Results are cached with TTLs aligned to the gold
  tables' TARGET_LAG (see `settings.CacheSettings`).
* Locally (no token): the same logical tables are read from CSVs in
  `assets/sample_data/` via `mock.py`.

Every public function here returns a pandas DataFrame and takes only a
`Settings` object, so `ui.py` and `stats.py` never need to know which mode
it's in.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from settings import Settings
from src import mock, query as q


def running_in_snowflake() -> bool:
    """Reliable SiS detection: the session token only exists inside Snowflake."""
    return os.path.isfile("/snowflake/session/token")


@st.cache_resource
def get_session(_settings: Settings):
    """Return the Snowpark session in SiS, or None when running locally."""
    if _settings.is_local:
        return None
    conn = st.connection("snowflake", ttl=_settings.snowflake.connection_ttl)
    return conn.session()


def _run(session, sql: str) -> pd.DataFrame:
    return session.sql(sql).to_pandas()


def load_item_stats(settings: Settings) -> pd.DataFrame:
    @st.cache_data(ttl=settings.cache.item_stats_ttl, show_spinner="Loading item stats…")
    def _load():
        if settings.is_local:
            return mock.item_stats_and_recommendations(settings.sample_data_dir)
        return _run(get_session(settings), q.ItemStatsQuery(settings).build())

    return _load()


def load_overview(settings: Settings) -> pd.DataFrame:
    @st.cache_data(ttl=settings.cache.overview_ttl, show_spinner="Loading champions…")
    def _load():
        if settings.is_local:
            return mock.champion_overview(settings.sample_data_dir)
        return _run(get_session(settings), q.ChampionOverviewQuery(settings).build())

    return _load()


def data_health(settings: Settings, items: pd.DataFrame, overview: pd.DataFrame) -> dict:
    """Small diagnostics surfaced in the UI — this is an internal dev tool, so
    showing source/size/mode is a feature, not clutter."""
    return {
        "mode": "Snowflake (live)" if not settings.is_local else "Local / Mock",
        "item_rows": len(items),
        "champions": items["CHAMPION"].nunique(),
    }
