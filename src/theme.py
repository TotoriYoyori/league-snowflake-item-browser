"""Custom CSS injected once at app start. Light mode, fixed palette.

Shares the visual system with `pipeline_monitor` / `role_importance`: dark-red
accent, Noto Sans SC in the font stack (browser/OS CJK fallback — not
`@import`ed, same as the other two apps), card-style containers, and pill
badges for status/signal semantics. Gem/trap flags use the shared
pill-ok (green) / pill-fail (red) colors rather than a separate jade/vermilion
palette, so all three apps read as one family.
"""

from __future__ import annotations

CSS = """
<style>
:root {
    --red: #cc1f1f;
    --dark-red: #a81818;
    --amber: #e08a1e;
    --green: #2f9e63;
    --page-bg: #f1f1f1;
    --card-bg: #ffffff;
    --card-border: #e6e6e6;
    --subtle-border: #f1f1f1;
    --thead-bg: #fafafa;
    --ink: #1a1a1a;
    --ink-soft: #888888;
    --ink-faint: #aaaaaa;
    --font-main: "Noto Sans SC", system-ui, sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--font-main);
    color: var(--ink);
}

.stApp {
    background-color: var(--page-bg);
}

[data-testid="stHeader"] {
    background-color: transparent;
}

/* ---------- App header ---------- */
.ie-header {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-bottom: 1.25rem;
}
.ie-header .ie-title {
    font-size: 4rem;
    font-weight: 700;
    color: var(--dark-red);
}
.ie-header .ie-subtitle-en {
    font-size: 1.5rem;
    color: var(--ink-soft);
}
.ie-header .ie-subtitle-zh {
    font-size: 1rem;
    color: var(--ink-faint);
}

/* ---------- Section header ---------- */
.ie-section-header {
    display: flex;
    align-items: baseline;
    gap: 0.6rem;
    margin: 1.6rem 0 0.6rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid var(--card-border);
}
.ie-section-header .ie-section-en {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--ink);
}
.ie-section-header .ie-section-zh {
    font-size: 0.85rem;
    color: var(--ink-faint);
}

/* ---------- Hero (champion) card ---------- */
.ie-hero {
    border: 1px solid var(--card-border);
    border-top: 3px solid var(--dark-red);
    background: var(--card-bg);
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 8px;
}
.ie-hero .ie-hero-name {
    font-size: 34px;
    font-weight: 700;
    color: var(--ink);
    margin: 0;
}
.ie-hero .ie-hero-lane {
    color: var(--ink-soft);
    font-size: 14px;
    margin: 2px 0 12px;
}
.ie-pills {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.ie-pill-stat {
    background: var(--page-bg);
    border: 1px solid var(--card-border);
    border-radius: 999px;
    padding: 5px 13px;
    font-size: 13px;
    color: var(--ink-soft);
}
.ie-pill-stat b {
    color: var(--ink);
    font-weight: 600;
}

/* ---------- Status / signal pill ---------- */
.ie-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 999px;
    white-space: nowrap;
}
.ie-pill-ok { background-color: rgba(47, 158, 99, 0.12); color: var(--green); }
.ie-pill-warn { background-color: rgba(224, 138, 30, 0.14); color: var(--amber); }
.ie-pill-fail { background-color: rgba(204, 31, 31, 0.12); color: var(--red); }
.ie-pill-neutral { background-color: var(--thead-bg); color: var(--ink-soft); }

/* ---------- Gem / trap signal cards ---------- */
.ie-card {
    border: 1px solid var(--card-border);
    border-radius: 10px;
    background: var(--card-bg);
    padding: 12px 14px;
    height: 100%;
}
.ie-card.gem { border-top: 3px solid var(--green); }
.ie-card.trap { border-top: 3px solid var(--red); }
.ie-card .ie-card-hd {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 8px;
}
.ie-card.gem .ie-card-hd { color: var(--green); }
.ie-card.trap .ie-card-hd { color: var(--dark-red); }
.ie-row {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    padding: 3px 0;
}
.ie-row .v { color: var(--ink-soft); }

/* ---------- Recommendation tags ---------- */
.ie-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 4px;
}
.ie-tag {
    background: var(--page-bg);
    border: 1px solid var(--card-border);
    color: var(--dark-red);
    border-radius: 8px;
    padding: 5px 11px;
    font-size: 13px;
}

/* ---------- Streamlit tabs ---------- */
[data-testid="stTabs"] button[role="tab"] {
    font-size: 1rem;
    font-weight: 600;
    color: var(--ink-soft);
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--dark-red);
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: var(--dark-red);
}

/* ---------- Item picker card (Recommendations tab) ---------- */
.ie-picker-hint {
    color: var(--ink-soft);
    font-size: 13px;
    margin-bottom: 6px;
}

/* ---------- Co-purchase visual cards ---------- */
.ie-copurchase-row {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 10px 0 18px;
    flex-wrap: wrap;
}
.ie-copurchase-anchor {
    border: 1px solid var(--card-border);
    border-top: 3px solid var(--dark-red);
    background: var(--card-bg);
    border-radius: 10px;
    padding: 14px 18px;
    min-width: 180px;
}
.ie-copurchase-anchor .ie-cp-label {
    font-size: 11px;
    color: var(--ink-faint);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.ie-copurchase-anchor .ie-cp-name {
    font-size: 18px;
    font-weight: 700;
    color: var(--ink);
    margin-top: 2px;
}
.ie-copurchase-arrow {
    font-size: 22px;
    color: var(--ink-faint);
}
.ie-copurchase-chips {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}
.ie-cp-chip {
    border: 1px solid var(--card-border);
    background: var(--card-bg);
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 600;
    color: var(--ink);
    position: relative;
}
.ie-cp-chip .rank {
    position: absolute;
    top: -8px;
    left: -8px;
    background: var(--dark-red);
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    border-radius: 999px;
    width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* ---------- Recommendation build strip ---------- */
/* One horizontal row: Starter, Trinket, Boots, Core x2, Flex x3.
   Starter/Trinket use the .small modifier below rather than a separate
   container, so everything stays on one line. */
.ie-build-group-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--ink-faint);
    margin: 14px 0 6px;
}

/* ---------- Best-in-Slot build strip ---------- */
.ie-bis-strip {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    flex-wrap: wrap;
    margin: 10px 0 6px;
}

.ie-bis-slot {
    border: 1px solid var(--card-border);
    border-top: 3px solid var(--dark-red);
    background: var(--card-bg);
    border-radius: 10px;
    padding: 12px 14px;
    flex: 1 1 140px;
    position: relative;
}
.ie-bis-slot.boots { border-top-color: var(--ink-soft); }
/* Core = "must buy" by purchase rate, not the formula — a neutral/ink
   accent instead of red keeps it visually distinct from Flex, which IS the
   formula's pick and keeps the red "this is our ranking" accent. */
.ie-bis-slot.core { border-top-color: var(--amber); }
.ie-bis-slot .ie-bis-slot-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--dark-red);
}
.ie-bis-slot.boots .ie-bis-slot-label { color: var(--ink-soft); }
.ie-bis-slot.core .ie-bis-slot-label { color: var(--amber); }
.ie-bis-slot .ie-bis-item {
    font-size: 14px;
    font-weight: 700;
    color: var(--ink);
    margin: 4px 0 8px;
    line-height: 1.25;
    min-height: 36px;
}
.ie-bis-slot .ie-bis-stat {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--ink-soft);
    padding: 1px 0;
}
.ie-bis-slot .ie-bis-stat b { color: var(--ink); }

/* Starter / Trinket sit in their own row above the main build strip —
   same card base, sized down via the .small modifier. */
.ie-early-strip {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    flex-wrap: wrap;
    margin: 10px 0 8px;
}

/* Starter / Trinket use this modifier on the same .ie-bis-slot base —
   narrower, shorter, muted border/label, and the win/buy/KDA stat rows
   are hidden since those two categories aren't meaningfully ranked (top
   purchase rate only, no BIS_SCORE comparison), just named. */
.ie-bis-slot.small {
    flex: 0 0 100px;
    width: 100px;
    height: 64px;
    padding: 6px 8px;
    border-top-width: 2px;
    border-top-color: var(--ink-faint);
}
.ie-bis-slot.small .ie-bis-slot-label { color: var(--ink-faint); font-size: 8px; }

.ie-bis-slot.small .ie-bis-item {
    font-size: 11px;
    font-weight: 600;
    color: var(--ink-soft);
    margin: 2px 0 0;
    min-height: 0;
    line-height: 1.2;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.ie-bis-slot.small .ie-bis-stat { display: none; }

.ie-bis-connector {
    display: flex;
    align-items: center;
    color: var(--ink-faint);
    font-size: 18px;
}

/* ---------- Dataframe tweaks ---------- */
[data-testid="stDataFrame"] {
    border: 1px solid var(--subtle-border);
    border-radius: 8px;
    overflow: hidden;
    background-color: var(--page-bg);
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background-color: var(--dark-red);
    border-right: 1px solid var(--card-border);
    color: var(--card-bg);
}

[data-testid="stSidebar"] p {
    color: var(--card-bg);
}

hr { border-color: var(--card-border); }
</style>
"""


def inject(st_module) -> None:
    st_module.markdown(CSS, unsafe_allow_html=True)
