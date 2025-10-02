
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PP pyrolysis oil – grouped bar by standard carbon-number bins.

- X-axis: bins (C4–C5, C6–C10, C11–C15, C16–C20, C21–C40)
- Bars: papers, shown side-by-side within each bin
- Input: CSV with columns [Paper, ReportedRangesJSON]
    - ReportedRangesJSON example:
      [{"low":6,"high":11,"pct":50},{"low":12,"high":20,"pct":45},{"low":21,"high":40,"pct":5}]
    - All percentages for a paper should be on the SAME basis (e.g., liquid fraction area% or wt%).
- Output: PNG figure + CSV of harmonized table

Usage:
    python pp_bins_grouped_plot.py \
        --input pp_bins_input.csv \
        --out_png grouped_bins.png \
        --out_csv harmonized_bins.csv
"""

import json
import argparse
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- Standard bins ----------
BINS: List[Tuple[int, int, str]] = [
    (4, 5,  "C4–C5"),
    (6, 10, "C6–C10"),
    (11, 15,"C11–C15"),
    (16, 20,"C16–C20"),
    (21, 40,"C21–C40"),
]

def allocate_to_bins(reported_ranges: List[Dict[str, float]], bins=BINS) -> Dict[str, float]:
    """
    Distribute a list of reported ranges into the common bins by overlap-count proportion.
    reported_ranges: [{"low": int, "high": int, "pct": float}, ...]
    """
    out = {name: 0.0 for _, _, name in bins}
    max_high = max(h for _, h, _ in bins)
    for rr in reported_ranges:
        a = int(rr["low"]); b = int(rr["high"]); pct = float(rr["pct"])
        if b > max_high:
            b = max_high
        if a > b:
            continue
        width = (b - a + 1)
        if width <= 0:
            continue
        for (L, U, name) in bins:
            overlap_low = max(a, L); overlap_high = min(b, U)
            if overlap_low <= overlap_high:
                overlap_count = (overlap_high - overlap_low + 1)
                out[name] += pct * (overlap_count / width)
    # Gentle normalization to 100 if close
    total = sum(out.values())
    if 99.0 <= total <= 101.0 and total != 0:
        out = {k: v * (100.0/total) for k, v in out.items()}
    return out

def build_harmonized_table(df_in: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df_in.iterrows():
        paper = str(r["Paper"])
        ranges = json.loads(r["ReportedRangesJSON"])
        bucketed = allocate_to_bins(ranges, bins=BINS)
        row = {"Paper": paper}
        row.update(bucketed)
        rows.append(row)
    df = pd.DataFrame(rows).set_index("Paper")
    ordered = [name for _, _, name in BINS]
    return df[ordered].round(3)

def plot_grouped_bins(df_bins: pd.DataFrame, out_png: str):
    """
    df_bins: index=bins, columns=papers (values = %)
    """
    x_vals = np.arange(len(df_bins.index))
    k = len(df_bins.columns)
    group_width = 0.85
    bar_width = group_width / k

    plt.figure(figsize=(11, 5.5))
    for i, col in enumerate(df_bins.columns):
        offsets = x_vals - group_width/2 + i*bar_width + bar_width/2
        plt.bar(offsets, df_bins[col].values, width=bar_width, label=col)

    plt.xticks(x_vals, df_bins.index, rotation=0)
    plt.xlabel("Carbon-number bins")
    plt.ylabel("Share (%)")
    plt.title("PP Pyrolysis Oil – Grouped Bar by Standard Bins")
    plt.legend(loc="upper right", fontsize=8, ncol=2)
    plt.grid(True, axis="y", linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    print(f"Saved figure: {out_png}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input CSV with columns [Paper, ReportedRangesJSON]")
    ap.add_argument("--out_png", default="pp_bins_grouped.png", help="Output PNG path")
    ap.add_argument("--out_csv", default="pp_bins_harmonized.csv", help="Output harmonized CSV path")
    args = ap.parse_args()

    df_in = pd.read_csv(args.input)
    df_h = build_harmonized_table(df_in)
    df_h.to_csv(args.out_csv, index=True)
    print(f"Saved harmonized table: {args.out_csv}")

    # Transpose to x=bins, bars=papers
    df_bins = df_h.T
    plot_grouped_bins(df_bins, args.out_png)

if __name__ == "__main__":
    main()
