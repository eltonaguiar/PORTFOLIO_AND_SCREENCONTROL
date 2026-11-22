"""Cost model. Friction is a first-class citizen: it is applied before any verdict."""

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass(frozen=True)
class CostModel:
    """Round-turn cost expressed as fractions of notional.

    taker_fee  : per-side exchange fee. 0.0010 = 10 bps.
    slippage   : per-side adverse price movement on the fill.
    """

    taker_fee: float = 0.0010
    slippage: float = 0.0003

    @property
    def per_side(self) -> float:
        return self.taker_fee + self.slippage

    @property
    def round_turn(self) -> float:
        return 2.0 * self.per_side

    def as_dict(self) -> Dict[str, float]:
        d = asdict(self)
        d["per_side"] = self.per_side
        d["round_turn"] = self.round_turn
        return d


# Conservative retail default: Binance/Kraken spot taker ~10 bps + 3 bps slippage
# each way => 26 bps round turn. A strategy must clear this before it is interesting.
DEFAULT_COSTS = CostModel(taker_fee=0.0010, slippage=0.0003)

# Grid used to expose the *breakeven cost*: at what friction does the edge die?
COST_GRID = [
    CostModel(taker_fee=0.0, slippage=0.0),
    CostModel(taker_fee=0.0005, slippage=0.0000),
    CostModel(taker_fee=0.0005, slippage=0.0002),
    CostModel(taker_fee=0.0010, slippage=0.0003),
    CostModel(taker_fee=0.0015, slippage=0.0005),
]
