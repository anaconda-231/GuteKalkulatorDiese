PRAGMA foreign_keys = ON;

-- Avora/Avora Root: echte Datenblatt-Werte (Datasheet_AVORA_rev5.pdf)
-- ersetzen die bisherigen Platzhalterwerte (die 1:1 von AURA uebernommen
-- waren: 1,5mm/500x500mm/8,7kg/158W). Beide Produkte sind laut
-- Ruecksprache dasselbe physische Panel und unterscheiden sich nur in der
-- Montageart (siehe product_mechanics) - deshalb identische Werte fuer
-- Avora (id 19) und Avora Root (id 20).
-- max_power_consumption_w = Maximum-Wert (360 W/Cabinet), konsistent mit
-- der Konvention im uebrigen Katalog (immer Maximum, nicht Average).
-- "Weight with wind bracing" (16,58 kg) ist im Schema nicht separat
-- abbildbar (nur ein weight_kg-Feld) - Basisgewicht (12 kg) uebernommen,
-- wie bei allen anderen Katalogeintraegen.
UPDATE article_catalog_mock
SET
    pixelpitch_mm = 3.91,
    width_mm = 500,
    height_mm = 1000,
    weight_kg = 12,
    max_power_consumption_w = 360,
    is_indoor_capable = 1,
    is_outdoor_capable = 1
WHERE id IN (19, 20);
