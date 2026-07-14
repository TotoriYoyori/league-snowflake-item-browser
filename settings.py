from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    # ----- Shrinkage strength (k): pulling a low-sample item's win rate toward its champion's baseline
    default_k: float = 20.0
    k_min: int = 0
    k_max: int = 100
    k_step: int = 5

    # ----- Minimum sample (n): purchases an item needs before it's eligible for a gem/trap flag
    default_min_n: int = 20
    min_n_min: int = 0
    min_n_max: int = 100
    min_n_step: int = 5

    category_order: tuple[str, ...] = (
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
    default_tiers: tuple[str, ...] = ("Boots", "Epic", "Legendary")

    # ----- Best-in-Slot composite score weights (must sum to 1.0) -----
    # score = 0.30(win) + (0.05)kda + (0.35)pop + (0.30)conf

    bis_w_win: float = 0.30
    bis_w_kda: float = 0.05
    bis_w_pop: float = 0.35
    bis_w_conf: float = 0.30
    bis_conf_scale: float = 100.0

    model_config = ConfigDict(frozen=True)

# --------------- SINGLETON ---------------
settings = Settings()
