"""firmpanel - build and analyse a cross-country firm-level panel from Compustat Global and North America.

clean      : combine the two databases, apply sample filters, convert to USD, winsorise
ratios     : working-capital, leverage, profitability, liquidity, distress and trade-credit measures
aggregate  : country- and region-level summaries with a minimum cell size (safe to publish)
regress    : firm fixed-effects panel regressions with clustered standard errors
"""
from . import aggregate, clean, ratios, regress

__all__ = ["clean", "ratios", "aggregate", "regress"]
__version__ = "0.1.0"
