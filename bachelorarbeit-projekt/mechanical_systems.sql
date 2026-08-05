-- Fremdschluessel muessen in SQLite pro Verbindung aktiviert werden
PRAGMA foreign_keys = ON;

-- Tabelle fuer die mechanischen Systeme (z.B. Standard-Stacking, Flugrahmen, ...)
CREATE TABLE mechanical_systems (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT NOT NULL,           -- z.B. 'Standard-Stacking'
    default_clamp_type TEXT,                    -- z.B. 'Quick-Clamp'
    default_base_type  TEXT                     -- z.B. 'Ground-Support'
);

-- Verknuepfungstabelle: welches Produkt nutzt welches mechanische System
CREATE TABLE product_mechanics (
    product_id INTEGER NOT NULL,
    system_id  INTEGER NOT NULL,
    PRIMARY KEY (product_id, system_id),
    FOREIGN KEY (product_id) REFERENCES article_catalog_mock (id)
        ON DELETE CASCADE,
    FOREIGN KEY (system_id) REFERENCES mechanical_systems (id)
        ON DELETE CASCADE
);

-- Beispiel-System anlegen
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type)
VALUES ('Standard-Stacking', 'Quick-Clamp', 'Ground-Support');

-- Beispiel-Verknuepfung: 'AURA' (article_catalog_mock) mit 'Standard-Stacking' verbinden
-- Ueber Subqueries, damit die konkreten IDs nicht per Hand nachgeschlagen werden muessen
INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'AURA'),
    (SELECT id FROM mechanical_systems WHERE name = 'Standard-Stacking');

-- Hanging-Truss-System: nutzt dieselbe 3-2-1 Breiten-Verteilung wie
-- Standard-Stacking, aber ohne Stacker/Clamps (haengt an einem Traversen-
-- system statt auf Basements zu stehen)
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type)
VALUES ('Hanging-Truss', NULL, 'Truss-Support');

INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'AURA'),
    (SELECT id FROM mechanical_systems WHERE name = 'Hanging-Truss');

-- Wandadapter-System: nutzt ebenfalls die 3-2-1 Breiten-Verteilung fuer die
-- Basements, aber ohne Footbeam/Single-Foot/Stacker/Clamp - die Wand haengt
-- stattdessen ueber Wandadapter direkt an der Wand
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type)
VALUES ('Wandadapter', NULL, 'Wall-Support');

INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'AURA'),
    (SELECT id FROM mechanical_systems WHERE name = 'Wandadapter');

-- NoBase-System: keine Basements. Fuer die unteren zwei Cabinet-Reihen
-- traegt stattdessen ein eigenstaendiges NoBase-System (Footbeam direkt am
-- Boden + NoBase-Stacker als Uebergangsstueck mit einer Clamp). Ab der
-- dritten Reihe wird das normale Standard-Stacker/Clamp-System fortgesetzt.
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type)
VALUES ('NoBase', 'Quick-Clamp', 'NoBase-Support');

INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'AURA'),
    (SELECT id FROM mechanical_systems WHERE name = 'NoBase');

-- ARUNA, LUGH und MERI 500x500 folgen mechanisch exakt dem Aura-Konzept
-- (3-Punkt-Sicherung bei NoBase, Clamp-Trennung, Ausleger/Diagonalen-
-- Koppelung etc.) - deshalb werden sie an dieselben vier mechanischen
-- Systeme angebunden wie AURA. Die individuellen Statik-Grenzwerte
-- (maxStackingHeight, Hanging-Oesen-Limits) werden trotzdem separat pro
-- Produkt in server.py hinterlegt (siehe MAX_STACKING_HEIGHT_BY_PRODUCT /
-- HANGING_OESEN_LIMITS_BY_PRODUCT) - aktuell noch Platzhalterwerte, echte
-- Datenblatt-Werte muessen von der LANG AG geliefert werden.
INSERT INTO product_mechanics (product_id, system_id)
SELECT ac.id, ms.id
FROM article_catalog_mock ac
CROSS JOIN mechanical_systems ms
WHERE ac.name IN ('ARUNA', 'LUGH', 'MERI 500x500');

-- Vanish-Stacking-System: eigenstaendiger, in sich geschlossener Baukasten
-- fuer den Vanish V8T. Statisch/hardwareseitig vollstaendig getrennt vom
-- Aura-Konzept - KEINE Verknuepfung mit Ausleger/Diagonale/Pipe/
-- Rohrschellen (Aura-Zubehoer-Logik) oder den Aura-Statik-Hoehengrenzen.
-- Genau 7 Bauteile (Stacking Bar, Foot Beam, Unterster Stacker, Stacker,
-- Verbinder ROE-V8TRC, Splint ROE-XXXTRSPRINGM, Klammer ROE-XXXTSPIGOTM),
-- siehe _calculate_vanish_mechanics in server.py.
INSERT INTO mounting_type (name)
SELECT 'Vanish-Stacking'
WHERE NOT EXISTS (SELECT 1 FROM mounting_type WHERE name = 'Vanish-Stacking');

INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type)
VALUES ('Vanish-Stacking', 'ROE-XXXTSPIGOTM', 'Vanish-Support');

-- Exklusive Verknuepfung: nur Vanish V8T nutzt dieses System - bewusst
-- keine Vermischung mit den vier Aura-Systemen.
INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'Vanish V8T'),
    (SELECT id FROM mechanical_systems WHERE name = 'Vanish-Stacking');

-- Modus-Vereinheitlichung: 'Stacking' und 'Hanging' sind feste,
-- produktunabhaengige UI-Buttons; 'Wall-Adapter' bleibt als dritter,
-- eigenstaendiger Button bestehen. Welche Systeme sich hinter einem Button
-- verbergen, haengt vom Produkt ab (siehe /api/mechanics-options in
-- server.py) - z.B. bietet 'Stacking' bei der Aura-Familie eine Wahl
-- zwischen Standard-Stacking und NoBase, bei Vanish V8T dagegen exklusiv
-- Vanish-Stacking (kein NoBase/Wandadapter, siehe product_mechanics oben).
ALTER TABLE mechanical_systems ADD COLUMN ui_mode TEXT;

UPDATE mechanical_systems SET ui_mode = 'Stacking'
WHERE name IN ('Standard-Stacking', 'NoBase', 'Vanish-Stacking');
UPDATE mechanical_systems SET ui_mode = 'Hanging' WHERE name = 'Hanging-Truss';
UPDATE mechanical_systems SET ui_mode = 'Wall-Adapter' WHERE name = 'Wandadapter';

-- 'No-Base' und 'Vanish-Stacking' waren bisher eigene Top-Level-Eintraege
-- in mounting_type - sie sind jetzt Sub-Optionen innerhalb des
-- 'Stacking'-Modus (aufgeloest ueber ui_mode + product_mechanics) und
-- werden hier entfernt. mounting_type enthaelt danach nur noch die drei
-- festen UI-Buttons.
DELETE FROM mounting_type WHERE name IN ('No-Base', 'Vanish-Stacking');

-- Vanish-Hanging: finaler, exklusiver Hanging-Modus fuer Vanish V8T.
-- ui_mode 'Hanging' ordnet es demselben festen UI-Button zu wie die
-- Aura-Oesen-Logik (Hanging-Truss), OHNE die Berechnung zu vermischen -
-- exakt eine Stueckliste-Position (Hanging Bar = Breite B), alle
-- Stacking-Bauteile (Stacker/Klammern/Splinte/Verbinder/...) sind hier
-- strukturell nicht vorhanden. Siehe _calculate_vanish_hanging_mechanics
-- in server.py.
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type, ui_mode)
VALUES ('Vanish-Hanging', NULL, 'Vanish-Hanging-Support', 'Hanging');

-- Exklusive Verknuepfung: nur Vanish V8T nutzt dieses System.
INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'Vanish V8T'),
    (SELECT id FROM mechanical_systems WHERE name = 'Vanish-Hanging');

-- LIAM-Truss-System: eigenstaendiges Hanging-Only-System fuer LIAM (siehe
-- liam_truss.py). Kein Stacking - LIAM wird bewusst an KEIN Standard-
-- Stacking/NoBase/Wandadapter-System angebunden, nur an dieses eine
-- Hanging-System. "Vollstaendiges Gitter": B vertikale Linien (Laenge H)
-- UND pro Ebene (aus H + Indoor/Outdoor-Raster) eine horizontale Linie
-- (Laenge B), je per Greedy-Laengenoptimierung (2m/1m-Module) zerlegt.
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type, ui_mode)
VALUES ('LIAM-Truss', NULL, 'Truss-Support', 'Hanging');

-- Exklusive Verknuepfung: nur LIAM nutzt dieses System.
INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'LIAM'),
    (SELECT id FROM mechanical_systems WHERE name = 'LIAM-Truss');

-- LUNA: ausschliesslich im Modus 'Hanging' verfuegbar - kein Stacking,
-- kein NoBase, kein Wandadapter. Entfernt vorsorglich jede evtl.
-- vorhandene Verknuepfung zu diesen Systemen, bevor die exklusive
-- Hanging-Verknuepfung angelegt wird.
DELETE FROM product_mechanics
WHERE product_id = (SELECT id FROM article_catalog_mock WHERE name = 'LUNA')
  AND system_id IN (
      SELECT id FROM mechanical_systems
      WHERE name IN ('Standard-Stacking', 'NoBase', 'Wandadapter', 'Vanish-Stacking')
  );

