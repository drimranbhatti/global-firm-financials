"""Sample construction.

Compustat Global (`comp.g_funda`) and Compustat North America (`comp.funda`) are combined. Rows are
restricted to industrial-format, consolidated, standardised statements. A firm-year present in both
databases is kept once: from North America when the firm is located in the USA or Canada, otherwise
from Global. Licensed data: nothing produced by this module may be redistributed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NA_LOC = {"USA", "CAN"}

# a country whose World Bank official rate represents each reporting currency
CURRENCY_COUNTRY = {"EUR": "DEU", "USD": None, "GBP": "GBR", "JPY": "JPN", "CNY": "CHN", "INR": "IND", "AUD": "AUS",
                    "TWD": None, "KRW": "KOR", "HKD": "HKG", "MYR": "MYS", "SGD": "SGP", "THB": "THA", "SEK": "SWE",
                    "PLN": "POL", "CHF": "CHE", "NOK": "NOR", "DKK": "DNK", "CAD": "CAN", "IDR": "IDN", "PKR": "PAK",
                    "ZAR": "ZAF", "TRY": "TUR", "BRL": "BRA", "MXN": "MEX", "ILS": "ISR", "PHP": "PHL", "VND": "VNM",
                    "SAR": "SAU", "AED": "ARE", "EGP": "EGY", "NZD": "NZL", "RUB": "RUS", "CLP": "CHL", "ARS": "ARG",
                    "BDT": "BGD", "LKR": "LKA", "NGN": "NGA", "KES": "KEN", "KWD": "KWT", "QAR": "QAT", "OMR": "OMN",
                    "BHD": "BHR", "JOD": "JOR", "MAD": "MAR", "TND": "TUN", "PEN": "PER", "COP": "COL", "HUF": "HUN",
                    "CZK": "CZE", "RON": "ROU", "BGN": "BGR", "HRK": "HRV", "ISK": "ISL", "KZT": "KAZ", "UAH": "UKR"}
# New Taiwan dollar per USD (annual average, central bank of Taiwan); not in the World Bank series
TWD_PER_USD = {2000: 31.2, 2001: 33.8, 2002: 34.6, 2003: 34.4, 2004: 33.4, 2005: 32.2, 2006: 32.5, 2007: 32.8, 2008: 31.5,
               2009: 33.0, 2010: 31.6, 2011: 29.5, 2012: 29.6, 2013: 29.8, 2014: 30.4, 2015: 31.9, 2016: 32.3, 2017: 30.4,
               2018: 30.2, 2019: 30.9, 2020: 29.5}


def combine(glob: pd.DataFrame, na: pd.DataFrame) -> pd.DataFrame:
    glob = glob.assign(source="Global"); na = na.assign(source="North America")
    df = pd.concat([na, glob], ignore_index=True, sort=False)
    df["fyear"] = df["fyear"].astype("Int64")
    df["prefer"] = np.where(df["loc"].isin(NA_LOC), df["source"].eq("North America"), df["source"].eq("Global")).astype(int)
    df = df.sort_values(["gvkey", "fyear", "prefer", "datadate"]).drop_duplicates(["gvkey", "fyear"], keep="last")
    return df.drop(columns="prefer").reset_index(drop=True)


def fx_table(wb_rates: pd.DataFrame) -> pd.DataFrame:
    """Local currency per USD by (currency, year) from World Bank PA.NUS.FCRF rows (iso3, year, rate)."""
    rows = []
    for cur, iso in CURRENCY_COUNTRY.items():
        for y in range(2000, 2021):
            if cur == "USD": rate = 1.0
            elif cur == "TWD": rate = TWD_PER_USD[y]
            else:
                m = wb_rates[(wb_rates.iso3 == iso) & (wb_rates.year == y)]["rate"]
                rate = float(m.iloc[0]) if len(m) and pd.notna(m.iloc[0]) else np.nan
            rows.append((cur, y, rate))
    return pd.DataFrame(rows, columns=["curcd", "fyear", "lcu_per_usd"])


def sample(df: pd.DataFrame, fx: pd.DataFrame, exclude_financials: bool = True) -> pd.DataFrame:
    """Apply filters and add total assets and sales in USD millions. Returns the analysis sample."""
    d = df[(df["at"] > 0) & (df["sale"] > 0) & df["loc"].notna()].copy()
    d["gsector"] = pd.to_numeric(d["gsector"], errors="coerce")
    if exclude_financials:
        d = d[~d["gsector"].isin([40, 55])]                       # banks/insurers and utilities: different balance sheets
    d = d.merge(fx, on=["curcd", "fyear"], how="left")
    d["at_usd"] = d["at"] / d["lcu_per_usd"]; d["sale_usd"] = d["sale"] / d["lcu_per_usd"]
    return d


def winsorize(s: pd.Series, by: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Clip a ratio at its 1st and 99th percentiles within each group (default: fiscal year)."""
    lo = s.groupby(by).transform(lambda x: x.quantile(lower)); hi = s.groupby(by).transform(lambda x: x.quantile(upper))
    return s.clip(lo, hi)
