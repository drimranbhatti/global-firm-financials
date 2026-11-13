"""Group summaries that are safe to publish: no firm identifiers, and cells with fewer than `min_firms` firms are dropped."""
from __future__ import annotations

import pandas as pd

MIN_FIRMS = 20


def summary(df: pd.DataFrame, by, cols, stat: str = "median", min_firms: int = MIN_FIRMS) -> pd.DataFrame:
    by = [by] if isinstance(by, str) else list(by)
    g = df.groupby(by)
    out = g[cols].agg(stat)
    out["firms"] = g["gvkey"].nunique()
    out["firm_years"] = g.size()
    return out[out["firms"] >= min_firms]


REGIONS = {
    "North America": {"USA", "CAN"},
    "Western Europe": {"GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "CHE", "AUT", "SWE", "NOR", "DNK", "FIN", "IRL", "PRT", "GRC", "LUX", "ISL"},
    "Japan": {"JPN"}, "China": {"CHN"}, "India": {"IND"},
    "Other developed Asia-Pacific": {"AUS", "NZL", "KOR", "TWN", "HKG", "SGP", "ISR"},
}


def region(loc: pd.Series, oic: set[str]) -> pd.Series:
    r = pd.Series("Other emerging", index=loc.index)
    r[loc.isin(oic)] = "OIC members"
    for name, codes in REGIONS.items():
        r[loc.isin(codes)] = name
    return r
