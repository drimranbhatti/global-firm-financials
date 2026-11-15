"""Percentile tables for the peer-benchmark page (docs/index.html).

    python scripts/build_benchmark.py [--panel private/panel.parquet]

Pools fiscal 2017-2019. A cell (market x industry) is published only with at least 30 firms and 60 firm-years,
and only the 10th-90th percentiles are kept, so no published number describes a single company.
"""
import argparse, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
IG = {"1010": "Energy", "1510": "Materials", "2010": "Capital goods", "2020": "Commercial & professional services", "2030": "Transportation",
      "2510": "Autos & components", "2520": "Consumer durables & apparel", "2530": "Consumer services", "2540": "Media & entertainment",
      "2550": "Retail", "3010": "Food & staples retail", "3020": "Food, beverage & tobacco", "3030": "Household & personal products",
      "3510": "Health care equipment & services", "3520": "Pharma & biotech", "4510": "Software & IT services", "4520": "Technology hardware",
      "4530": "Semiconductors", "5010": "Telecom services", "5020": "Media & entertainment", "6010": "Real estate"}
EU27 = {"AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
        "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"}
METRICS = {"dso": "Receivable days (DSO)", "dio": "Inventory days (DIO)", "dpo": "Payable days (DPO)", "ccc": "Cash conversion cycle",
           "gross_margin": "Gross margin", "roa": "Operating return on assets", "leverage": "Debt / assets", "cash": "Cash / assets",
           "current_ratio": "Current ratio", "interest_cover": "Interest cover (EBIT / interest)", "sales_growth": "Sales growth"}
PCTS = [10, 20, 30, 40, 50, 60, 70, 80, 90]
MIN_FIRMS, MIN_OBS = 30, 60

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--panel", default=str(ROOT / "private" / "panel.parquet")); a = ap.parse_args()
    p = pd.read_parquet(a.panel); p = p[p.fyear.between(2017, 2019)].copy()
    p["industry"] = p.industry_group.map(IG)
    names = pd.read_csv(ROOT / "data" / "coverage_by_country.csv", index_col=0)
    big = names[names.firms >= 150].index.tolist()
    markets = {"All countries": p.index, "European Union (27)": p.index[p["loc"].isin(EU27)]}
    for r in sorted(p.region.unique()): markets[r] = p.index[p.region.eq(r)]
    for c in big: markets[c] = p.index[p["loc"].eq(c)]
    out = {}
    for mname, idx in markets.items():
        d = p.loc[idx]
        for ind, g in [("All industries", d)] + list(d.groupby("industry")):
            if g.gvkey.nunique() < MIN_FIRMS: continue
            cell = {}
            for m in METRICS:
                v = g[m].dropna()
                if len(v) >= MIN_OBS and g.loc[v.index, "gvkey"].nunique() >= MIN_FIRMS:
                    cell[m] = [round(float(x), 4) for x in np.percentile(v, PCTS)]
            if cell: out.setdefault(mname, {})[ind] = {"firms": int(g.gvkey.nunique()), "q": cell}
    meta = {"percentiles": PCTS, "metrics": METRICS, "years": "2017-2019", "min_firms": MIN_FIRMS,
            "pct_metrics": ["gross_margin", "roa", "leverage", "cash", "sales_growth"]}
    json.dump({"meta": meta, "data": out}, open(ROOT / "data" / "benchmark_percentiles.json", "w"), separators=(",", ":"))
    print(len(out), "markets;", sum(len(v) for v in out.values()), "market-industry cells")
