"""Firm fixed-effects regressions with standard errors clustered by firm (linearmodels)."""
from __future__ import annotations

import pandas as pd
from linearmodels.panel import PanelOLS


def fe(df: pd.DataFrame, y: str, xs: list[str], time_effects: bool = True, min_obs: int = 200) -> pd.DataFrame | None:
    """Two-way (firm and year) fixed effects. Returns coefficient, s.e., t and p for each regressor, plus N and firms."""
    d = df[["gvkey", "fyear", y] + xs].dropna()
    if len(d) < min_obs or d["gvkey"].nunique() < 30:
        return None
    d = d.set_index(["gvkey", "fyear"])
    res = PanelOLS(d[y], d[xs], entity_effects=True, time_effects=time_effects, drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
    out = pd.DataFrame({"coef": res.params, "se": res.std_errors, "t": res.tstats, "p": res.pvalues})
    out.attrs.update(nobs=int(res.nobs), firms=int(d.index.get_level_values(0).nunique()), r2_within=float(res.rsquared_within))
    return out
