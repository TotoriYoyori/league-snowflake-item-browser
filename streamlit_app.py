import streamlit as st

from settings import settings
from src import data, stats, ui

ui.setup_page()
ui.render_header()

overview = data.load_overview()
items_raw = data.load_item_stats()

with st.sidebar:
    st.markdown(f"### {ui.APP_TITLE}")
    champion = st.selectbox("Champion", overview["CHAMPION"].tolist())

    tiers = st.multiselect(
        "Item tier",
        list(settings.category_order),
        default=list(settings.default_tiers),
    )

    method_en, method_zh = ui.SECTION_LABELS["method"]
    with st.expander(f"{method_en} · {method_zh}", expanded=False):
        min_n = st.slider(
            "Minimum sample (n)",
            settings.min_n_min, settings.min_n_max, settings.default_min_n, step=settings.min_n_step,
            help="Items below this purchase count are never flagged.",
        )
        k = st.slider(
            "Shrinkage strength (k)",
            settings.k_min, settings.k_max, int(settings.default_k), step=settings.k_step,
            help="Games of benefit-of-the-doubt given to the champion baseline. "
                 "Higher = noisy win rates pulled harder toward the champion mean.",
        )

items = stats.prepare(items_raw, k=k, min_n=min_n)

champ_items_unfiltered = items[items["CHAMPION"] == champion].sort_values(
    "PLAYER_PURCHASE_RATE", ascending=False
)

champ_items = champ_items_unfiltered
if tiers:
    champ_items = champ_items[champ_items["ITEM_CATEGORY"].isin(tiers)]

meta = overview[overview["CHAMPION"] == champion].iloc[0]

ui.render_hero(meta)

tab_builds, tab_recs = st.tabs(
    [f"{en} · {zh}" for en, zh in ui.TAB_LABELS]
)

with tab_builds:
    ui.render_item_builds_tab(champ_items)

with tab_recs:
    ui.render_recommendations_tab(champ_items, champ_items_unfiltered)

ui.render_health(data.data_health(items_raw, overview))
