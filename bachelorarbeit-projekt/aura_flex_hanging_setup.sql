-- Aura Flex Hanging (LANG-016, article_catalog_mock.id = 16, configurator_
-- product "AURA FLEX Config", id = 16): eigenes Hanging-System, analog zu
-- Flex-Stacking bewusst NICHT ueber die 3-2-1-Hanging-Truss-Modul-
-- Verteilung. Es gibt nur einen einzigen Truss-Typ ("Aura Truss"), der
-- zwischen jeweils 2 benachbarten Cabinets befestigt wird - kein laengeres
-- Modul verfuegbar (siehe _calculate_aura_flex_hanging_mechanics in
-- server.py). Statische Maximalhoehe identisch zu AURA.
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type, ui_mode)
VALUES ('Flex-Hanging', NULL, 'Flex-Truss-Support', 'Hanging');

INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM configurator_product WHERE name = 'AURA FLEX Config'),
    (SELECT id FROM mechanical_systems WHERE name = 'Flex-Hanging');
