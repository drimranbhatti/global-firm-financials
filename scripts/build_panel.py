"""Build the private analysis panel from licensed Compustat extracts.

    python scripts/build_panel.py --global PATH/global_annual.parquet --na PATH/na_annual.parquet --out PATH/panel.parquet

Inputs are reduced extracts of comp.g_funda and comp.funda (see scripts/reduce_compustat.py). The output
contains firm identifiers and stays outside the repository. World Bank exchange rates and GDP per capita
(public) are downloaded and saved to data/.
"""
import argparse, json, pathlib, sys, urllib.request
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from firmpanel import aggregate, clean, ratios


def wb(indicator):
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&date=2000:2020&per_page=20000"
    rows = json.load(urllib.request.urlopen(url))[1]
    return pd.DataFrame([(r["countryiso3code"], int(r["date"]), r["value"]) for r in rows if r["countryiso3code"]], columns=["iso3", "year", "value"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--global", dest="g", required=True); ap.add_argument("--na", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    fx = wb("PA.NUS.FCRF").rename(columns={"value": "rate"}); fx.to_csv(ROOT / "data" / "worldbank_fx.csv", index=False)
    gdp = wb("NY.GDP.PCAP.KD").rename(columns={"value": "gdp_pc"}); gdp.to_csv(ROOT / "data" / "worldbank_gdp_per_capita.csv", index=False)
    raw = clean.combine(pd.read_parquet(a.g), pd.read_parquet(a.na))
    d = clean.sample(raw, clean.fx_table(fx))
    r = ratios.compute(d)
    r["zombie"] = ratios.zombie(d, r["interest_cover"])
    for c in r.columns.drop(["zombie", "size", "age"]):
        r[c] = clean.winsorize(r[c].replace([np.inf, -np.inf], np.nan), d["fyear"])
    oic = set(pd.read_csv(ROOT / "data" / "oic_members.csv")["iso3"])
    keep = ["gvkey", "fyear", "loc", "curcd", "source", "gsector", "at_usd", "sale_usd"]
    panel = pd.concat([d[keep], r], axis=1)
    # market values exist only in Compustat North America (price x shares outstanding, local currency)
    mv = d["prcc_f"] * d["csho"]
    panel["tobins_q"] = clean.winsorize(((d["at"] - d["ceq"] + mv) / d["at"]).replace([np.inf, -np.inf], np.nan), d["fyear"])
    panel["market_leverage"] = clean.winsorize(((d["dltt"].fillna(0) + d["dlc"].fillna(0)) / (d["dltt"].fillna(0) + d["dlc"].fillna(0) + mv)).replace([np.inf, -np.inf], np.nan), d["fyear"])
    panel["cash_flow"] = clean.winsorize(((d["ib"] + d["dp"]) / d["at"]).replace([np.inf, -np.inf], np.nan), d["fyear"])
    panel["altman_z_market"] = clean.winsorize((1.2 * (d["act"] - d["lct"]) / d["at"] + 1.4 * d["re"] / d["at"] + 3.3 * d["oiadp"] / d["at"]
                                                + 0.6 * mv / d["lt"].where(d["lt"] > 0) + 1.0 * d["sale"] / d["at"]).replace([np.inf, -np.inf], np.nan), d["fyear"])
    panel["region"] = aggregate.region(panel["loc"], oic)
    panel = panel.merge(gdp.rename(columns={"iso3": "loc", "year": "fyear"}), on=["loc", "fyear"], how="left")
    panel["fyear"] = panel["fyear"].astype(int)
    panel.to_parquet(a.out, index=False)
    print(panel.shape, panel["gvkey"].nunique(), "firms,", panel["loc"].nunique(), "countries; USD size missing:", round(panel["size"].isna().mean(), 3))
