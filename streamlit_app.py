import streamlit as st

from settings import get_settings
from src import data, stats, ui

settings = get_settings()
ui.setup_page(settings)
ui.render_header(settings)

# --- Load (cached; live warehouse in SiS, local CSV otherwise) ---
overview = data.load_overview(settings)
items_raw = data.load_item_stats(settings)

# --- Controls ---
controls = ui.sidebar_controls(overview, settings)

# --- Stats pipeline with current knobs ---
items = stats.prepare(
    items_raw,
    k=controls["k"],
    min_n=controls["min_n"],
)

# --- Slice to selection ---
champ = controls["champion"]
champ_items_unfiltered = items[items["CHAMPION"] == champ].sort_values(
    "PLAYER_PURCHASE_RATE", ascending=False
)

champ_items = champ_items_unfiltered
if controls["tiers"]:
    champ_items = champ_items[champ_items["ITEM_CATEGORY"].isin(controls["tiers"])]

meta = overview[overview["CHAMPION"] == champ].iloc[0]

# --- Render ---
ui.render_hero(meta)

tab_builds, tab_recs = st.tabs(
    [f"{en} · {zh}" for en, zh in settings.ui.tab_labels]
)

with tab_builds:
    ui.render_item_builds_tab(champ_items, settings)

with tab_recs:
    ui.render_recommendations_tab(champ_items, champ_items_unfiltered, settings)

ui.render_health(data.data_health(settings, items_raw, overview))
