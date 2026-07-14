import html

import pandas as pd
import streamlit as st

from settings import settings
from src import stats
from src.ui.components import SECTION_LABELS, render_section_header


def _item_picker(champ_items: pd.DataFrame) -> str:
    label_en, label_zh = SECTION_LABELS["pick_item"]
    st.markdown(f'<div class="ie-picker-hint">{label_en} · {label_zh}</div>', unsafe_allow_html=True)

    options = champ_items.sort_values("PLAYER_PURCHASE_RATE", ascending=False)["ITEM"].tolist()
    return st.selectbox("Item", options, label_visibility="collapsed")


def render_copurchase(row: pd.Series) -> None:
    """Visual co-purchase panel: anchor card + ranked chips for TOP_ITEM_1/2/3."""
    recs = [row.get(c) for c in ("TOP_ITEM_1", "TOP_ITEM_2", "TOP_ITEM_3")]
    recs = [str(r) for r in recs if isinstance(r, str) and r]

    anchor_name = html.escape(str(row["ITEM"]))

    if not recs:
        st.markdown(
            f"""
            <div class="ie-copurchase-row">
                <div class="ie-copurchase-anchor">
                    <div class="ie-cp-label">Selected</div>
                    <div class="ie-cp-name">{anchor_name}</div>
                </div>
                <div class="ie-copurchase-arrow">→</div>
                <div style="color:var(--ink-faint);font-size:13px;">
                    Not enough purchases with this item to surface a pairing yet.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    chips = "".join(
        f'<div class="ie-cp-chip"><span class="rank">{i+1}</span>{html.escape(r)}</div>'
        for i, r in enumerate(recs)
    )
    st.markdown(
        f"""
        <div class="ie-copurchase-row">
            <div class="ie-copurchase-anchor">
                <div class="ie-cp-label">Selected</div>
                <div class="ie-cp-name">{anchor_name}</div>
            </div>
            <div class="ie-copurchase-arrow">→</div>
            <div class="ie-copurchase-chips">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _bis_card_html(r: pd.Series, extra_classes: str = "") -> str:
    slot_class = "ie-bis-slot"
    if r["ITEM_CATEGORY"] == "Boots":
        slot_class += " boots"
    if extra_classes:
        slot_class += f" {extra_classes}"
    item_name = html.escape(str(r["ITEM"]))
    slot_label = html.escape(str(r["SLOT"]))
    return (
        f'<div class="{slot_class}">'
        f'<div class="ie-bis-slot-label">{slot_label}</div>'
        f'<div class="ie-bis-item">{item_name}</div>'
        f'<div class="ie-bis-stat"><span>win (adj)</span><b>{r["ADJ_WIN_RATE"]*100:.0f}%</b></div>'
        f'<div class="ie-bis-stat"><span>buy rate</span><b>{r["PLAYER_PURCHASE_RATE"]*100:.0f}%</b></div>'
        f'<div class="ie-bis-stat"><span>KDA</span><b>{r["AVG_KDA"]:.2f}</b></div>'
        f"</div>"
    )


def render_best_in_slot(champ_items: pd.DataFrame) -> None:
    """One horizontal strip: Starter, Trinket, Boots, Core x2, Flex x3. Core =
    top purchase rate ("must buy"); Flex = top BIS_SCORE among what's left.

    Cards are joined into ONE continuous HTML string (no newlines) — newline-
    heavy concatenation can push Streamlit's sanitizer into markdown mode and
    silently escape every card after the first.
    """
    scored = stats.add_bis_score(
        champ_items,
        w_win=settings.bis_w_win,
        w_kda=settings.bis_w_kda,
        w_pop=settings.bis_w_pop,
        w_conf=settings.bis_w_conf,
        conf_scale=settings.bis_conf_scale,
    )
    result = stats.build_recommendation(scored)
    early, build = result["early"], result["build"]

    if early.empty and build.empty:
        st.caption("Not enough items at this sample floor to assemble a build.")
        return

    core_items = set(build[build["SLOT"].str.startswith("Core")]["ITEM"]) if not build.empty else set()

    if not early.empty:
        early_cards = "".join(_bis_card_html(r, extra_classes="small") for _, r in early.iterrows())
        st.markdown(f'<div class="ie-early-strip">{early_cards}</div>', unsafe_allow_html=True)

    if not build.empty:
        build_cards = "".join(
            _bis_card_html(r, extra_classes="core" if r["ITEM"] in core_items else "")
            for _, r in build.iterrows()
        )
        st.markdown(f'<div class="ie-bis-strip">{build_cards}</div>', unsafe_allow_html=True)

    st.caption(
        "Starter, Trinket, Boots, and Core are just the most-purchased item in each slot. "
        "Flex is ranked by a blended score of adjusted win rate, KDA, purchase rate, and "
        "sample confidence, picked from whatever's left."
    )


def render_recommendations_tab(
    champ_items: pd.DataFrame,
    champ_items_unfiltered: pd.DataFrame,
) -> None:
    """`champ_items` (tier-filtered) drives the picker/co-purchase panel;
    `champ_items_unfiltered` drives the build so it doesn't lose slots to
    the tier filter."""
    if champ_items.empty:
        st.caption("No items match the current tier filter for this champion.")
        return

    render_section_header("recommendations")
    picked_item = _item_picker(champ_items)
    row = champ_items[champ_items["ITEM"] == picked_item].iloc[0]
    render_copurchase(row)

    render_section_header("bis")
    render_best_in_slot(champ_items_unfiltered)
