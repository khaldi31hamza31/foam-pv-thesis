#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trace des GRAPHES (courbes) de U et p le long de lignes d'echantillonnage,
comparables aux Fig. 10-11 de Raciti Castelli et al. (profil de vitesse
V/V0 dans le sillage) et a la Fig. 4 de Fage & Johansen (coefficient de
pression Cp le long de la plaque).

Prealable obligatoire, depuis le dossier du cas :
    foamToVTK -latestTime

Usage :
    python3 plot_profiles.py [chemin_du_cas] --alpha 30

Necessite : pyvista, numpy, matplotlib
"""
import argparse
import glob
import os
import math
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def find_internal_vtk(case_dir):
    vtk_dir = os.path.join(case_dir, "VTK")
    if not os.path.isdir(vtk_dir):
        print("ERREUR : dossier VTK/ introuvable. Lancez d'abord :")
        print("    foamToVTK -latestTime")
        raise SystemExit(1)
    candidates = (glob.glob(os.path.join(vtk_dir, "**", "*internal*.vtu"), recursive=True)
                  + glob.glob(os.path.join(vtk_dir, "**", "*internal*.vtk"), recursive=True))
    if not candidates:
        all_files = (glob.glob(os.path.join(vtk_dir, "**", "*.vtu"), recursive=True)
                     + glob.glob(os.path.join(vtk_dir, "**", "*.vtk"), recursive=True))
        excluded = ("inlet", "outlet", "plate", "sidea", "sideb", "frontandback")
        candidates = [f for f in all_files
                      if not any(x in os.path.basename(f).lower() for x in excluded)]
    if not candidates:
        raise SystemExit("Aucun fichier VTK exploitable trouve sous " + vtk_dir)
    return max(candidates, key=os.path.getmtime)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", nargs="?", default=".")
    ap.add_argument("--alpha", type=float, required=True)
    ap.add_argument("--b", type=float, default=1.0)
    ap.add_argument("--U0", type=float, default=0.75)
    args = ap.parse_args()

    latest = find_internal_vtk(args.case_dir)
    print("Lecture de :", latest)
    mesh = pv.read(latest)
    print("Champs disponibles :", mesh.array_names)

    a = math.radians(args.alpha)
    chord = np.array([math.cos(a), math.sin(a)])     # direction de la corde
    perp = np.array([-math.sin(a), math.cos(a)])      # normale a la plaque
    b = args.b

    FIG_DIR = os.path.join(args.case_dir, "figures")
    os.makedirs(FIG_DIR, exist_ok=True)

    # ---------------- 1) profils de vitesse dans le sillage (comme Fig 10-11) ----------------
    # lignes perpendiculaires a l'ecoulement (+x), a quelques distances en aval
    fig, ax = plt.subplots(figsize=(7, 6))
    for x_over_b in [5, 10, 20]:
        x0 = x_over_b * b
        y = np.linspace(-3*b, 3*b, 200)
        pts = np.column_stack([np.full_like(y, x0), y, np.zeros_like(y)])
        line = pv.PolyData(pts)
        sampled = line.sample(mesh)
        if "U" not in sampled.array_names:
            continue
        Umag = np.linalg.norm(sampled["U"], axis=1)
        ax.plot(Umag/args.U0, y/b, label=f"x/b={x_over_b}")
    ax.set_xlabel("V / V0")
    ax.set_ylabel("y/b")
    ax.set_title(f"Profils de vitesse dans le sillage (alpha={args.alpha} deg)\n(a comparer aux Fig. 10-11 de Raciti Castelli et al.)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out1 = os.path.join(FIG_DIR, "07_profils_vitesse_sillage.png")
    fig.savefig(out1, dpi=150)
    print("[OK]", out1)

    # ---------------- 1b) profils de PRESSION dans le sillage (meme style) ----------------
    fig, ax = plt.subplots(figsize=(7, 6))
    for x_over_b in [5, 10, 20]:
        x0 = x_over_b * b
        y = np.linspace(-3*b, 3*b, 200)
        pts = np.column_stack([np.full_like(y, x0), y, np.zeros_like(y)])
        line = pv.PolyData(pts)
        sampled = line.sample(mesh)
        if "p" not in sampled.array_names:
            continue
        Cp = np.asarray(sampled["p"]) / (0.5*args.U0**2)
        ax.plot(Cp, y/b, label=f"x/b={x_over_b}")
    ax.set_xlabel("Cp = p / (0.5 V0^2)")
    ax.set_ylabel("y/b")
    ax.set_title(f"Profils de pression dans le sillage (alpha={args.alpha} deg)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out1b = os.path.join(FIG_DIR, "07b_profils_pression_sillage.png")
    fig.savefig(out1b, dpi=150)
    print("[OK]", out1b)

    # ---------------- 2) coefficient de pression le long de la plaque (comme Fig 4) ----------------
    # foamToVTK exporte aussi chaque patch nomme separement (VTK/<case>/boundary/plate.vtu) :
    # on lit directement cette surface plutot que de filtrer geometriquement le maillage
    # interne (plus robuste, p deja evalue exactement sur la paroi).
    vtk_dir = os.path.join(args.case_dir, "VTK")
    plate_candidates = (glob.glob(os.path.join(vtk_dir, "**", "*plate*.vtu"), recursive=True)
                         + glob.glob(os.path.join(vtk_dir, "**", "*plate*.vtk"), recursive=True)
                         + glob.glob(os.path.join(vtk_dir, "**", "*plate*.vtp"), recursive=True))
    plate_candidates = [c for c in plate_candidates if "internal" not in c.lower()]

    if not plate_candidates:
        print("[INFO] fichier VTK du patch 'plate' introuvable sous VTK/ -- "
              "verifiez que foamToVTK exporte bien les patches nommes "
              "(certaines versions demandent l'option -patches), figure Cp ignoree.")
    else:
        plate_path = max(plate_candidates, key=os.path.getmtime)
        print("Lecture du patch plate :", plate_path)
        plate_mesh = pv.read(plate_path)
        if "p" not in plate_mesh.array_names:
            print("[INFO] champ p absent du patch plate, figure Cp ignoree")
        else:
            pts = plate_mesh.points
            proj = pts[:, :2] @ chord
            p_vals = plate_mesh["p"] if "p" in plate_mesh.point_data else plate_mesh.cell_data["p"]
            order = np.argsort(proj)
            Cp = np.asarray(p_vals)[order] / (0.5*args.U0**2)
            s = (proj[order] + b/2) / b

            fig, ax = plt.subplots(figsize=(7, 5))
            ax.plot(s, Cp, '.', ms=3)
            ax.set_xlabel("position le long de la corde (0=bord d'attaque, 1=bord de fuite)")
            ax.set_ylabel("Cp = p / (0.5 V0^2)")
            ax.set_title(f"Coefficient de pression le long de la plaque (alpha={args.alpha} deg)\n"
                         "(a comparer a la Fig. 4 de Fage & Johansen)")
            ax.grid(alpha=0.3)
            fig.tight_layout()
            out2 = os.path.join(FIG_DIR, "08_Cp_le_long_plaque.png")
            fig.savefig(out2, dpi=150)
            print("[OK]", out2)


if __name__ == "__main__":
    main()
