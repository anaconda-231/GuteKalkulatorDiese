PRAGMA foreign_keys = ON;

-- INFiLED MV-Serie (Indoor) - 13 Modelle ueber drei Pixelpitches (3,91 /
-- 2,97 / 5,95 mm), jeweils in mini/Pro/Pro-mini-Auspraegung (5,95mm
-- zusaetzlich "PH" = Portrait/Hochkant-Cabinet 500x1000mm statt 500x500 /
-- 1000x1000mm). Nur Indoor - Outdoor-Pendants folgen laut Ruecksprache
-- spaeter und werden dann per UPDATE auf dieselben Artikel-Zeilen oder
-- als weitere Zeilen ergaenzt. Ruecksprache: die MV-Serie gibt es nur als
-- Festinstallation, deshalb is_temporary_capable = 0 fuer alle Modelle
-- (analog zur INFiLED-Wallpaper-Serie und RX-Serie).
-- Max. Power Consumption steht in diesen Datenblaettern bereits als
-- W/Panel (nicht W/m² wie bei der RX-Serie), daher direkte Uebernahme
-- ohne Umrechnung.
INSERT INTO article_catalog_mock
    (article_number, name, pixelpitch_mm, width_mm, height_mm, weight_kg, max_power_consumption_w,
     is_indoor_capable, is_outdoor_capable, is_fixed_capable, is_temporary_capable)
VALUES
    -- 3,91 mm Familie
    ('IL-FISS-IRMV3.9 mini',     'MV3.9 mini',     3.91, 500,  500,  8.1,  135, 1, 0, 1, 0),
    ('IL-FISS-IRMV3.9',          'MV3.9',          3.91, 1000, 1000, 18.6, 540, 1, 0, 1, 0),
    ('IL-FISS-IRMV3.9 Pro mini', 'MV3.9 Pro mini', 3.91, 500,  500,  8.1,  135, 1, 0, 1, 0),
    ('IL-FISS-IRMV3.9 Pro',      'MV3.9 Pro',      3.91, 1000, 1000, 18.6, 540, 1, 0, 1, 0),
    -- 2,97 mm Familie
    ('IL-FISS-IRMV2.9',          'MV2.9',          2.97, 1000, 1000, 18.6, 540, 1, 0, 1, 0),
    ('IL-FISS-IRMV2.9 mini',     'MV2.9 mini',     2.97, 500,  500,  8.1,  135, 1, 0, 1, 0),
    ('IL-FISS-IRMV2.9 Pro',      'MV2.9 Pro',      2.97, 1000, 1000, 18.6, 540, 1, 0, 1, 0),
    ('IL-FISS-IRMV2.9 Pro mini', 'MV2.9 Pro mini', 2.97, 500,  500,  8.1,  135, 1, 0, 1, 0),
    -- 5,95 mm Familie (inkl. PH = Portrait-Cabinet 500x1000mm)
    ('IL-FISS-IRMV5.9',          'MV5.9',          5.95, 1000, 1000, 18.6, 540, 1, 0, 1, 0),
    ('IL-FISS-IRMV5.9 PH',       'MV5.9 PH',       5.95, 500,  1000, 12.8, 270, 1, 0, 1, 0),
    ('IL-FISS-IRMV5.9 mini',     'MV5.9 mini',     5.95, 500,  500,  8.1,  135, 1, 0, 1, 0),
    ('IL-FISS-IRMV5.9 Pro',      'MV5.9 Pro',      5.95, 1000, 1000, 18.6, 540, 1, 0, 1, 0),
    ('IL-FISS-IRMV5.9 Pro mini', 'MV5.9 Pro mini', 5.95, 500,  500,  8.1,  135, 1, 0, 1, 0);

INSERT INTO configurator_product (product_article_id, name)
VALUES (NULL, 'INFiLED MV Series');

INSERT INTO configurator_product_article (configurator_product_id, article_catalog_mock_id)
SELECT
    (SELECT id FROM configurator_product WHERE name = 'INFiLED MV Series'),
    ac.id
FROM article_catalog_mock ac
WHERE ac.article_number IN
    ('IL-FISS-IRMV3.9 mini', 'IL-FISS-IRMV3.9', 'IL-FISS-IRMV3.9 Pro mini', 'IL-FISS-IRMV3.9 Pro',
     'IL-FISS-IRMV2.9', 'IL-FISS-IRMV2.9 mini', 'IL-FISS-IRMV2.9 Pro', 'IL-FISS-IRMV2.9 Pro mini',
     'IL-FISS-IRMV5.9', 'IL-FISS-IRMV5.9 PH', 'IL-FISS-IRMV5.9 mini', 'IL-FISS-IRMV5.9 Pro', 'IL-FISS-IRMV5.9 Pro mini');
