"""Firm-level financial ratios. All are currency-free except where noted."""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute(d: pd.DataFrame) -> pd.DataFrame:
    """Add ratio columns to a cleaned sample (one row per firm-year)."""
    d = d.sort_values(["gvkey", "fyear"]).copy()
    cogs = d["cogs"].where(d["cogs"] > 0)
    out = pd.DataFrame(index=d.index)
    out["dso"] = 365 * d["rect"] / d["sale"]                              # receivable days
    out["dio"] = 365 * d["invt"] / cogs                                   # inventory days
    out["dpo"] = 365 * d["ap"] / cogs                                     # payable days
    out["ccc"] = out["dso"] + out["dio"] - out["dpo"]                     # cash conversion cycle
    out["trade_credit"] = d["rect"] / d["sale"]                           # receivables / sales (PhD design)
    out["roa"] = d["oiadp"] / d["at"]                                     # operating return on assets
    out["gross_margin"] = (d["sale"] - d["cogs"]) / d["sale"]
    debt = d["dltt"].fillna(0) + d["dlc"].fillna(0)
    out["leverage"] = debt / d["at"]                                      # book leverage
    out["tangibility"] = d["ppent"] / d["at"]
    out["cash"] = d["che"] / d["at"]
    out["intangibles"] = d["intan"].fillna(0) / d["at"]
    out["current_ratio"] = d["act"] / d["lct"].where(d["lct"] > 0)
    out["capex"] = d["capx"] / d["at"]
    out["rd"] = d["xrd"].fillna(0) / d["sale"]
    out["payout"] = d["dvt"] / d["ib"].where(d["ib"] > 0)
    out["interest_cover"] = d["oiadp"] / d["xint"].where(d["xint"] > 0)
    out["size"] = np.log(d["at_usd"])                                     # ln total assets, USD millions
    out["sales_growth"] = d.groupby("gvkey")["sale"].pct_change(fill_method=None).where(d.groupby("gvkey")["fyear"].diff() == 1)
    out["age"] = np.log1p(d["fyear"] - d.groupby("gvkey")["fyear"].transform("min")).astype(float)
    # Altman Z'' (1995) for non-manufacturers and emerging markets: needs no market data
    wc = d["act"] - d["lct"]; tl = d["lt"].where(d["lt"] > 0)
    out["z_score"] = 6.56 * wc / d["at"] + 3.26 * d["re"] / d["at"] + 6.72 * d["oiadp"] / d["at"] + 1.05 * (d["at"] - d["lt"]) / tl
    return out


DAYS = ["dso", "dio", "dpo", "ccc"]


def zombie(d: pd.DataFrame, cover: pd.Series, years: int = 3) -> pd.Series:
    """A firm-year is a 'zombie' if interest coverage has been below 1 for `years` consecutive years (and the firm has debt)."""
    low = (cover < 1).astype(float).where(cover.notna())
    g = low.groupby(d["gvkey"])
    run = g.transform(lambda x: x.rolling(years, min_periods=years).sum())
    consecutive = d.groupby("gvkey")["fyear"].diff(years - 1) == years - 1
    return (run == years) & consecutive
