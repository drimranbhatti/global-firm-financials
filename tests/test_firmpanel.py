import numpy as np
import pandas as pd
import pytest

from firmpanel import aggregate, clean, ratios, regress

rng = np.random.default_rng(0)


def toy(n_firms=60, years=range(2005, 2015)):
    rows = []
    for f in range(n_firms):
        for y in years:
            at = rng.uniform(50, 500); sale = at * rng.uniform(0.5, 1.5); cogs = 0.7 * sale
            rows.append(dict(gvkey=f"{f:06d}", fyear=y, datadate=y * 10000 + 1231, loc="USA" if f % 2 else "PAK", curcd="USD",
                             gsector=20, at=at, sale=sale, cogs=cogs, rect=sale * 0.2, invt=cogs * 0.1, ap=cogs * 0.15,
                             act=at * 0.4, lct=at * 0.3, che=at * 0.1, oiadp=at * 0.08, dltt=at * 0.2, dlc=at * 0.05,
                             lt=at * 0.5, ppent=at * 0.3, intan=0, re=at * 0.2, capx=at * 0.05, dvt=1, ib=5, xint=2, xrd=0))
    return pd.DataFrame(rows)


def test_combine_prefers_north_america_for_us_firms():
    g = toy(2, [2010]).assign(sale=1.0); n = toy(2, [2010]).assign(sale=2.0)
    c = clean.combine(g, n)
    assert len(c) == 2
    assert c.set_index("loc").loc["USA", "sale"] == 2.0 and c.set_index("loc").loc["PAK", "sale"] == 1.0


def test_ratios_known_values():
    d = clean.sample(toy(4, [2010, 2011]), clean.fx_table(pd.DataFrame(columns=["iso3", "year", "rate"])))
    r = ratios.compute(d)
    assert r["dso"].iloc[0] == pytest.approx(365 * 0.2)
    assert r["dio"].iloc[0] == pytest.approx(36.5) and r["dpo"].iloc[0] == pytest.approx(365 * 0.15)
    assert r["ccc"].iloc[0] == pytest.approx(365 * 0.2 + 36.5 - 365 * 0.15)
    assert r["leverage"].iloc[0] == pytest.approx(0.25)


def test_aggregate_drops_small_cells():
    d = toy(30, [2010]); d.loc[:2, "loc"] = "XXX"
    s = aggregate.summary(d.assign(v=1.0), "loc", ["v"], min_firms=5)
    assert "XXX" not in s.index and set(s.index) == {"USA", "PAK"}


def test_fe_recovers_planted_slope():
    d = toy(80); x = rng.normal(size=len(d)); fe_ = d["gvkey"].map({k: rng.normal() for k in d.gvkey.unique()})
    d["x"] = x + fe_; d["y"] = 0.5 * x + 2 * fe_ + rng.normal(0, 0.1, len(d))
    out = regress.fe(d, "y", ["x"])
    assert out.loc["x", "coef"] == pytest.approx(0.5, abs=0.02)


def test_zombie_needs_three_consecutive_years():
    d = pd.DataFrame({"gvkey": ["a"] * 4, "fyear": [2000, 2001, 2002, 2003]})
    z = ratios.zombie(d, pd.Series([0.5, 0.5, 0.5, 2.0]))
    assert z.tolist() == [False, False, True, False]
