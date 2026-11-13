"""Reduce Compustat Global and North America annual CSV exports to compact parquet extracts.

    python scripts/reduce_compustat.py GLOBAL_ANNUAL.csv NORTH_AMERICA_ANNUAL.zip OUT_DIR

The output contains licensed data: keep it outside the repository and never commit it.
"""
import pathlib, sys, time, zipfile
import pandas as pd

ID = ["gvkey", "fyear", "datadate", "indfmt", "consol", "popsrc", "datafmt", "curcd", "loc", "fic", "conm", "gsector", "gind",
      "sic", "exchg", "ipodate", "costat"]
FIN = ["at", "sale", "revt", "cogs", "rect", "invt", "ap", "act", "lct", "che", "oiadp", "oibdp", "ebit", "ebitda", "ib", "dltt",
       "dlc", "lt", "ceq", "seq", "ppent", "intan", "re", "capx", "dvt", "xrd", "xint", "emp", "oancf", "txt", "xsga", "dp", "prcc_f", "csho"]


def reduce(open_stream, out, fmt, pop):
    t = time.time(); head = pd.read_csv(open_stream(), nrows=0).columns
    use = [c for c in ID + FIN if c in head]
    parts = [ch[(ch.indfmt == "INDL") & (ch.consol == "C") & (ch.datafmt == fmt) & (ch.popsrc == pop)]
             for ch in pd.read_csv(open_stream(), usecols=use, chunksize=200_000, low_memory=False,
                                   dtype={"gvkey": str, "sic": str, "gind": str, "gsector": str})]
    df = pd.concat(parts, ignore_index=True); df.to_parquet(out, index=False)
    print(out, df.shape, round(time.time() - t), "s")


if __name__ == "__main__":
    g, z, o = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]); o.mkdir(parents=True, exist_ok=True)
    reduce(lambda: open(g, "rb"), o / "global_annual.parquet", "HIST_STD", "I")          # comp.g_funda
    def na():
        zf = zipfile.ZipFile(z); return zf.open(zf.namelist()[0])
    reduce(na, o / "na_annual.parquet", "STD", "D")                                       # comp.funda
