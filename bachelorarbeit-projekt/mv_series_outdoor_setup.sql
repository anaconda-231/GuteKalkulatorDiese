PRAGMA foreign_keys = ON;

-- INFiLED MV-Serie (Outdoor) - Ergaenzung der bereits bestehenden Serie
-- "INFiLED MV Series" (siehe mv_series_setup.sql, 13 Indoor-Modelle) um 20
-- Outdoor-Modelle ueber vier Pixelpitches (12,5 / 7,81 / 5,95 / 2,97 mm),
-- jeweils in mehreren Auspraegungen (mini/Pro/Pro-mini/Max/Max-mini - nicht
-- jede Pixelpitch hat alle Auspraegungen, siehe Datenblaetter). Gleiches
-- Muster wie bei der RX-Serie: EINE Serie, is_indoor_capable/
-- is_outdoor_capable trennen die Modelle pro Artikel-Zeile, wodurch der
-- bestehende location-Filter in /api/product-models automatisch die
-- passenden Modelle zeigt - keine zweite Serie noetig.
-- Ruecksprache: die MV-Serie gibt es nur als Festinstallation, deshalb
-- is_temporary_capable = 0 fuer alle Modelle (wie bei den Indoor-Modellen).
-- Max. Power Consumption steht bereits als W/Panel, keine Umrechnung noetig.
INSERT INTO article_catalog_mock
    (article_number, name, pixelpitch_mm, width_mm, height_mm, weight_kg, max_power_consumption_w,
     is_indoor_capable, is_outdoor_capable, is_fixed_capable, is_temporary_capable)
VALUES
    -- 12,5 mm Familie
    ('IL-FISS-ORMV12.5',          'MV12.5',          12.5, 1000, 1000, 19.6,  660, 0, 1, 1, 0),
    ('IL-FISS-ORMV12.5 mini',     'MV12.5 mini',     12.5, 500,  500,  8.3,   165, 0, 1, 1, 0),
    ('IL-FISS-ORMV12.5 Pro',      'MV12.5 Pro',      12.5, 1000, 1000, 19.6,  540, 0, 1, 1, 0),
    ('IL-FISS-ORMV12.5 Pro mini', 'MV12.5 Pro mini', 12.5, 500,  500,  8.3,   135, 0, 1, 1, 0),
    -- 7,81 mm Familie
    ('IL-FISS-ORMV7.8',           'MV7.8',           7.81, 1000, 1000, 19,    660, 0, 1, 1, 0),
    ('IL-FISS-ORMV7.8 mini',      'MV7.8 mini',      7.81, 500,  500,  8.1,   165, 0, 1, 1, 0),
    ('IL-FISS-ORMV7.8 Pro',       'MV7.8 Pro',       7.81, 1000, 1000, 19,    630, 0, 1, 1, 0),
    ('IL-FISS-ORMV7.8 Pro mini',  'MV7.8 Pro mini',  7.81, 500,  500,  8.1,   158, 0, 1, 1, 0),
    ('IL-FISS-ORMV7.8 Max',       'MV7.8 Max',       7.81, 1000, 1000, 19,    640, 0, 1, 1, 0),
    ('IL-FISS-ORMV7.8 Max mini',  'MV7.8 Max mini',  7.81, 500,  500,  8.1,   160, 0, 1, 1, 0),
    -- 5,95 mm Familie
    ('IL-FISS-ORMV5.9',           'MV5.9',           5.95, 1000, 1000, 19.88, 660, 0, 1, 1, 0),
    ('IL-FISS-ORMV5.9 mini',      'MV5.9 mini',      5.95, 500,  500,  8.8,   165, 0, 1, 1, 0),
    ('IL-FISS-ORMV5.9 Pro',       'MV5.9 Pro',       5.95, 1000, 1000, 19.88, 660, 0, 1, 1, 0),
    ('IL-FISS-ORMV5.9 Pro mini',  'MV5.9 Pro mini',  5.95, 500,  500,  8.8,   165, 0, 1, 1, 0),
    ('IL-FISS-ORMV5.9 Max',       'MV5.9 Max',       5.95, 1000, 1000, 19.88, 600, 0, 1, 1, 0),
    ('IL-FISS-ORMV5.9 Max mini',  'MV5.9 Max mini',  5.95, 500,  500,  8.8,   150, 0, 1, 1, 0),
    -- 2,97 mm Familie
    ('IL-FISS-ORMV2.9',           'MV2.9',           2.97, 1000, 1000, 19.6,  660, 0, 1, 1, 0),
    ('IL-FISS-ORMV2.9 mini',      'MV2.9 mini',      2.97, 500,  500,  8.3,   165, 0, 1, 1, 0),
    ('IL-FISS-ORMV2.9 Pro',       'MV2.9 Pro',       2.97, 1000, 1000, 19.6,  600, 0, 1, 1, 0),
    ('IL-FISS-ORMV2.9 Pro mini',  'MV2.9 Pro mini',  2.97, 500,  500,  8.3,   150, 0, 1, 1, 0);

INSERT INTO configurator_product_article (configurator_product_id, article_catalog_mock_id)
SELECT
    (SELECT id FROM configurator_product WHERE name = 'INFiLED MV Series'),
    ac.id
FROM article_catalog_mock ac
WHERE ac.article_number IN
    ('IL-FISS-ORMV12.5', 'IL-FISS-ORMV12.5 mini', 'IL-FISS-ORMV12.5 Pro', 'IL-FISS-ORMV12.5 Pro mini',
     'IL-FISS-ORMV7.8', 'IL-FISS-ORMV7.8 mini', 'IL-FISS-ORMV7.8 Pro', 'IL-FISS-ORMV7.8 Pro mini',
     'IL-FISS-ORMV7.8 Max', 'IL-FISS-ORMV7.8 Max mini',
     'IL-FISS-ORMV5.9', 'IL-FISS-ORMV5.9 mini', 'IL-FISS-ORMV5.9 Pro', 'IL-FISS-ORMV5.9 Pro mini',
     'IL-FISS-ORMV5.9 Max', 'IL-FISS-ORMV5.9 Max mini',
     'IL-FISS-ORMV2.9', 'IL-FISS-ORMV2.9 mini', 'IL-FISS-ORMV2.9 Pro', 'IL-FISS-ORMV2.9 Pro mini');
