-- Gemischte Wandhoehe: volle Cabinets + ein halbes Cabinet obenauf
-- (Ruecksprache LANG AG: "Wenn man bei Avora, Meri, Avora Root, AR3.9
-- 1000x500 die Zahl 1,5 / 2,5 etc eintraegt, wird ganz normal gestackt und
-- das oberste Cabinet mit einem 500x500 aufgebaut. Die oberste Reihe braucht
-- keinen Stacker und keine Clamp.")
--
-- Statt das halbe Cabinet im Code fest zu verdrahten, bekommt jedes
-- 1000er-Panel einen Verweis auf sein 500er-Gegenstueck. Damit kennt das
-- Frontend dessen echte Werte (Gewicht, Leistung, Pixelhoehe) und kann eine
-- gemischte Wand korrekt aufsummieren, statt das halbe Cabinet zu schaetzen.
-- NULL = Produkt hat kein halbes Cabinet, dort bleibt die Hoehe wie bisher
-- eine ganze Cabinet-Anzahl.
PRAGMA foreign_keys = ON;

ALTER TABLE article_catalog_mock ADD COLUMN half_cabinet_article_id INTEGER
    REFERENCES article_catalog_mock (id);

UPDATE article_catalog_mock
SET half_cabinet_article_id = (
    SELECT half.id FROM article_catalog_mock half
    WHERE half.name = article_catalog_mock.name || ' 500x500'
)
WHERE name IN ('AR3.91 Plus LE', 'Avora', 'Avora Root');

-- MERI hat sein halbes Cabinet schon lange als eigenes Produkt im Katalog
-- ('MERI 500x500'), nur ohne Verweis - deshalb hier separat.
UPDATE article_catalog_mock
SET half_cabinet_article_id = (SELECT id FROM article_catalog_mock WHERE name = 'MERI 500x500')
WHERE name = 'MERI 500x1000';
