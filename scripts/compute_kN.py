#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calcule kN = FN / (rho * b * V0^2) -- EXACTEMENT la definition de
Fage & Johansen (1927, §2, liste des symboles) et de Raciti Castelli
et al. (2012, eq. 1) -- a partir de Cd/Cl (convention standard
0.5*rho*V0^2*Aref d'OpenFOAM), puis moyenne sur la fin du calcul.

FN est la force NORMALE A LA PLAQUE (pas alignee sur l'ecoulement).
Avec l'ecoulement le long de +x (cas gmsh, plaque vraiment inclinee),
la direction normale a la corde est perp = (-sin(alpha), cos(alpha)).
F_N (convention standard, 0.5 rho V^2 Aref) = -Cd*sin(alpha) + Cl*cos(alpha)
kN = F_N_standard / 2   (Fage & Johansen n'ont PAS de facteur 1/2)

Usage :
    python3 compute_kN.py [chemin_du_cas] --alpha 30 [--fraction 0.5]
"""
import argparse
import glob
import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def find_coeff_files(case_dir):
    """Retourne TOUS les fichiers coefficient.dat, dans l'ordre chronologique
    des sous-dossiers postProcessing/forceCoeffs1/<time>/ -- chaque relance
    de simpleFoam (meme via startFrom latestTime) cree un nouveau sous-dossier,
    il faut les concatener pour avoir l'historique complet."""
    base = os.path.join(case_dir, "postProcessing", "forceCoeffs1")
    if not os.path.isdir(base):
        print(f"ERREUR : {base} introuvable.")
        sys.exit(1)
    subdirs = sorted(os.listdir(base), key=lambda s: float(s))
    files = []
    for d in subdirs:
        full = os.path.join(base, d)
        candidates = glob.glob(os.path.join(full, "*.dat"))
        for c in candidates:
            if "coefficient" in os.path.basename(c):
                files.append(c)
                break
        else:
            if candidates:
                files.append(candidates[0])
    if not files:
        print("ERREUR : aucun coefficient.dat trouve sous", base)
        sys.exit(1)
    return files


def parse_coeff_file(path):
    header, rows = None, []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if line.startswith("#"):
                header = line.lstrip("#").split()
                continue
            rows.append([float(x) for x in line.split()])
    return header, np.array(rows)


def parse_all(paths):
    """Concatene tous les fichiers, en ne gardant que les lignes dont le
    Time est strictement croissant (evite les doublons si deux segments
    se recouvrent d'une iteration)."""
    header = None
    all_rows = []
    last_t = -1e30
    for p in paths:
        h, data = parse_coeff_file(p)
        if header is None:
            header = h
        for row in data:
            if row[0] > last_t:
                all_rows.append(row)
                last_t = row[0]
    return header, np.array(all_rows)


def col(header, name):
    for i, h in enumerate(header):
        if h == name:
            return i
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", nargs="?", default=".")
    ap.add_argument("--alpha", type=float, required=True, help="angle d'incidence (deg)")
    ap.add_argument("--fraction", type=float, default=0.5)
    ap.add_argument("--kN-ref", type=float, default=None,
                     help="valeur de reference (Table I, Fage & Johansen) pour comparaison")
    args = ap.parse_args()

    paths = find_coeff_files(args.case_dir)
    print("Lecture de :", len(paths), "segment(s) :")
    for p in paths:
        print("  -", p)
    header, data = parse_all(paths)
    ci_cd, ci_cl = col(header, "Cd"), col(header, "Cl")

    t = data[:, 0]
    Cd = data[:, ci_cd]
    Cl = data[:, ci_cl]

    a = math.radians(args.alpha)
    FN_standard = Cd * math.sin(a) - Cl * math.cos(a)   # signe corrige (verifie le 16/08)
    kN = FN_standard / 2.0

    n = len(t)
    i0 = int(n * (1 - args.fraction))
    kN_win = kN[i0:]
    kN_mean, kN_std = kN_win.mean(), kN_win.std()

    print(f"\nFenetre : Time = {t[i0]:.0f} .. {t[-1]:.0f} ({len(kN_win)} points)")
    print(f"kN = {kN_mean:.4f} +/- {kN_std:.4f}  ({100*kN_std/abs(kN_mean):.1f}% rel.)")

    if args.kN_ref:
        err = 100 * (kN_mean - args.kN_ref) / args.kN_ref
        print(f"kN reference (Fage & Johansen) = {args.kN_ref}")
        print(f"Delta_kN = {err:+.2f} %   (formule Raciti Castelli eq. 3)")

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(t, kN, lw=0.8, color="tab:purple")
    ax.axvspan(t[i0], t[-1], color="tab:purple", alpha=0.15, label="fenetre de moyenne")
    ax.axhline(kN_mean, color="tab:red", ls="--", label=f"kN moyen = {kN_mean:.4f}")
    if args.kN_ref:
        ax.axhline(args.kN_ref, color="k", ls=":", label=f"kN reference = {args.kN_ref}")
    ax.set_xlabel("iteration")
    ax.set_ylabel("kN = FN / (rho b V0^2)")
    ax.set_title(f"kN au cours des iterations (alpha={args.alpha} deg)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    out_dir = os.path.join(args.case_dir, "figures")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "kN_convergence.png")
    fig.savefig(out, dpi=150)
    print("\nFigure enregistree :", out)


if __name__ == "__main__":
    main()
