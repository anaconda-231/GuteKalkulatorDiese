-- Tabelle komplett zurücksetzen
DROP TABLE IF EXISTS article_catalog_mock;

-- Neue Struktur mit binären Flags (1 = Ja, 0 = Nein)
CREATE TABLE article_catalog_mock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_number TEXT,
    name TEXT,
    pixelpitch_mm REAL,
    is_indoor_capable INTEGER,    -- NEU: Ist Indoor möglich?
    is_outdoor_capable INTEGER,   -- NEU: Ist Outdoor möglich?
    is_fixed_capable INTEGER,     -- NEU: Ist Festinstallation möglich?
    is_temporary_capable INTEGER, -- NEU: Ist temporärer Einsatz möglich?
    weight_kg REAL
);

-- Daten mit den korrekten Berechtigungen befüllen
-- Wir schauen dazu in deine PDF-Datenblätter
INSERT INTO article_catalog_mock (article_number, name, pixelpitch_mm, is_indoor_capable, is_outdoor_capable, is_fixed_capable, is_temporary_capable, weight_kg) VALUES
('LANG-001', 'AR3.91 Plus LE', 3.91, 1, 1, 1, 1, 14.3),
('LANG-002', 'ARUNA', 1.95, 1, 1, 1, 1, 9.8),
('LANG-003', 'AURA', 1.5, 1, 0, 1, 1, 8.7),
('LANG-004', 'ENKI', 0.9375, 1, 0, 1, 1, 7.2),
('LANG-005', 'JUPITER', 1.58, 1, 0, 1, 1, 9.2),
('LANG-006', 'LEDGEND', 0.9375, 1, 0, 1, 0, 6.0), -- Nur Fest, kein Temporär!
('LANG-007', 'LIAM', 6.25, 1, 1, 1, 1, 12.0),
('LANG-008', 'LUGH', 2.6, 1, 0, 1, 1, 8.8),
('LANG-009', 'LUNA', 1.93, 1, 0, 1, 1, 9.2),
('LANG-010', 'VENUS', 1.27, 1, 0, 1, 1, 9.2);

-- Tabelle für die Montagearten
CREATE TABLE mounting_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL -- z.B. 'Stacking', 'Hanging', 'Wall-Adapter', 'No-Base'
);

INSERT INTO mounting_type (name) VALUES ('Stacking'), ('Hanging'), ('Wall-Adapter'), ('No-Base');