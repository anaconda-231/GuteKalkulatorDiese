-- Halbe Cabinets (500x500) fuer AR3.9, Avora und Avora Root
-- (Ruecksprache LANG AG: "das sind halbe cabinets aber der Pixelpitch ist der
-- gleiche nur die hoehe ist halbiert").
--
-- Umgesetzt nach dem bestehenden Vorbild im Katalog: 'MERI 500x1000' und
-- 'MERI 500x500' sind zwei getrennte Produkte mit identischem Pixelpitch und
-- halbierter Hoehe. Die drei neuen Eintraege folgen exakt diesem Muster und
-- haengen an denselben mechanischen Systemen wie ihre 1000er-Variante.
--
-- WICHTIG - ID-Konvention: in dieser Datenbank gilt durchgaengig
--   configurator_product.id = configurator_product.product_article_id
--                           = article_catalog_mock.id
--                           = product_mechanics.product_id
-- Ausserdem sind die Statik-Tabellen in server.py ueber genau diese ID
-- verschluesselt (MAX_STACKING_HEIGHT_BY_PRODUCT, NEW_AR_STACKING_PRODUCT_IDS,
-- CURVING_DEGREE_STEPS_BY_PRODUCT, BALLAST_TABLE_BY_PRODUCT). Die IDs werden
-- deshalb explizit vergeben (79/80/81 - in beiden Tabellen frei) statt dem
-- AUTOINCREMENT ueberlassen.
--
-- ACHTUNG Platzhalter: weight_kg und max_power_consumption_w sind hier auf die
-- HAELFTE der 1000er-Variante gesetzt, weil dafuer noch keine Datenblattwerte
-- vorliegen. Beim MERI-Paar ist der reale Faktor NICHT 0,5 (9,8 -> 6,1 kg bzw.
-- 270 -> 150 W), die echten Werte weichen also mit hoher Wahrscheinlichkeit ab
-- und muessen von der LANG AG nachgereicht werden.
PRAGMA foreign_keys = ON;

INSERT INTO article_catalog_mock
    (id, article_number, name, pixelpitch_mm, width_mm, height_mm, weight_kg,
     max_power_consumption_w, is_outdoor_capable, is_temporary_capable,
     is_indoor_capable, is_fixed_capable)
SELECT v.new_id, v.new_article_number, ac.name || ' 500x500',
       ac.pixelpitch_mm, ac.width_mm, ac.height_mm / 2,
       ROUND(ac.weight_kg / 2.0, 2), ac.max_power_consumption_w / 2,
       ac.is_outdoor_capable, ac.is_temporary_capable,
       ac.is_indoor_capable, ac.is_fixed_capable
FROM (
    SELECT 79 AS new_id, 'LANG-021' AS new_article_number, 'AR3.91 Plus LE' AS parent
    UNION ALL SELECT 80, 'LANG-022', 'Avora'
    UNION ALL SELECT 81, 'LANG-023', 'Avora Root'
) v
JOIN article_catalog_mock ac ON ac.name = v.parent
WHERE NOT EXISTS (SELECT 1 FROM article_catalog_mock x WHERE x.id = v.new_id);

-- Als eigenstaendig waehlbares Produkt registrieren (1:1-Pfad ueber
-- product_article_id, den /api/products nutzt) ...
INSERT INTO configurator_product (id, product_article_id, name)
SELECT ac.id, ac.id, ac.name
FROM article_catalog_mock ac
WHERE ac.id IN (79, 80, 81)
  AND NOT EXISTS (SELECT 1 FROM configurator_product cp WHERE cp.id = ac.id);

-- ... und zusaetzlich im Serie/Modell-Pfad, damit beide Auswahlwege dieselben
-- Produkte kennen (so ist es auch bei MERI 500x500 hinterlegt).
INSERT INTO configurator_product_article (configurator_product_id, article_catalog_mock_id)
SELECT ac.id, ac.id
FROM article_catalog_mock ac
WHERE ac.id IN (79, 80, 81)
  AND NOT EXISTS (
      SELECT 1 FROM configurator_product_article cpa
      WHERE cpa.configurator_product_id = ac.id
        AND cpa.article_catalog_mock_id = ac.id
  );

-- Mechanische Systeme 1:1 von der 1000er-Variante uebernehmen: die halbe
-- Bauhoehe aendert nichts daran, WELCHE Systeme moeglich sind (Indoor
-- AR-/Standard-Stacking, Outdoor AR-Outdoor-Stacking, Hanging, Wandadapter).
INSERT INTO product_mechanics (product_id, system_id)
SELECT v.new_id, pm.system_id
FROM (
    SELECT 79 AS new_id, 'AR3.91 Plus LE' AS parent
    UNION ALL SELECT 80, 'Avora'
    UNION ALL SELECT 81, 'Avora Root'
) v
JOIN article_catalog_mock ac ON ac.name = v.parent
JOIN product_mechanics pm ON pm.product_id = ac.id
WHERE NOT EXISTS (
    SELECT 1 FROM product_mechanics x
    WHERE x.product_id = v.new_id AND x.system_id = pm.system_id
);
