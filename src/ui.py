"""UI — one render function per feature, pure presentation.

No business logic and no data access live here: every function takes a ready
DataFrame (already passed through `src/stats.py`) and draws it. This is what
keeps `streamlit_app.py` readable as plain orchestration. Mirrors the
`ui.py` convention shared with `pipeline_monitor` / `role_importance`,
including the bilingual EN/ZH header, section-header, and `st.tabs` pattern
(see role_importance's EDA / Model Evaluation / Lane Importance / Predictor
tabs for the same shape).

Tab layout:
    Item Builds     — the full stats table + gems/traps signal cards.
    Recommendations — pick one item, see what it's commonly built with
                       (visual chips, not a hidden checkbox) and the
                       champion's recommended build (one horizontal strip).
"""

from __future__ import annotations

import html
import textwrap

import pandas as pd
import streamlit as st

from settings import Settings
from src import stats, theme


def setup_page(settings: Settings) -> None:
    st.set_page_config(page_title=settings.ui.app_title, page_icon="⚜", layout="wide")
    theme.inject(st)


def render_header(settings: Settings) -> None:
    mode_label = "Local / Mock" if settings.is_local else "Snowflake (live)"
    mode_class = "ie-pill-neutral" if settings.is_local else "ie-pill-ok"
    st.markdown(
        textwrap.dedent(f"""
        <div class="ie-header">
            <div class="ie-title">{settings.ui.app_title}
                <span class="ie-pill {mode_class}">{mode_label}</span>
            </div>
            <div class="ie-subtitle-en">{settings.ui.app_subtitle_en}</div>
            <div class="ie-subtitle-zh">{settings.ui.app_subtitle_zh}</div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_section_header(section_key: str, settings: Settings) -> None:
    en, zh = settings.ui.section_labels[section_key]
    st.markdown(
        textwrap.dedent(f"""
        <div class="ie-section-header">
            <span class="ie-section-en">{en}</span>
            <span class="ie-section-zh">{zh}</span>
        </div>
        """),
        unsafe_allow_html=True,
    )


def sidebar_controls(overview: pd.DataFrame, settings: Settings) -> dict:
    """Champion picker, tier filter, and the method knobs. Returns selections.

    Shared across both tabs: whichever champion/tier/k/min_n is chosen here
    drives the Item Builds table, the signal cards, AND the Recommendations
    tab, so switching tabs never loses context.
    """
    m = settings.method
    with st.sidebar:
        st.markdown(f"### {settings.ui.app_title}")
        champion = st.selectbox("Champion", overview["CHAMPION"].tolist())

        tiers = st.multiselect(
            "Item tier",
            list(m.category_order),
            default=list(m.default_tiers),
        )

        method_en, method_zh = settings.ui.section_labels["method"]
        with st.expander(f"{method_en} · {method_zh}", expanded=False):
            min_n = st.slider(
                "Minimum sample (n)",
                m.min_n_min, m.min_n_max, m.default_min_n, step=m.min_n_step,
                help="Items below this purchase count are never flagged.",
            )
            k = st.slider(
                "Shrinkage strength (k)",
                m.k_min, m.k_max, int(m.default_k), step=m.k_step,
                help="Games of benefit-of-the-doubt given to the champion baseline. "
                     "Higher = noisy win rates pulled harder toward the champion mean.",
            )
        return {"champion": champion, "tiers": tiers, "min_n": min_n, "k": k}


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


# ===========================================================================
# TAB 1 — Item Builds (stats table + gem/trap signal cards)
# ===========================================================================
def render_item_table(df: pd.DataFrame) -> None:
    """Plain, sortable item table — a stats reference, not an interaction
    trigger. Item selection for recommendations now happens explicitly via
    the picker on the Recommendations tab, not by clicking a row here."""
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


def render_signals(df: pd.DataFrame, settings: Settings) -> None:
    gems = df[df["FLAG"] == "gem"].sort_values("ADJ_WIN_RATE", ascending=False).head(5)
    traps = df[df["FLAG"] == "trap"].sort_values("PLAYER_PURCHASE_RATE", ascending=False).head(5)

    gem_en, gem_zh = settings.ui.section_labels["gems"]
    trap_en, trap_zh = settings.ui.section_labels["traps"]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(_signal_card("gem", f"{gem_en} · {gem_zh}", gems), unsafe_allow_html=True)
    with c2:
        st.markdown(_signal_card("trap", f"{trap_en} · {trap_zh}", traps), unsafe_allow_html=True)


def render_item_builds_tab(champ_items: pd.DataFrame, settings: Settings) -> None:
    render_section_header("items", settings)
    render_item_table(champ_items)

    render_section_header("signals", settings)
    render_signals(champ_items, settings)


# ===========================================================================
# TAB 2 — Recommendations (item picker -> co-purchase chips + build strip)
# ===========================================================================
def _item_picker(champ_items: pd.DataFrame, settings: Settings) -> str:
    label_en, label_zh = settings.ui.section_labels["pick_item"]
    st.markdown(f'<div class="ie-picker-hint">{label_en} · {label_zh}</div>', unsafe_allow_html=True)

    options = champ_items.sort_values("PLAYER_PURCHASE_RATE", ascending=False)["ITEM"].tolist()
    return st.selectbox("Item", options, label_visibility="collapsed")


def render_copurchase(row: pd.Series) -> None:
    """Visual co-purchase panel: the picked item as an anchor card, with its
    TOP_ITEM_1/2/3 as ranked chips — no table, no hidden interaction."""
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


def render_best_in_slot(champ_items: pd.DataFrame, settings: Settings) -> None:
    """Recommendation build: one horizontal strip, 8 cards left to right —
    Starter, Trinket, Boots, Core x2, Flex x3 — with Starter/Trinket sized
    down (`.small` modifier) rather than pulled into a separate row, since
    two separate `st.markdown()` calls stack vertically by default (each is
    its own flex container / block element) even if both use `display:flex`
    internally. One call, one flex container, keeps everything on one line.

        Starter / Trinket / Boots / Core — top purchase rate: "everyone
                                            buys this regardless of matchup"
        Flex                             — top BIS_SCORE among whatever's
                                            left once Core is excluded: the
                                            formula's actual situational pick

    Presenting all 8 as equally "the best pick" would overstate how settled
    a build is, so Core keeps a neutral/ink card accent (popularity-driven)
    while Flex keeps the red "this is our ranking" accent — same visual
    distinction as before, just in one row instead of two.

    All cards are joined into ONE continuous HTML string (no newlines)
    rather than built with `+=` across a loop — see `render_copurchase` for
    why: newline-heavy concatenation can push Streamlit's HTML sanitizer
    into markdown-parsing mode partway through, silently escaping every
    card after the first instead of rendering it.
    """
    scored = stats.add_bis_score(
        champ_items,
        w_win=settings.method.bis_w_win,
        w_kda=settings.method.bis_w_kda,
        w_pop=settings.method.bis_w_pop,
        w_conf=settings.method.bis_w_conf,
        conf_scale=settings.method.bis_conf_scale,
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
        "Starter, Trinket, Boots, and Core are the champion's most-purchased picks in "
        "each slot. Flex is ranked by a blended score — adjusted win rate, KDA, purchase "
        "rate, and sample confidence — among what's left."
    )


def render_recommendations_tab(
    champ_items: pd.DataFrame,
    champ_items_unfiltered: pd.DataFrame,
    settings: Settings,
) -> None:
    """`champ_items` (tier-filtered, same set as the Item Builds tab) drives
    the item picker and co-purchase panel, so recommendations always match
    what's visible in the table. `champ_items_unfiltered` drives the build —
    it shouldn't silently lose slots just because the sidebar tier filter
    happens to be narrowed to Boots."""
    if champ_items.empty:
        st.caption("No items match the current tier filter for this champion.")
        return

    render_section_header("recommendations", settings)
    picked_item = _item_picker(champ_items, settings)
    row = champ_items[champ_items["ITEM"] == picked_item].iloc[0]
    render_copurchase(row)

    render_section_header("bis", settings)
    render_best_in_slot(champ_items_unfiltered, settings)


def render_health(info: dict) -> None:
    st.caption(
        f"Source: {info['mode']} · {info['item_rows']:,} item rows · "
        f"{info['champions']} champions"
    )