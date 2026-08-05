PRAGMA foreign_keys = ON;

-- Serie->Modell-Auswahl fuer Festinstallation: Verknuepfungstabelle, die es
-- einer Serie (configurator_product) erlaubt, mehrere Modelle/Pixelpitches
-- (article_catalog_mock) anzubieten, statt wie bisher exakt eines
-- (product_article_id). Bestehende 1:1-Zuordnungen werden unten uebernommen,
-- damit alle bisherigen Serien unveraendert weiterfunktionieren (das
-- Modell-Dropdown zeigt dort einfach genau ein Modell).
CREATE TABLE IF NOT EXISTS configurator_product_article (
    configurator_product_id INTEGER NOT NULL,
    article_catalog_mock_id INTEGER NOT NULL,
    PRIMARY KEY (configurator_product_id, article_catalog_mock_id),
    FOREIGN KEY (configurator_product_id) REFERENCES configurator_product (id)
        ON DELETE CASCADE,
    FOREIGN KEY (article_catalog_mock_id) REFERENCES article_catalog_mock (id)
        ON DELETE CASCADE
);

INSERT OR IGNORE INTO configurator_product_article (configurator_product_id, article_catalog_mock_id)
SELECT id, product_article_id
FROM configurator_product
WHERE product_article_id IS NOT NULL;

-- INFiLED Wallpaper-Serie (siehe Datenblaetter): sieben Modelle mit jeweils
-- eigenem Pixelpitch, exklusiv fuer Festinstallation - is_temporary_capable
-- = 0, da die Wallpaper-Serie laut Datenblatt eine reine
-- Festinstallationsloesung ist (kein Verleih-/temporaerer Einsatz).
-- Indoor-only (is_outdoor_capable = 0), Cabinet-Groesse einheitlich
-- 600 x 337,5 mm (hier wie bei den uebrigen 600er-Cabinets dieses Katalogs
-- als 337 mm gefuehrt, siehe ENKI/LEDGEND).
INSERT INTO article_catalog_mock
    (article_number, name, pixelpitch_mm, width_mm, height_mm, weight_kg, max_power_consumption_w,
     is_indoor_capable, is_outdoor_capable, is_fixed_capable, is_temporary_capable)
VALUES
    ('INF-WP094',     'WP0.9m4 LE',      0.94, 600, 337, 6.8, 180, 1, 0, 1, 0),
    ('INF-WP125',     'WP1.2 LE',        1.25, 600, 337, 5.2, 180, 1, 0, 1, 0),
    ('INF-WP125PRO',  'WP1.2 LE pro',    1.25, 600, 337, 5.2, 180, 1, 0, 1, 0),
    ('INF-WP156',     'WP1.5 LE',        1.56, 600, 337, 5.2, 180, 1, 0, 1, 0),
    ('INF-WP156PRO',  'WP1.5 LE pro',    1.56, 600, 337, 5.2, 180, 1, 0, 1, 0),
    ('INF-WP156M4',   'WP1.5m4 LE',      1.56, 600, 337, 5.2, 180, 1, 0, 1, 0),
    ('INF-WP156M4R2', 'WP1.56m4 LE-R2',  1.56, 600, 337, 5.2, 180, 1, 0, 1, 0);

-- Serie-Eintrag ohne product_article_id (NULL = "Mehrmodell-Serie", siehe
-- /api/products in server.py: dieser INNER JOIN uebergeht Serien ohne
-- product_article_id automatisch - die WP-Serie erscheint deshalb nur ueber
-- die neuen Endpunkte /api/product-series und /api/product-models, nicht in
-- der alten Flachliste, und damit auch nicht im temporaeren Einsatz, da dort
-- ohnehin nur /api/products verwendet wird).
INSERT INTO configurator_product (product_article_id, name)
VALUES (NULL, 'INFiLED WP Wallpaper');

INSERT INTO configurator_product_article (configurator_product_id, article_catalog_mock_id)
SELECT
    (SELECT id FROM configurator_product WHERE name = 'INFiLED WP Wallpaper'),
    ac.id
FROM article_catalog_mock ac
WHERE ac.article_number IN
    ('INF-WP094', 'INF-WP125', 'INF-WP125PRO', 'INF-WP156', 'INF-WP156PRO', 'INF-WP156M4', 'INF-WP156M4R2');
