import html

import pandas as pd
import streamlit as st

from src.ui.components import SECTION_LABELS, render_section_header


def render_item_table(df: pd.DataFrame) -> None:
    """Plain, sortable item table. Item selection happens via the picker on the Recommendations tab."""
    view = df.assign(
        Buy=df["PLAYER_PURCHASE_RATE"],
        Win=df["WIN_RATE"],
        Adj=df["ADJ_WIN_RATE"],
        n=df["EFF_N"].astype("Int64"),
        First=df["MOST_COMMON_FIRST_PURCHASE_MINUTE"],
    )[["ITEM", "ITEM_CATEGORY", "Buy", "Win", "Adj", "n", "AVG_KDA", "First", "FLAG"]]

    st.dataframe(
        view,
        hide_index=True,
        column_config={
            "ITEM": "Item",
            "ITEM_CATEGORY": "Tier",
            "Buy": st.column_config.NumberColumn("Buy %", format="percent"),
            "Win": st.column_config.NumberColumn("Win (raw)", format="percent"),
            "Adj": st.column_config.NumberColumn("Win (adj)", format="percent"),
            "n": st.column_config.NumberColumn("n", help="Estimated purchases"),
            "AVG_KDA": st.column_config.NumberColumn("KDA", format="%.2f"),
            "First": st.column_config.NumberColumn("1st buy", format="%d′"),
            "FLAG": "Signal",
        },
    )


def _signal_card(kind: str, title: str, rows: pd.DataFrame) -> str:
    items = ""
    for _, r in rows.iterrows():
        items += (
            f'<div class="ie-row"><span>{html.escape(str(r["ITEM"]))}</span>'
            f'<span class="v">{r["ADJ_WIN_RATE"]*100:.0f}% · buy {r["PLAYER_PURCHASE_RATE"]*100:.0f}%</span></div>'
        )
    if not items:
        items = '<div class="ie-row"><span class="v">none at this sample floor</span></div>'
    return f'<div class="ie-card {kind}"><div class="ie-card-hd">{title}</div>{items}</div>'


def render_signals(df: pd.DataFrame) -> None:
    gems = df[df["FLAG"] == "gem"].sort_values("ADJ_WIN_RATE", ascending=False).head(5)
    traps = df[df["FLAG"] == "trap"].sort_values("PLAYER_PURCHASE_RATE", ascending=False).head(5)

    gem_en, gem_zh = SECTION_LABELS["gems"]
    trap_en, trap_zh = SECTION_LABELS["traps"]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(_signal_card("gem", f"{gem_en} · {gem_zh}", gems), unsafe_allow_html=True)
    with c2:
        st.markdown(_signal_card("trap", f"{trap_en} · {trap_zh}", traps), unsafe_allow_html=True)


def render_item_builds_tab(champ_items: pd.DataFrame) -> None:
    render_section_header("items")
    render_item_table(champ_items)

    render_section_header("signals")
    render_signals(champ_items)
