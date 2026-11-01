#!/usr/bin/env python3
"""Concatenate shard CSVs into one results file (keeps a single header, never overwrites an existing output).
usage: merge_results.py OUT.csv IN1.csv IN2.csv ...
Optional --drop-profiles a,b removes those profiles from the INPUTS first (used when a profile was re-run after recalibration)."""
import argparse, os, sys
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("inputs", nargs="+"); ap.add_argument("--drop-profiles", default="")
a = ap.parse_args()
if os.path.exists(a.out):
    sys.exit(f"refusing to overwrite {a.out}; choose a new name")
df = pd.concat([pd.read_csv(f) for f in a.inputs], ignore_index=True)
if a.drop_profiles:
    df = df[~df.profile.isin(a.drop_profiles.split(","))]
df.to_csv(a.out, index=False)
print(f"wrote {a.out}: {len(df)} rows from {len(a.inputs)} files")
