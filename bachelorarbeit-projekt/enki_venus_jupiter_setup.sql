-- Praezisierung der Montagearten fuer ENKI, VENUS und JUPITER.
-- Fremdschluessel muessen in SQLite pro Verbindung aktiviert werden.
PRAGMA foreign_keys = ON;

-- ENKI hatte bisher UEBERHAUPT kein mechanisches System verknuepft (keine
-- Montageart im UI waehlbar). Wie die uebrige Aura-Familie bekommt ENKI
-- Standard-Stacking, Hanging-Truss und Wandadapter - bewusst OHNE NoBase:
-- 'No Base' (bodenfreischwebend, ohne Basis-Footbeam) ist bei ENKI
-- konstruktionsbedingt nicht umsetzbar (Ruecksprache LANG AG) und darf
-- deshalb weder im UI-Dropdown auswaehlbar sein noch in der Kalkulation
-- auftauchen. Da product_mechanics die einzige Quelle fuer
-- /api/mechanics-options ist (server.py), reicht das Weglassen der
-- NoBase-Verknuepfung aus, um sie ueberall zuverlaessig auszublenden.
INSERT INTO product_mechanics (product_id, system_id)
SELECT cp.id, ms.id
FROM configurator_product cp
JOIN article_catalog_mock ac ON ac.id = cp.product_article_id
CROSS JOIN mechanical_systems ms
WHERE ac.name = 'ENKI'
  AND ms.name IN ('Standard-Stacking', 'Hanging-Truss', 'Wandadapter');

-- VENUS und JUPITER sind bereits an Standard-Stacking, Hanging-Truss,
-- Wandadapter UND NoBase angebunden (siehe curving_setup.sql) - keine
-- weitere DB-Aenderung noetig. Die "Stacker 3 Cabinets hoch"-Abweichung vom
-- Aura-Konzept fuer den Stacking-Modus ist reine Berechnungslogik
-- (STACKER_SPAN_BY_PRODUCT in server.py), keine eigene Verknuepfungstabelle
-- oder ein eigenes mechanical_systems-Row noetig, weil sonst NICHTS von der
-- Aura-Logik abweicht (Ruecksprache: "1:1 kopiert, mit dem spezifischen
-- Unterschied, dass der vertikale Stacker exakt 3 Cabinets hoch ist").
