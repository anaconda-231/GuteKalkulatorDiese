-- Echte Datenblattwerte fuer die halben Cabinets (500x500) von AR3.9,
-- Avora und Avora Root (Ruecksprache LANG AG) - ersetzt die Platzhalter
-- (halbierte 1000er-Werte) aus ar_avora_500x500_setup.sql:
--   Gewicht                9,4 kg je Cabinet
--   Leistung maximal     180 W je Cabinet
--   Leistung Durchschnitt 60 W je Cabinet
--
-- Zwei neue Spalten, weil der Katalog beides bisher nicht kannte:
--   avg_power_consumption_w  Durchschnittsleistung. Bewusst NICHT fuer die
--     Auslegung verwendet - Stromkreise und Gesamtleistung rechnen weiterhin
--     mit dem Maximalwert (siehe POWER_CIRCUIT_WATT_CAPACITY im Frontend),
--     alles andere waere elektrisch nicht zulaessig. Der Wert wird nur
--     zusaetzlich ausgewiesen.
--   note  Freitext-Bemerkung zum Produkt, wird in den Produktdaten und im
--     PDF-Bericht angezeigt.
--
-- NULL bei allen uebrigen Produkten bedeutet schlicht "kein Wert bzw. keine
-- Bemerkung hinterlegt" - dort aendert sich nichts.
PRAGMA foreign_keys = ON;

ALTER TABLE article_catalog_mock ADD COLUMN avg_power_consumption_w INTEGER;
ALTER TABLE article_catalog_mock ADD COLUMN note TEXT;

UPDATE article_catalog_mock
SET weight_kg = 9.4,
    max_power_consumption_w = 180,
    avg_power_consumption_w = 60
WHERE id IN (79, 80, 81);   -- AR3.91 Plus LE / Avora / Avora Root, je 500x500

-- Avora ist laut Ruecksprache noch nicht final; die uebernommenen Werte sind
-- dort nur eine Schaetzung und muessen als solche erkennbar sein.
UPDATE article_catalog_mock
SET note = 'Avora ist noch nicht final – die hinterlegten Werte sind eine Schätzung und noch nicht datenblattgesichert.'
WHERE id = 80;   -- Avora 500x500
