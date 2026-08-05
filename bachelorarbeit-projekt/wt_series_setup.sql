PRAGMA foreign_keys = ON;

-- INFiLED WT-Serie (Indoor, exklusiv Festinstallation laut Ruecksprache) -
-- 6 Modelle ueber drei Pixelpitches (0,93 / 1,25 / 1,56 mm), jeweils in
-- zwei LED-Konfigurationen: SSC (Flip chip COB) und SSM (MIP). Cabinet
-- 600x337,5mm identisch bei allen sechs Modellen (wie bei der WP-Serie
-- hier als 337 mm gefuehrt, siehe wp_series_setup.sql). Gewicht (4,5 kg)
-- und Max. Power Consumption (60 W/Panel) sind bei allen sechs Modellen
-- laut Datenblatt identisch - nur Pixelpitch/LED-Konfiguration variieren.
-- is_temporary_capable = 0, is_outdoor_capable = 0 (nur Indoor,
-- Festinstallation, wie die uebrigen exklusiven Serien).
INSERT INTO article_catalog_mock
    (article_number, name, pixelpitch_mm, width_mm, height_mm, weight_kg, max_power_consumption_w,
     is_indoor_capable, is_outdoor_capable, is_fixed_capable, is_temporary_capable)
VALUES
    ('IL-FISS-IRWT0.93-SSC', 'WT0.93 SSC', 0.93, 600, 337, 4.5, 60, 1, 0, 1, 0),
    ('IL-FISS-IRWT0.93-SSM', 'WT0.93 SSM', 0.93, 600, 337, 4.5, 60, 1, 0, 1, 0),
    ('IL-FISS-IRWT1.25-SSC', 'WT1.25 SSC', 1.25, 600, 337, 4.5, 60, 1, 0, 1, 0),
    ('IL-FISS-IRWT1.25-SSM', 'WT1.25 SSM', 1.25, 600, 337, 4.5, 60, 1, 0, 1, 0),
    ('IL-FISS-IRWT1.56-SSC', 'WT1.56 SSC', 1.56, 600, 337, 4.5, 60, 1, 0, 1, 0),
    ('IL-FISS-IRWT1.56-SSM', 'WT1.56 SSM', 1.56, 600, 337, 4.5, 60, 1, 0, 1, 0);

INSERT INTO configurator_product (product_article_id, name)
VALUES (NULL, 'INFiLED WT Series');

INSERT INTO configurator_product_article (configurator_product_id, article_catalog_mock_id)
SELECT
    (SELECT id FROM configurator_product WHERE name = 'INFiLED WT Series'),
    ac.id
FROM article_catalog_mock ac
WHERE ac.article_number IN
    ('IL-FISS-IRWT0.93-SSC', 'IL-FISS-IRWT0.93-SSM',
     'IL-FISS-IRWT1.25-SSC', 'IL-FISS-IRWT1.25-SSM',
     'IL-FISS-IRWT1.56-SSC', 'IL-FISS-IRWT1.56-SSM');
