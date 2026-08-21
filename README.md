# Plaque plane inclinée à 30° — écoulement RANS (OpenFOAM)

Simulation d'une plaque plane mince inclinée de 30° par rapport à un
écoulement uniforme, résolue en RANS (k-omega SST) avec `simpleFoam`.
Le cas reproduit la configuration de Fage & Johansen (1927) et de
Raciti Castelli, Cioppa & Benini (2012) : plaque de corde `b`,
domaine de 12 cordes en amont, 25 cordes en aval, ±10 cordes
latéralement, faces latérales en `symmetryPlane`.

La grandeur comparée à la référence est le coefficient de force
normale à la plaque :

```
kN = FN / (rho * b * V0^2)
```

(convention de Fage & Johansen, sans le facteur 1/2 habituel des
coefficients aérodynamiques). Référence : **kN = 0.645**.

## Contenu

```
scripts/            scripts communs aux 4 maillages (identiques dans chaque cas)
  compute_kN.py        calcule kN à partir de postProcessing/forceCoeffs1
  plot_fields.py        cartes de champs (U, p) à partir d'un export VTK
  plot_profiles.py      profils de vitesse/pression dans le sillage + Cp le long de la plaque
  plot_residuals.py     courbes de convergence des résidus

cases/
  grossier/          26 380 cellules
  intermediaire/     46 454 cellules
  fin/               103 598 cellules
  finer/             183 282 cellules
```

Chaque dossier de `cases/` contient tout ce qu'il faut pour régénérer
le cas OpenFOAM : `plaque.geo` (géométrie GMSH), `Allrun`, `0.orig/`,
`constant/`, `system/`. Les résultats bruts (champs à chaque pas de
temps, export VTK, logs de résolution) ne sont pas versionnés : ils se
régénèrent en une commande (`./Allrun`) et pèsent plusieurs dizaines
de Mo par cas. Seules les figures finales (`figures/`) et les
coefficients de force (`postProcessing/forceCoeffs1/`, quelques Ko)
sont gardés.

## Reproduire un cas

Depuis `cases/<nom_du_cas>/` :

```bash
./Allrun
```

Le script génère le maillage avec GMSH, le convertit avec
`gmshToFoam`, demande une vérification manuelle de
`constant/polyMesh/boundary` (GMSH ne renseigne pas toujours le bon
type de patch), puis lance `checkMesh`, `renumberMesh` et `simpleFoam`.

Post-traitement :

```bash
python3 ../../scripts/compute_kN.py . --alpha 30 --kN-ref 0.645
foamToVTK -latestTime
python3 ../../scripts/plot_fields.py .
python3 ../../scripts/plot_profiles.py . --alpha 30
python3 ../../scripts/plot_residuals.py log.simpleFoam --out figures/09_residus.png
```

## Étude de convergence de maillage

Les quatre maillages ne diffèrent que par la taille de maille imposée
près de la plaque (`lc_plate`) et loin du corps (`lc_far`) dans
`plaque.geo` — tout le reste du cas est identique.

| Maillage      | Cellules | kN    | Écart à la référence |
|---------------|---------:|------:|----------------------:|
| Grossier      |   26 380 | 0.631 | -2.1 %                |
| Intermédiaire |   46 454 | 0.583 | -9.6 %                |
| Fin           |  103 598 | 0.563 | -12.7 %               |
| Finer         |  183 282 | 0.557 | -13.7 %               |

Référence (Fage & Johansen, 1927) : kN = 0.645.

kN oscille légèrement en régime permanent sur les maillages grossier,
fin et finer (moyenne calculée sur la seconde moitié du calcul), alors
que le maillage intermédiaire converge de façon plus stricte. L'écart
entre le maillage fin et le maillage encore plus fin reste faible
(~1 %), ce qui indique que la valeur s'est stabilisée autour de
kN ≈ 0.56, en dessous de la valeur expérimentale de Fage & Johansen.
Cet écart est cohérent avec l'ordre de grandeur rapporté par
Raciti Castelli et al. pour ce type de modélisation RANS 2D.

## Paramètres physiques

- Modèle de turbulence : k-omega SST (RAS)
- Fluide : newtonien, nu = 1.5e-5 m²/s
- Vitesse d'entrée : U0 = 0.75 m/s (alignée sur x)
- Schémas convectifs : upwind borné sur U, k, omega
- 30 000 itérations (`simpleFoam`)