-- Luna-Hanging-System: gleiches 1:1-Modell wie Vanish-Hanging - exakt eine
-- Stueckliste-Position (Hanging Bar = Breite B, 1x pro vertikaler Linie),
-- Hoehe (H) hat keinen Einfluss. Siehe
-- _calculate_luna_hanging_mechanics in server.py.
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type, ui_mode)
VALUES ('Luna-Hanging', NULL, 'Luna-Hanging-Support', 'Hanging');

-- Exklusive Verknuepfung: nur LUNA nutzt dieses System.
INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'LUNA'),
    (SELECT id FROM mechanical_systems WHERE name = 'Luna-Hanging');

-- Harmonisierung: AURA, ARUNA und LUNA nutzen fuer den Modus 'Hanging' ab
-- sofort exakt dieselben statischen Grenzwerte UND dieselbe
-- 3-2-1-Basement-Stueckliste - das eigene 1:1-Modell von LUNA
-- (Luna-Hanging, siehe oben) entfaellt deshalb wieder. LUNA haengt jetzt an
-- genau demselben mechanical_systems-Eintrag wie AURA/ARUNA/LUGH/MERI
-- 500x500 (Hanging-Truss). Statik-Grenzwerte kommen ab sofort einheitlich
-- aus _get_hanging_statics() in server.py statt aus produktindividuellen
-- Dict-Eintraegen - AURA und ARUNA referenzieren im Code dieselbe Funktion.
DELETE FROM product_mechanics
WHERE product_id = (SELECT id FROM article_catalog_mock WHERE name = 'LUNA')
  AND system_id = (SELECT id FROM mechanical_systems WHERE name = 'Luna-Hanging');

DELETE FROM mechanical_systems WHERE name = 'Luna-Hanging';

INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'LUNA'),
    (SELECT id FROM mechanical_systems WHERE name = 'Hanging-Truss');

-- AR-Stacking-System (AR3.9, Produkt AR3.91 Plus LE): uebernimmt die
-- komplette Aura-Logik 1:1 (Interlocks/Clamp-Regel, 3-2-1-Basement-
-- Verteilung, Zubehoer-Auswahl, statische Hoehen-Limits). Einzige
-- Abweichung (Ruecksprache): der Stacker hat exakt die Grundflaeche eines
-- Cabinets statt wie beim Aura-Konzept variabel ueber 2 Cabinets zu
-- greifen - das Basis-Raster (Stacking-Base/Stacking-Foot, Aequivalent zum
-- Aura-Footbeam) ist deshalb 1:1 zum Cabinet-Raster. Siehe
-- _calculate_ar_stacking_mechanics in server.py.
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type, ui_mode)
VALUES ('AR-Stacking', 'Quick-Clamp', 'Ground-Support', 'Stacking');

-- Exklusive Verknuepfung: nur AR3.91 Plus LE nutzt dieses System.
INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'AR3.91 Plus LE'),
    (SELECT id FROM mechanical_systems WHERE name = 'AR-Stacking');

-- AR-Hanging-System (AR3.9): dasselbe 1:1-Hanging-Bar-Modell wie gewohnt
-- (siehe Vanish-Hanging oben) - genau eine Stueckliste-Position (Hanging
-- Bar = Breite B, 1x pro vertikaler Linie), Hoehe (H) hat keinen Einfluss.
-- Siehe _calculate_ar_hanging_mechanics in server.py.
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type, ui_mode)
VALUES ('AR-Hanging', NULL, 'AR-Hanging-Support', 'Hanging');

-- Exklusive Verknuepfung: nur AR3.91 Plus LE nutzt dieses System.
INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM article_catalog_mock WHERE name = 'AR3.91 Plus LE'),
    (SELECT id FROM mechanical_systems WHERE name = 'AR-Hanging');

-- AURA FLEX und LUNA bekommen zusaetzlich das NoBase-System (Ruecksprache:
-- "Statik und Aufbau sind exakt gleich wie Aura"). Physisch identisch zur
-- Aura-NoBase-Konfiguration - NoBase kennt keine Basements (der einzige
-- Flex-spezifische Unterschied waere ohnehin die Basement-Bauform), und
-- Footbeam/Stacker/Clamp nutzen bei Flex bereits dieselbe generische Formel
-- wie Aura (siehe _calculate_aura_flex_mechanics/_calculate_nobase_
-- mechanics in server.py) - deshalb keine eigene "Flex-NoBase"-Variante,
-- sondern direkte Anbindung an das bestehende, generische NoBase-System.
-- LUNA war zuvor exklusiv auf 'Hanging' beschraenkt (siehe oben) - diese
-- eine Verknuepfung durchbricht das bewusst, alle uebrigen Aura-Systeme
-- (Standard-Stacking/Wandadapter/Vanish-Stacking) bleiben fuer LUNA
-- weiterhin nicht verknuepft.
INSERT INTO product_mechanics (product_id, system_id)
SELECT ac.id, (SELECT id FROM mechanical_systems WHERE name = 'NoBase')
FROM article_catalog_mock ac
WHERE ac.name IN ('AURA FLEX', 'LUNA');
