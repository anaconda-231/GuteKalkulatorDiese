PRAGMA foreign_keys = ON;

-- RX-Serie (Regience): eine Serie, zwei Umgebungsvarianten (Indoor "i" /
-- Outdoor "d") je Pixelpitch - modelliert als 12 einzelne Modelle unter
-- EINER Serie (configurator_product_article, siehe wp_series_setup.sql).
-- is_indoor_capable/is_outdoor_capable trennen die beiden Varianten pro
-- Modell, wodurch der bestehende location-Filter in /api/product-models
-- automatisch die richtigen 6 Pixelpitches zeigt, je nachdem ob "Indoor"
-- oder "Outdoor" als Einsatzort gewaehlt ist - keine zwei separaten Serien
-- noetig.
-- Ruecksprache: die Serie->Modell-Kaskade (Serie waehlen, dann Modell/
-- Pixelpitch) existiert bislang exklusiv fuer Festinstallation - die alte,
-- flache Produktliste im temporaeren Einsatz kann nur ein Modell pro
-- Produkt darstellen und koennte die 6 Pixelpitches der RX-Serie nicht
-- sauber unterscheiden. Deshalb ist_temporary_capable = 0 fuer alle 12
-- RX-Modelle (analog zur INFiLED-Wallpaper-Serie) - die RX-Serie
-- erscheint dadurch ausschliesslich unter Festinstallation.
-- Watt/Cabinet errechnet aus Max Power (W/m²) * Cabinetflaeche (0,5 x 0,5m
-- = 0,25 m²): Indoor 520 W/m² -> 130 W/Cabinet fuer alle Pitches; Outdoor
-- 600 W/m² -> 150 W/Cabinet (P1.25-P2.97), 750 W/m² -> 187,5 W/Cabinet
-- (P3.9).
INSERT INTO article_catalog_mock
    (article_number, name, pixelpitch_mm, width_mm, height_mm, weight_kg, max_power_consumption_w,
     is_indoor_capable, is_outdoor_capable, is_fixed_capable, is_temporary_capable)
VALUES
    -- Indoor (RXxxxi)
    ('REG-RX125I', 'RX125i', 1.25, 500, 500, 9.2, 130,   1, 0, 1, 0),
    ('REG-RX156I', 'RX156i', 1.56, 500, 500, 9.2, 130,   1, 0, 1, 0),
    ('REG-RX195I', 'RX195i', 1.95, 500, 500, 9.2, 130,   1, 0, 1, 0),
    ('REG-RX260I', 'RX260i', 2.6,  500, 500, 9.2, 130,   1, 0, 1, 0),
    ('REG-RX297I', 'RX297i', 2.97, 500, 500, 9.2, 130,   1, 0, 1, 0),
    ('REG-RX390I', 'RX390i', 3.9,  500, 500, 9.2, 130,   1, 0, 1, 0),
    -- Outdoor (RXxxxd)
    ('REG-RX125D', 'RX125d', 1.25, 500, 500, 9.2, 150,   0, 1, 1, 0),
    ('REG-RX156D', 'RX156d', 1.56, 500, 500, 9.2, 150,   0, 1, 1, 0),
    ('REG-RX195D', 'RX195d', 1.95, 500, 500, 9.2, 150,   0, 1, 1, 0),
    ('REG-RX260D', 'RX260d', 2.6,  500, 500, 9.2, 150,   0, 1, 1, 0),
    ('REG-RX297D', 'RX297d', 2.97, 500, 500, 9.2, 150,   0, 1, 1, 0),
    ('REG-RX390D', 'RX390d', 3.9,  500, 500, 9.2, 187.5, 0, 1, 1, 0);

INSERT INTO configurator_product (product_article_id, name)
VALUES (NULL, 'RX Series');

INSERT INTO configurator_product_article (configurator_product_id, article_catalog_mock_id)
SELECT
    (SELECT id FROM configurator_product WHERE name = 'RX Series'),
    ac.id
FROM article_catalog_mock ac
WHERE ac.article_number IN
    ('REG-RX125I', 'REG-RX156I', 'REG-RX195I', 'REG-RX260I', 'REG-RX297I', 'REG-RX390I',
     'REG-RX125D', 'REG-RX156D', 'REG-RX195D', 'REG-RX260D', 'REG-RX297D', 'REG-RX390D');
