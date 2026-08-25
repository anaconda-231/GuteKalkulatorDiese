-- AR3.9 / Avora Root Outdoor-Stacking (Ruecksprache LANG AG)
--
-- Eigener Outdoor-Baukasten mit eigenen Vertriebsnummern (INFILED-ER-*):
--   Basement  INFILED-ER-FOOT-W1 / -W2 / -W3   (3-2-1-Breitenverteilung)
--   Footbeam  INFILED-ER-FBEAM-L1m             (1 m, unter jeder Cabinetspalte)
--   Stacker   INFILED-ER-STACK-H1              (1 m = 1 Cabinet hoch)
--   Clamp     INFILED-ER-CLP-SINGL             (je Cabinet, oben mittig)
--
-- Rechnerisch ist das exakt die Geometrie des bestehenden AR-Stacking-Systems
-- (Footbeam 1:1 zum Cabinet-Raster, Stacker ueber genau 1 Reihe, 1 Clamp je
-- Stacker) - deshalb teilt sich das System in server.py den Rechenweg mit
-- AR-Stacking (_calculate_ar_stacking_mechanics) und unterscheidet sich nur
-- ueber den Systemnamen, an dem im Frontend die ER-Artikelnummern haengen.
-- "Jede Spalte muss abgesichert sein" ist damit erfuellt: footbeams =
-- width_cabinets, also eine Stacker-/Clamp-Achse je Cabinetspalte.
--
-- ui_mode 'Stacking' ordnet es demselben festen UI-Button zu wie die uebrigen
-- Stacking-Systeme. Sichtbar ist es ausschliesslich bei Einsatzort "outdoor"
-- und verdraengt dort die Indoor-Systeme desselben Modus - siehe
-- SYSTEM_LOCATION_ONLY / api_mechanics_options in server.py.
PRAGMA foreign_keys = ON;

INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type, ui_mode)
SELECT 'AR-Outdoor-Stacking', 'INFILED-ER-CLP-SINGL', 'Ground-Support', 'Stacking'
WHERE NOT EXISTS (SELECT 1 FROM mechanical_systems WHERE name = 'AR-Outdoor-Stacking');

-- AR3.91 Plus LE, Avora Root und AR 10.41 (Ruecksprache: "Das Outdoor
-- stacking zaehlt auch fuer ar10") - die komplette AR-Familie nutzt Outdoor
-- denselben ER-Baukasten.
INSERT INTO product_mechanics (product_id, system_id)
SELECT ac.id, (SELECT id FROM mechanical_systems WHERE name = 'AR-Outdoor-Stacking')
FROM article_catalog_mock ac
WHERE ac.name IN ('AR3.91 Plus LE', 'Avora Root', 'AR 10.41')
  AND NOT EXISTS (
      SELECT 1 FROM product_mechanics pm
      WHERE pm.product_id = ac.id
        AND pm.system_id = (SELECT id FROM mechanical_systems WHERE name = 'AR-Outdoor-Stacking')
  );
