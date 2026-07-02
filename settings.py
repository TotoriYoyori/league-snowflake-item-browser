import os

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SnowflakeSettings:
    database: str = "LEAGUE_RECORDS"
    warehouse: str = "COMPUTE_WH"
    schema: str = "GOLD"
    connection_ttl: int | None = None  # st.connection ttl, None = forever


@dataclass(frozen=True)
class CacheSettings:
    # TTLs in seconds, aligned to the gold tables' TARGET_LAG.
    # Item table lags ~7 days; overview ~1.
    item_stats_ttl: int = 6 * 60 * 60
    overview_ttl: int = 60 * 60


@dataclass(frozen=True)
class MethodSettings:
    """Knobs for the gems/traps shrinkage model, surfaced in the sidebar."""

    default_k: float = 20.0
    k_min: int = 0
    k_max: int = 100
    k_step: int = 5

    default_min_n: int = 20
    min_n_min: int = 0
    min_n_max: int = 100
    min_n_step: int = 5

    category_order: tuple = (
        "Starter",
        "Basic",
        "Boots",
        "Epic",
        "Legendary",
        "Consumable",
        "Trinket",
        "Legacy",
        "Other",
    )
    default_tiers: tuple = ("Boots", "Epic", "Legendary")

    # ----- Best-in-Slot composite score weights (must sum to 1.0) -----
    # Blends four signals, each percentile-ranked within the champion so
    # scale differences across champions/items don't distort the mix:
    #   win  = adjusted win rate (the shrinkage-corrected stat, not raw)
    #   kda  = average KDA — intentionally low weight; KDA on its own
    #          rewards passive/late farming as much as good itemization,
    #          so it's a minor tiebreaker rather than a driver here
    #   pop  = purchase rate — the heaviest term. What the wider playerbase
    #          already converges on is strong evidence of what's actually
    #          good, and this is what most directly fixes low-n items
    #          (e.g. a 3-purchase item with a lucky win rate) outranking
    #          items with hundreds of purchases behind them
    #   conf = confidence from sample size (saturating). Correlated with
    #          pop by construction (EFF_N = purchase_rate * games_played)
    #          but scored separately so low-n is penalized even relative
    #          to other items of similar purchase rate on lower-volume
    #          champions
    #
    # conf_scale=100 means confidence keeps discriminating out past n=100,
    # rather than maxing out by n=40-60 (this dataset's EFF_N spans
    # roughly 1-700, so a narrow scale stops mattering well before the
    # real high-sample items).
    bis_w_win: float = 0.30
    bis_w_kda: float = 0.05
    bis_w_pop: float = 0.35
    bis_w_conf: float = 0.30
    bis_conf_scale: float = 100.0  # EFF_N at which confidence reaches ~63%


@dataclass(frozen=True)
class UISettings:
    app_title: str = "Itemization Explorer"
    app_subtitle_en: str = "League of Legends Item Builds — Stats, Signals & Recommendations"
    app_subtitle_zh: str = "英雄联盟装备统计 — 数据洞察与推荐"
    tab_labels: tuple = (
        ("Item Builds", "装备统计"),
        ("Recommendations", "推荐装备"),
    )
    section_labels: dict = field(
        default_factory=lambda: {
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
    )


@dataclass(frozen=True)
class Settings:
    env: str
    is_local: bool
    snowflake: SnowflakeSettings
    cache: CacheSettings
    method: MethodSettings
    ui: UISettings
    sample_data_dir: str


def _running_in_snowflake() -> bool:
    """Reliable SiS detection: the session token only exists inside Snowflake."""
    return os.path.isfile("/snowflake/session/token")


def get_settings() -> Settings:
    forced_env = os.environ.get("APP_ENV", "").strip().lower()
    if forced_env in ("local", "production"):
        is_local = forced_env == "local"
    else:
        is_local = not _running_in_snowflake()

    return Settings(
        env="local" if is_local else "production",
        is_local=is_local,
        snowflake=SnowflakeSettings(),
        cache=CacheSettings(),
        method=MethodSettings(),
        ui=UISettings(),
        sample_data_dir=os.environ.get(
            "LOCAL_DATA_DIR",
            os.path.join(os.path.dirname(__file__), "assets", "sample_data"),
        ),
    )