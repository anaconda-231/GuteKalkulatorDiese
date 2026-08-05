-- Curving-Feature: Datenbank-Vorbereitung.
-- Fremdschluessel muessen in SQLite pro Verbindung aktiviert werden.
PRAGMA foreign_keys = ON;

-- JUPITER, VENUS und MERI 500x1000 haben bereits vollstaendige
-- article_catalog_mock/configurator_product-Eintraege, waren aber bisher an
-- KEIN mechanisches System angebunden (kein Montage-Modus waehlbar). Sie
-- folgen mechanisch dem Aura-Konzept (wie ARUNA/LUGH/MERI 500x500, siehe
-- mechanical_systems.sql) - deshalb dieselben vier Systeme.
INSERT INTO product_mechanics (product_id, system_id)
SELECT cp.id, ms.id
FROM configurator_product cp
JOIN article_catalog_mock ac ON ac.id = cp.product_article_id
CROSS JOIN mechanical_systems ms
WHERE ac.name IN ('JUPITER', 'VENUS', 'MERI 500x1000')
  AND ms.name IN ('Standard-Stacking', 'Hanging-Truss', 'Wandadapter', 'NoBase');

-- Platzhalter-Statik-Grenzwerte fuer JUPITER/VENUS/MERI 500x1000 werden in
-- server.py gepflegt (MAX_STACKING_HEIGHT_BY_PRODUCT / HANGING_OESEN_LIMITS_
-- BY_PRODUCT, jeweils = AURA-Wert), nicht in der Datenbank.

-- AR 10.41 folgt mechanisch dem AR3.9-Konzept (AR3.91 Plus LE) - AR-Stacking
-- + AR-Hanging, exklusiv (kein Standard-Stacking/NoBase/Wandadapter).
INSERT INTO product_mechanics (product_id, system_id)
SELECT cp.id, ms.id
FROM configurator_product cp
JOIN article_catalog_mock ac ON ac.id = cp.product_article_id
CROSS JOIN mechanical_systems ms
WHERE ac.name = 'AR 10.41'
  AND ms.name IN ('AR-Stacking', 'AR-Hanging');

-- Neue Produkte Avora / Avora Root (Curving-faehig, Aura-Konzept). Reale
-- Datenblattwerte liegen von der LANG AG noch nicht vor - Platzhalter-Specs
-- angelehnt an AURA (id 3), muss durch die LANG AG bestaetigt werden.
INSERT INTO article_catalog_mock
    (article_number, name, pixelpitch_mm, width_mm, height_mm, weight_kg,
     max_power_consumption_w, is_outdoor_capable, is_temporary_capable,
     is_indoor_capable, is_fixed_capable)
VALUES
    ('LANG-019', 'Avora', 1.5, 500, 500, 8.7, 158, 0, 1, 1, 1),
    ('LANG-020', 'Avora Root', 1.5, 500, 500, 8.7, 158, 0, 1, 1, 1);

INSERT INTO configurator_product (product_article_id, name)
SELECT id, name || ' Config'
FROM article_catalog_mock
WHERE name IN ('Avora', 'Avora Root');

INSERT INTO product_mechanics (product_id, system_id)
SELECT cp.id, ms.id
FROM configurator_product cp
JOIN article_catalog_mock ac ON ac.id = cp.product_article_id
CROSS JOIN mechanical_systems ms
WHERE ac.name IN ('Avora', 'Avora Root')
  AND ms.name IN ('Standard-Stacking', 'Hanging-Truss', 'Wandadapter', 'NoBase');
