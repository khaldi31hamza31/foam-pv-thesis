#!/usr/bin/env python3
"""
Genere des figures de contour pour les champs U (magnitude) et p a partir
de la sortie VTK d'OpenFOAM.

Etape prealable obligatoire, depuis le dossier du cas :
    foamToVTK -latestTime          (ou sans -latestTime pour tous les instants)

Cela cree un dossier VTK/ que ce script lit ensuite.

Usage :
    python3 plot_fields.py [chemin_du_cas]

Necessite : pyvista, vtk, numpy   (pip install --break-system-packages pyvista vtk numpy)
"""
import sys
import os
import glob
import numpy as np
import pyvista as pv

CASE_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
VTK_DIR = os.path.join(CASE_DIR, "VTK")
FIG_DIR = os.path.join(CASE_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def find_latest_internal_vtk():
    if not os.path.isdir(VTK_DIR):
        print("ERREUR : dossier VTK/ introuvable.")
        print("Lancez d'abord, depuis le dossier du cas :")
        print("    foamToVTK -latestTime")
        sys.exit(1)

    candidates = (
        glob.glob(os.path.join(VTK_DIR, "**", "*internal*.vtu"), recursive=True)
        + glob.glob(os.path.join(VTK_DIR, "**", "*internal*.vtk"), recursive=True)
    )
    if not candidates:
        # certaines versions n'ajoutent pas "internal" au nom : on prend
        # tout fichier vtu/vtk qui n'est pas un patch de bord connu
        all_files = (
            glob.glob(os.path.join(VTK_DIR, "**", "*.vtu"), recursive=True)
            + glob.glob(os.path.join(VTK_DIR, "**", "*.vtk"), recursive=True)
        )
        excluded = ("inlet", "outlet", "plate", "top", "bottom", "frontandback")
        candidates = [f for f in all_files
                      if not any(x in os.path.basename(f).lower() for x in excluded)]
    if not candidates:
        print("ERREUR : aucun fichier VTK exploitable trouve sous", VTK_DIR)
        sys.exit(1)

    return max(candidates, key=os.path.getmtime)


def main():
    latest = find_latest_internal_vtk()
    print("Lecture de :", latest)
    mesh = pv.read(latest)
    print("Champs disponibles :", mesh.array_names)

    try:
        pv.start_xvfb()
    except Exception:
        pass  # deja disponible ou pas necessaire (affichage present)

    # --- champ U : magnitude ---
    if "U" in mesh.array_names:
        U = mesh["U"]
        mesh["U_mag"] = np.linalg.norm(U, axis=1)
        plotter = pv.Plotter(off_screen=True, window_size=(1600, 500))
        plotter.add_mesh(mesh, scalars="U_mag", cmap="viridis", show_edges=False)
        plotter.view_xy()
        plotter.enable_parallel_projection()
        out = os.path.join(FIG_DIR, "04_champ_vitesse.png")
        plotter.screenshot(out)
        print("[OK]", out)
    else:
        print("[INFO] champ U absent, figure vitesse ignoree")

    # --- champ p ---
    if "p" in mesh.array_names:
        plotter = pv.Plotter(off_screen=True, window_size=(1600, 500))
        plotter.add_mesh(mesh, scalars="p", cmap="coolwarm", show_edges=False)
        plotter.view_xy()
        plotter.enable_parallel_projection()
        out = os.path.join(FIG_DIR, "05_champ_pression.png")
        plotter.screenshot(out)
        print("[OK]", out)
    else:
        print("[INFO] champ p absent, figure pression ignoree")

    # --- zoom sur le sillage proche (utile pour voir l'allee tourbillonnaire) ---
    if "U" in mesh.array_names:
        clipped = mesh.clip_box(bounds=(-2, 10, -3, 3, -1, 1), invert=False)
        plotter = pv.Plotter(off_screen=True, window_size=(1400, 700))
        plotter.add_mesh(clipped, scalars="U_mag", cmap="viridis", show_edges=False)
        plotter.view_xy()
        plotter.enable_parallel_projection()
        out = os.path.join(FIG_DIR, "06_zoom_sillage_vitesse.png")
        plotter.screenshot(out)
        print("[OK]", out)


if __name__ == "__main__":
    main()
