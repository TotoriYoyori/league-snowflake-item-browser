import html
import textwrap

import pandas as pd
import streamlit as st

from src import data
from src.ui.theme import inject

# --------------- APP LABELING ---------------
APP_TITLE = "Itemization Explorer"
APP_SUBTITLE_EN = "League of Legends Item Builds: Stats, Signals & Recommendations"
APP_SUBTITLE_ZH = "英雄联盟装备统计 — 数据洞察与推荐"
TAB_LABELS = (
    ("Item Builds", "装备统计"),
    ("Recommendations", "推荐装备"),
)
SECTION_LABELS = {
    "controls": ("Controls", "筛选设置"),
    "method": ("Method", "计算方法"),
    "items": ("Item builds", "装备统计"),
    "signals": ("Signals", "数据信号"),
    "gems": ("Hidden gems", "潜力装备"),
    "traps": ("Trap items", "陷阱装备"),
    "recommendations": ("Commonly built with", "常见搭配"),
    "bis": ("Sample Build", "参考出装"),
    "pick_item": ("Pick an item", "选择装备"),
}

# --------------- STATUS PILLS (CSS classes defined in theme.py) ---------------
PILL_OK = "ie-pill-ok"
PILL_WARN = "ie-pill-warn"
PILL_FAIL = "ie-pill-fail"
PILL_NEUTRAL = "ie-pill-neutral"


# --------------- PAGE SETUP ---------------
def setup_page() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="⚜", layout="wide")
    inject(st)


def render_header() -> None:
    mode_label = "Local / Mock" if data.IS_LOCAL else "Snowflake (live)"
    mode_level = PILL_NEUTRAL if data.IS_LOCAL else PILL_OK
    st.markdown(
        textwrap.dedent(f"""
        <div class="ie-header">
            <div class="ie-title">{APP_TITLE}
                <span class="ie-pill {mode_level}">{mode_label}</span>
            </div>
            <div class="ie-subtitle-en">{APP_SUBTITLE_EN}</div>
            <div class="ie-subtitle-zh">{APP_SUBTITLE_ZH}</div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_section_header(section_key: str) -> None:
    en, zh = SECTION_LABELS[section_key]
    st.markdown(
        textwrap.dedent(f"""
        <div class="ie-section-header">
            <span class="ie-section-en">{en}</span>
            <span class="ie-section-zh">{zh}</span>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_hero(meta: pd.Series) -> None:
    def pct(x):
        return "—" if pd.isna(x) else f"{x * 100:.1f}%"

    name = html.escape(str(meta["CHAMPION"]))
    lane = html.escape(str(meta.get("MOST_PICKED_LANE", "")))
    st.markdown(
        f"""
        <div class="ie-hero">
          <p class="ie-hero-name">{name}</p>
          <p class="ie-hero-lane">{lane} · primary lane {pct(meta.get('PRIMARY_LANE_SHARE'))}</p>
          <div class="ie-pills">
            <span class="ie-pill-stat">pick <b>{pct(meta.get('GLOBAL_PICK_RATE'))}</b></span>
            <span class="ie-pill-stat">win <b>{pct(meta.get('GLOBAL_WIN_RATE'))}</b></span>
            <span class="ie-pill-stat">ban <b>{pct(meta.get('GLOBAL_BAN_RATE'))}</b></span>
            <span class="ie-pill-stat">games <b>{int(meta.get('GLOBAL_GAMES_PLAYED', 0)):,}</b></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_health(info: dict) -> None:
    st.caption(
        f"Source: {info['mode']} · {info['item_rows']:,} item rows · "
        f"{info['champions']} champions"
    )
