-- Aura Flex (LANG-016, article_catalog_mock.id = 16, configurator_product
-- "AURA FLEX Config", id = 16): eigenes Stacking-System, das NICHT der
-- 3-2-1-Basement-Optimierung der uebrigen Aura-Familie folgt. Statt
-- Basements in den Breiten 3/2/1 Cabinets gibt es bei Flex nur einen
-- einzigen Basement-Typ mit fester Breite 0,5 Cabinets, der an jeder
-- Schnittstelle zwischen zwei benachbarten Cabinets sitzt (siehe
-- _calculate_aura_flex_mechanics in server.py). Nur der Stacking-Modus wird
-- angebunden - kein Hanging/Wandadapter/NoBase fuer dieses Produkt.
INSERT INTO mechanical_systems (name, default_clamp_type, default_base_type, ui_mode)
VALUES ('Flex-Stacking', 'Quick-Clamp', 'Flex-Support', 'Stacking');

INSERT INTO product_mechanics (product_id, system_id)
SELECT
    (SELECT id FROM configurator_product WHERE name = 'AURA FLEX Config'),
    (SELECT id FROM mechanical_systems WHERE name = 'Flex-Stacking');
