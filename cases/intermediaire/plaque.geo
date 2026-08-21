// ============================================================
// Plaque plane inclinee - maillage GMSH
// Geometrie fidele a Raciti Castelli, Cioppa & Benini (2012) /
// Fage & Johansen (1927) : 12 cordes amont, 25 cordes aval,
// plaque vraiment inclinee dans un domaine fixe.
//
// Utilisation :
//   gmsh -3 plaque.geo -o plaque.msh -format msh2
//   gmshToFoam plaque.msh -case <dossier_du_cas>
//
// Puis, dans constant/polyMesh/boundary, verifier/corriger les
// types (voir README.md) : gmshToFoam laisse tout en
// "patch" par defaut, il faut mettre "empty" pour frontAndBack,
// "wall" pour plate, "symmetryPlane" pour sideA/sideB (comme
// Fig. 2 de Raciti Castelli et al.).
// ============================================================

// ---- parametres (SEULE la ligne alpha change d'un angle a l'autre) ----
alpha = 30;              // angle d'incidence (deg)
b     = 1.0;             // corde de la plaque
t     = 0.03*b;          // epaisseur (3% de la corde, comme Fage & Johansen)
Lup   = 12*b;
Ldown = 25*b;
H     = 10*b;             // demi-hauteur du domaine
dz    = 0.01;              // epaisseur du "slab" 2D en z

lc_plate = 0.006*b;       // taille de maille pres de la plaque
lc_far   = 0.6*b;         // taille de maille loin (coins du domaine)

// ---- geometrie de la plaque ----
alphaRad = alpha * Pi / 180;
cx = Cos(alphaRad); cy = Sin(alphaRad);      // direction de la corde
px = -Sin(alphaRad); py = Cos(alphaRad);     // direction perpendiculaire (epaisseur)

Point(1) = { -b/2*cx - t/2*px, -b/2*cy - t/2*py, 0, lc_plate };  // bord d'attaque, face 1
Point(2) = { -b/2*cx + t/2*px, -b/2*cy + t/2*py, 0, lc_plate };  // bord d'attaque, face 2
Point(3) = {  b/2*cx + t/2*px,  b/2*cy + t/2*py, 0, lc_plate };  // bord de fuite,  face 2
Point(4) = {  b/2*cx - t/2*px,  b/2*cy - t/2*py, 0, lc_plate };  // bord de fuite,  face 1

Line(1) = {1,2};   // bord d'attaque (pointe)
Line(2) = {2,3};   // face superieure de la plaque
Line(3) = {3,4};   // bord de fuite (pointe)
Line(4) = {4,1};   // face inferieure de la plaque
Line Loop(1) = {1,2,3,4};

// ---- domaine exterieur ----
Point(11) = {-Lup,  -H, 0, lc_far};
Point(12) = { Ldown,-H, 0, lc_far};
Point(13) = { Ldown, H, 0, lc_far};
Point(14) = {-Lup,   H, 0, lc_far};

Line(11) = {11,12};   // bas          (-> sideA)
Line(12) = {12,13};   // droite       (-> outlet)
Line(13) = {13,14};   // haut         (-> sideB)
Line(14) = {14,11};   // gauche       (-> inlet)
Line Loop(11) = {11,12,13,14};

Plane Surface(1) = {11, 1};   // domaine fluide = rectangle MOINS la plaque

// ---- controle du raffinement (fin pres de la plaque, grossier loin) ----
Field[1] = Distance;
Field[1].CurvesList = {1,2,3,4};
Field[1].Sampling = 300;

Field[2] = Threshold;
Field[2].InField = 1;
Field[2].SizeMin = lc_plate;
Field[2].SizeMax = lc_far;
Field[2].DistMin = 0.15*b;
Field[2].DistMax = 6*b;

Background Field = 2;
Mesh.CharacteristicLengthExtendFromBoundary = 0;

// ---- extrusion 1 couche en z (maillage "slab" 2D pour OpenFOAM) ----
// Convention GMSH (a verifier via checkMesh, voir README.md) :
//   out[0] = surface "haut" (z=dz)
//   out[1] = volume
//   out[2..5] = faces laterales issues de Line(11,12,13,14) -> sideA,outlet,sideB,inlet
//   out[6..9] = faces laterales issues de Line(1,2,3,4)     -> plate (4 aretes)
out[] = Extrude {0, 0, dz} { Surface{1}; Layers{1}; Recombine; };

Physical Surface("frontAndBack") = {1, out[0]};
Physical Volume("fluid")  = {out[1]};
Physical Surface("sideA")  = {out[2]};
Physical Surface("outlet") = {out[3]};
Physical Surface("sideB")  = {out[4]};
Physical Surface("inlet")  = {out[5]};
Physical Surface("plate")  = {out[6], out[7], out[8], out[9]};

Mesh.Algorithm = 6;   // Frontal-Delaunay, bonne qualite pour geometries fines
