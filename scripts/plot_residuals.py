#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trace la convergence des residus (Ux, Uy, p, k, omega) a partir d'un ou
plusieurs logs OpenFOAM (simpleFoam/pimpleFoam), dans l'ordre chronologique
-- utile quand la simulation a ete relancee plusieurs fois (comme ici,
log.simpleFoam_upwind avec plusieurs "tee -a").

Usage :
    python3 plot_residuals.py log.simpleFoam_upwind [autres_logs...] --alpha 30
"""
import argparse
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FIELD_RE = re.compile(
    r"Solving for (\w+), Initial residual = ([\d.eE+-]+), Final residual = ([\d.eE+-]+)"
)
TIME_RE = re.compile(r"^Time = ([\d.eE+-]+)")


def parse_logs(paths):
    """Retourne un dict {field: (iterations[], initial_residuals[])},
    en associant chaque bloc 'Solving for' au dernier 'Time = ' rencontre."""
    data = {}
    current_time = 0
    for path in paths:
        with open(path, errors="ignore") as f:
            for line in f:
                m = TIME_RE.match(line)
                if m:
                    current_time = float(m.group(1))
                    continue
                m = FIELD_RE.search(line)
                if m:
                    field, init_res, _ = m.group(1), float(m.group(2)), m.group(3)
                    data.setdefault(field, ([], []))
                    data[field][0].append(current_time)
                    data[field][1].append(init_res)
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+", help="fichier(s) log, dans l'ordre chronologique")
    ap.add_argument("--out", default="figures/09_residus.png")
    args = ap.parse_args()

    data = parse_logs(args.logs)
    if not data:
        print("ERREUR : aucun residu trouve. Verifiez le(s) chemin(s) de log.")
        return

    import os
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 6))
    for field in ["Ux", "Uy", "p", "k", "omega"]:
        if field not in data:
            continue
        t, res = data[field]
        ax.semilogy(t, res, lw=0.8, label=field)

    ax.set_xlabel("iteration")
    ax.set_ylabel("residu initial (echelle log)")
    ax.set_title("Convergence des residus")
    ax.axhline(1e-4, color="grey", ls="--", lw=1, label="seuil p (1e-4)")
    ax.axhline(1e-5, color="grey", ls=":", lw=1, label="seuil U/k/omega (1e-5)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print("[OK]", args.out)


if __name__ == "__main__":
    main()
