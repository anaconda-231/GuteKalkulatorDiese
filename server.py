from flask import Flask, jsonify, render_template, request
import math
import os
import sqlite3

from liam_truss import calculate_liam_truss_mechanics

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.cache = {}
DB_PATH = "konfigurator.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    # Vorher wurde die Datei roh per open()/read() zurueckgegeben - dabei
    # lief index.html NIE durch Jinja, wodurch {{ url_for('static', ...) }}
    # (Sidebar-Logo UND PDF-Logo) woertlich als Text an den Browser ging und
    # das Logo nirgends geladen werden konnte. render_template() rendert die
    # Jinja-Ausdruecke korrekt, TEMPLATES_AUTO_RELOAD/jinja_env.cache={} oben
    # sorgen weiterhin dafuer, dass Aenderungen an index.html ohne
    # Server-Neustart sichtbar werden.
    return render_template("index.html")



@app.route("/api/mounting-types")
def get_mounting_types():
    conn = get_db_connection()
    rows = conn.execute("SELECT id, name FROM mounting_type ORDER BY name").fetchall()
    conn.close()

    mounting_types = [dict(row) for row in rows]
    return jsonify(mounting_types)


@app.route("/api/products")
def get_products():
    location = request.args.get("location")  # "indoor" | "outdoor"
    usage = request.args.get("usage")         # "fest" | "temporaer"

    query = """
        SELECT
            cp.id AS product_id,
            cp.name AS product_name,
            ac.article_number,
            ac.name AS article_name,
            ac.pixelpitch_mm,
            ac.width_mm,
            ac.height_mm,
            ac.weight_kg,
            ac.max_power_consumption_w,
            -- Durchschnittsleistung und Produktbemerkung sind nur bei
            -- einzelnen Produkten hinterlegt (siehe
            -- ar_avora_500x500_values.sql) und sonst NULL - das Frontend
            -- blendet die Zeilen dann aus.
            ac.avg_power_consumption_w,
            ac.note,
            -- Halbes Cabinet (500x500) fuer eine gemischte Wandhoehe wie
            -- 2,5 m = 2 volle + 1 halbes Cabinet. NULL, wenn das Produkt kein
            -- halbes Gegenstueck hat - dann bleibt die Hoehe eine ganze
            -- Cabinet-Anzahl. Siehe half_top_row_setup.sql.
            half.id AS half_article_id,
            half.name AS half_article_name,
            half.article_number AS half_article_number,
            half.height_mm AS half_height_mm,
            half.weight_kg AS half_weight_kg,
            half.max_power_consumption_w AS half_max_power_consumption_w
        FROM configurator_product cp
        JOIN article_catalog_mock ac ON cp.product_article_id = ac.id
        LEFT JOIN article_catalog_mock half ON half.id = ac.half_cabinet_article_id
        WHERE 1=1
    """
    # Jede Bedingung filtert nur auf ihrer eigenen Spalte. Ein "Allrounder"-
    # Produkt (is_indoor_capable=1 UND is_outdoor_capable=1) erfüllt so
    # automatisch beide Filter - das ergibt das gewünschte logische ODER,
    # ohne dass Indoor- und Outdoor-Filter sich gegenseitig ausschließen.
    if location == "indoor":
        query += " AND ac.is_indoor_capable = 1"
    elif location == "outdoor":
        query += " AND ac.is_outdoor_capable = 1"

    if usage == "fest":
        query += " AND ac.is_fixed_capable = 1"
    elif usage == "temporaer":
        query += " AND ac.is_temporary_capable = 1"

    query += " ORDER BY cp.name"

    conn = get_db_connection()
    rows = conn.execute(query).fetchall()
    conn.close()

    products = [dict(row) for row in rows]
    return jsonify(products)


# Serie->Modell-Auswahl (exklusiv fuer Festinstallation, siehe
# configurator_product_article in wp_series_setup.sql): eine Serie
# (configurator_product) kann mehrere Modelle/Pixelpitches anbieten
# (article_catalog_mock-Zeilen), statt wie bei /api/products ueber die
# alte 1:1-Spalte product_article_id. /api/product-series liefert die
# waehlbaren Serien, /api/product-models danach die Modelle innerhalb einer
# gewaehlten Serie - beide filtern identisch zu /api/products nach
# location/usage, damit z.B. is_temporary_capable=0-Serien (aktuell die
# INFiLED-Wallpaper-Serie) im temporaeren Einsatz gar nicht erst auftauchen.
@app.route("/api/product-series")
def get_product_series():
    location = request.args.get("location")
    usage = request.args.get("usage")

    query = """
        SELECT DISTINCT
            cp.id AS product_id,
            cp.name AS product_name
        FROM configurator_product cp
        JOIN configurator_product_article cpa ON cpa.configurator_product_id = cp.id
        JOIN article_catalog_mock ac ON ac.id = cpa.article_catalog_mock_id
        WHERE 1=1
    """
    if location == "indoor":
        query += " AND ac.is_indoor_capable = 1"
    elif location == "outdoor":
        query += " AND ac.is_outdoor_capable = 1"

    if usage == "fest":
        query += " AND ac.is_fixed_capable = 1"
    elif usage == "temporaer":
        query += " AND ac.is_temporary_capable = 1"

    query += " ORDER BY cp.name"

    conn = get_db_connection()
    rows = conn.execute(query).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/api/product-models")
def get_product_models():
    product_id = request.args.get("product_id", type=int)
    if product_id is None:
        return jsonify({"error": "product_id ist erforderlich"}), 400

    location = request.args.get("location")
    usage = request.args.get("usage")

    query = """
        SELECT
            cp.id AS product_id,
            cp.name AS product_name,
            ac.id AS article_id,
            ac.article_number,
            ac.name AS article_name,
            ac.pixelpitch_mm,
            ac.width_mm,
            ac.height_mm,
            ac.weight_kg,
            ac.max_power_consumption_w,
            -- Durchschnittsleistung und Produktbemerkung sind nur bei
            -- einzelnen Produkten hinterlegt (siehe
            -- ar_avora_500x500_values.sql) und sonst NULL - das Frontend
            -- blendet die Zeilen dann aus.
            ac.avg_power_consumption_w,
            ac.note,
            -- Halbes Cabinet (500x500) fuer eine gemischte Wandhoehe wie
            -- 2,5 m = 2 volle + 1 halbes Cabinet. NULL, wenn das Produkt kein
            -- halbes Gegenstueck hat - dann bleibt die Hoehe eine ganze
            -- Cabinet-Anzahl. Siehe half_top_row_setup.sql.
            half.id AS half_article_id,
            half.name AS half_article_name,
            half.article_number AS half_article_number,
            half.height_mm AS half_height_mm,
            half.weight_kg AS half_weight_kg,
            half.max_power_consumption_w AS half_max_power_consumption_w
        FROM configurator_product cp
        JOIN configurator_product_article cpa ON cpa.configurator_product_id = cp.id
        JOIN article_catalog_mock ac ON ac.id = cpa.article_catalog_mock_id
        LEFT JOIN article_catalog_mock half ON half.id = ac.half_cabinet_article_id
        WHERE cp.id = ?
    """
    params = [product_id]

    if location == "indoor":
        query += " AND ac.is_indoor_capable = 1"
    elif location == "outdoor":
        query += " AND ac.is_outdoor_capable = 1"

    if usage == "fest":
        query += " AND ac.is_fixed_capable = 1"
    elif usage == "temporaer":
        query += " AND ac.is_temporary_capable = 1"

    query += " ORDER BY ac.pixelpitch_mm"

    conn = get_db_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


def _product_uses_system(conn, product_id, system_name):
    row = conn.execute(
        """
        SELECT 1
        FROM product_mechanics pm
        JOIN mechanical_systems ms ON ms.id = pm.system_id
        WHERE pm.product_id = ? AND ms.name = ?
        """,
        (product_id, system_name),
    ).fetchone()
    return row is not None


def _optimal_basements(width_cabinets):
    # Fuellt die verbleibende Luecke iterativ von links: immer das groesste
    # Basement setzen, das noch hineinpasst. Eine Luecke von genau 4 waere
    # per Greedy 3+1 - das wuerde ein vermeidbares 1er-Basement erzeugen,
    # obwohl 2+2 die Luecke ohne Rest fuellt. Deshalb wird bei einer
    # verbleibenden Luecke von 4 bewusst auf zwei 2er ausgewichen, statt
    # bedingungslos das groesste Stueck (3er) zu setzen.
    basements_3 = basements_2 = basements_1 = 0
    rest = width_cabinets

    while rest > 0:
        if rest == 4:
            basements_2 += 2
            rest = 0
        elif rest >= 3:
            basements_3 += 1
            rest -= 3
        elif rest == 2:
            basements_2 += 1
            rest = 0
        else:  # rest == 1: kein groesseres Basement passt mehr hinein
            basements_1 += 1
            rest = 0

    return basements_3, basements_2, basements_1


def _apply_curving_width_split(width_cabinets, curving_mode):
    # Im Curving-Modus (Concave/Convex) muss jede Basement-/Truss-Einheit
    # exakt Breite 1 haben, weil an jeder Fuge unabhaengig geknickt werden
    # koennen muss - die 3-2-1-Optimierung (_optimal_basements) entfaellt
    # deshalb vollstaendig zugunsten von width_cabinets Einzel-Segmenten.
    if curving_mode in ("concave", "convex"):
        return 0, 0, width_cabinets
    return _optimal_basements(width_cabinets)


# Ab dieser Wandhoehe (in Cabinets) ist Stacking statisch nicht mehr
# vertretbar - der Aufbau wird komplett blockiert (siehe calculate_mechanics).
# Gilt identisch fuer Standard-Stacking UND NoBase - beide teilen sich
# dieselbe Statik-Hardware-Logik (Ausleger, Diagonale, Pipe, Rohrschellen),
# siehe _calculate_stacking_accessories. Der Grenzwert selbst ist pro Produkt
# hinterlegt (jedes Produkt hat sein eigenes Datenblatt-Limit), die Auswahl-
# Logik der Statik-Hardware anhand der Hoehe ist fuer alle Produkte identisch
# ("Aura-Konzept").
# Platzhalterwerte: ARUNA, LUGH und MERI 500x500 folgen mechanisch exakt dem
# Aura-Konzept, echte Datenblatt-Grenzwerte liegen aber noch nicht vor - bis
# dahin wird hier der AURA-Wert uebernommen. Muss durch die LANG AG bestaetigt
# bzw. korrigiert werden.
MAX_STACKING_HEIGHT_BY_PRODUCT = {
    3: 12,   # AURA
    2: 12,   # ARUNA (Platzhalter, = AURA-Wert)
    8: 12,   # LUGH (Platzhalter, = AURA-Wert)
    18: 12,  # MERI 500x500 (Platzhalter, = AURA-Wert)
    # LUNA: neu an NoBase angebunden (Ruecksprache: "Statik und Aufbau
    # exakt gleich wie Aura") - identischer Grenzwert, keine eigenen
    # Datenblatt-Abweichungen bekannt.
    9: 12,   # LUNA (NoBase)
    # AR3.91 Plus LE: dieser Wert (12) gilt jetzt nur noch als Outdoor-/
    # Fallback-Grenze - Indoor wird durch NEW_AR_STACKING_INDOOR_MAX_HEIGHT
    # (6, echte Statiktabelle) ueberschrieben, siehe calculate_mechanics.
    # Outdoor hat laut Ruecksprache eine eigene, noch nicht hinterlegte
    # Statik - bis dahin bleibt hier der alte Platzhalterwert stehen.
    1: 12,   # AR3.91 Plus LE (AR-Stacking)
    # Neu an Standard-Stacking/AR-Stacking angebunden fuers Curving-Feature
    # (siehe curving_setup.sql) - noch keine eigenen Datenblatt-Werte,
    # deshalb ebenfalls Platzhalter = AURA-Wert. Muss durch die LANG AG
    # bestaetigt bzw. korrigiert werden.
    # JUPITER/VENUS: echter Datenblatt-Wert (Ruecksprache) - 18 Cabinets,
    # siehe _calculate_venus_jupiter_stacking_accessories fuer die
    # zugehoerigen (von Aura abweichenden) Ausleger/Diagonale/Pipe-Schwellen.
    5: 18,   # JUPITER
    10: 18,  # VENUS
    17: 12,  # MERI 500x1000 (Platzhalter, = AURA-Wert)
    # AR 10.41: wie bei AR3.91 Plus LE nur noch Outdoor-/Fallback-Grenze,
    # Indoor siehe NEW_AR_STACKING_INDOOR_MAX_HEIGHT.
    12: 12,  # AR 10.41 (AR-Stacking)
    # Avora/Avora Root: echter Datenblatt-Wert (Datasheet_AVORA_rev5.pdf,
    # "Max. Overall height (hanging/standing): 18 Cabinets / 6 Cabinets") -
    # 6 Cabinets fuer den stehenden/gestapelten Aufbau. Beide Produkte sind
    # laut Ruecksprache dasselbe physische Panel, das sich nur in der
    # Montageart unterscheidet, deshalb identischer Wert. Avora Root nutzt
    # zusaetzlich (Ruecksprache: "hat die AR Statik") die neue AR-
    # Zubehoer-Kaskade fuer Indoor (NEW_AR_STACKING_PRODUCT_IDS) - deckt
    # sich hier zufaellig mit demselben Hoehenwert (6), Avora (ohne Root)
    # NICHT.
    19: 6,   # Avora
    20: 6,   # Avora Root
    # ENKI: echter Datenblatt-Wert (Ruecksprache) - 18 Cabinets, siehe
    # _calculate_enki_stacking_accessories fuer die zugehoerigen (von Aura
    # abweichenden) Ausleger/Diagonale/Pipe-Schwellen.
    4: 18,   # ENKI
    # AURA FLEX: dasselbe physische Cabinet wie AURA (siehe article_catalog_
    # mock, identische Massse), nur mit abweichender Basement-Bauform -
    # statisch darf Flex deshalb exakt so hoch gebaut werden wie normales
    # AURA, identischer Grenzwert.
    16: 12,  # AURA FLEX
    # Halbe Cabinets (500x500) von AR3.9/Avora/Avora Root: der Grenzwert der
    # 1000er-Variante ist eine BAUHOEHE, keine Stueckzahl - bei halber
    # Cabinet-Hoehe passen deshalb doppelt so viele Cabinets in dieselbe
    # zulaessige Hoehe (AR3.91/Avora Root 6 Cabinets = 6 m -> 12 halbe,
    # Avora ebenso). Siehe ar_avora_500x500_setup.sql.
    79: 12,  # AR3.91 Plus LE 500x500
    80: 12,  # Avora 500x500
    81: 12,  # Avora Root 500x500
}
STACKING_HEIGHT_LIMIT_ERROR = (
    "Dieser Aufbau ist bei dieser Wandhöhe nicht umsetzbar. "
    "Bitte wenden Sie sich für Sonderlösungen an die LANG AG."
)

# Curving (Concave/Convex): nur die vier Systeme mit 3-2-1-Breitenlogik
# (Basements bzw. Hanging-Truss-Module) koennen ueberhaupt auf Breite-1-
# Segmente umgestellt werden - NoBase/Wandadapter/Vanish-* bleiben ohne
# Curving-Option. LIAM-Truss hat eine eigene, additive Curving-Erweiterung
# (siehe liam_truss.py) und wird deshalb hier bewusst NICHT gelistet.
CURVING_CAPABLE_SYSTEMS = {"Standard-Stacking", "AR-Stacking", "Hanging-Truss", "AR-Hanging", "AR-Outdoor-Stacking"}

# AR3.9/Avora Root Outdoor-Stacking (Ruecksprache): eigener Baukasten mit
# eigenen Artikelnummern (INFILED-ER-*), rechnerisch aber exakt dieselbe
# Geometrie wie AR-Stacking - Basements 3-2-1, Footbeam 1:1 unter jeder
# Cabinetspalte, Stacker 1 Cabinet hoch, 1 Clamp je Cabinet oben mittig
# ("jede Spalte muss abgesichert sein"). Deshalb bewusst kein eigener
# Rechenweg, sondern dieselbe Funktion wie AR-Stacking; unterschieden wird
# nur ueber den Systemnamen (Stueckliste/Artikelnummern im Frontend).
AR_OUTDOOR_STACKING_SYSTEM = "AR-Outdoor-Stacking"

# Systeme, die nur bei einem bestimmten Einsatzort angeboten werden.
SYSTEM_LOCATION_ONLY = {AR_OUTDOOR_STACKING_SYSTEM: "outdoor"}

# Welche Systeme ein einsatzort-exklusives System verdraengt, sobald es
# verfuegbar ist: AR3.9 und Avora Root bauen Outdoor ausschliesslich mit dem
# ER-Baukasten, nicht wahlweise mit ihrem Indoor-Stacking (AR3.91 -> AR-
# Stacking, Avora Root -> Standard-Stacking). Bewusst eine explizite Liste
# statt "verdraengt alles im selben Modus": NoBase ist ein eigenstaendiges
# Montagekonzept und bleibt Outdoor waehlbar.
SYSTEM_REPLACED_BY = {AR_OUTDOOR_STACKING_SYSTEM: {"AR-Stacking", "Standard-Stacking"}}

# Platzhalter-Gradstufen (Grad pro Fuge, Concave/Convex) - keine realen
# Datenblattwerte vorhanden, muss durch die LANG AG bestaetigt werden. Pro
# Produkt-ID hinterlegt (aktuell ueberall dieselben Werte), damit produkt-
# individuelle Abweichungen spaeter ohne Strukturaenderung eingepflegt
# werden koennen. Gilt sowohl fuer die Stacking/Hanging-Truss-Familie als
# auch fuer LIAM (eigene, additive Curving-Logik, siehe liam_truss.py).
CURVING_DEGREE_STEPS_BY_PRODUCT = {
    3: [2.5, 5, 7.5, 10],   # AURA
    2: [2.5, 5, 7.5, 10],   # ARUNA
    9: [2.5, 5, 7.5, 10],   # LUNA
    1: [2.5, 5, 7.5, 10],   # AR3.91 Plus LE
    12: [2.5, 5, 7.5, 10],  # AR 10.41
    8: [2.5, 5, 7.5, 10],   # LUGH
    5: [2.5, 5, 7.5, 10],   # JUPITER
    10: [2.5, 5, 7.5, 10],  # VENUS
    18: [2.5, 5, 7.5, 10],  # MERI 500x500
    17: [2.5, 5, 7.5, 10],  # MERI 500x1000
    7: [2.5, 5, 7.5, 10],   # LIAM
    19: [2.5, 5, 7.5, 10],  # Avora
    20: [2.5, 5, 7.5, 10],  # Avora Root
    # Halbe Cabinets (500x500) - Curving ist eine horizontale Biegung, die
    # Cabinet-Hoehe spielt dafuer keine Rolle: identische Gradstufen wie die
    # jeweilige 1000er-Variante.
    79: [2.5, 5, 7.5, 10],  # AR3.91 Plus LE 500x500
    80: [2.5, 5, 7.5, 10],  # Avora 500x500
    81: [2.5, 5, 7.5, 10],  # Avora Root 500x500
}
CURVING_UNSUPPORTED_ERROR = "Curving wird von diesem System nicht unterstützt."
CURVING_ANGLE_INVALID_ERROR = "Ungültige Gradstufe für dieses Produkt."

# ENKI, VENUS und JUPITER kopieren die Aura-Stacking-Logik 1:1 (Basements,
# Footbeam, Single Foot, Clamp-Verhaeltnis, Ausleger/Diagonale/Pipe/
# Rohrschellen) - die EINZIGE Abweichung ist, dass der vertikale Stacker
# exakt 3 Cabinets hoch ist statt wie beim Aura-Konzept 2 (Ruecksprache).
# Gilt fuer den gesamten "Stacking"-Modus, also sowohl fuer Standard-
# Stacking als auch fuer den regulaeren Stacker, der bei NoBase ab der
# dritten Cabinet-Reihe fortgesetzt wird (siehe _calculate_aura_mechanics /
# _calculate_nobase_mechanics) - es ist physisch dasselbe Bauteil. Alle
# anderen Produkte bleiben beim Aura-Standardwert 2 (siehe .get()-Fallback
# an den Aufrufstellen in calculate_mechanics).
STACKER_SPAN_BY_PRODUCT = {
    4: 3,   # ENKI
    5: 3,   # JUPITER
    10: 3,  # VENUS
}

# VENUS und JUPITER sind laut Ruecksprache dasselbe physische Produkt (nur
# andere Montage) und haben ein eigenes, vom Aura-Konzept abweichendes
# Ausleger/Diagonale/Pipe-Schwellenwert-Schema (LANG-AG-Datenblatt) - siehe
# _calculate_venus_jupiter_stacking_accessories. Gilt fuer Standard-Stacking
# UND den regulaeren Stacker-Bereich oberhalb des NoBase-Uebergangsstuecks
# (physisch dieselbe Kipp-Statik-Hardware).
VENUS_JUPITER_PRODUCT_IDS = {5, 10}

# ENKI hat ebenfalls ein eigenes Ausleger/Diagonale/Pipe-Schwellenwert-Schema
# (LANG-AG-Datenblatt), zahlenmaessig aehnlich aber nicht identisch zu
# VENUS/JUPITER - siehe _calculate_enki_stacking_accessories. Die
# "Ausleger nach hinten"-Stufe kommt bei ENKI in BEIDEN Personenkontakt-
# Faellen nie zum Einsatz: ihr Grenzwert liegt bei ENKI jeweils exakt auf
# dem Grenzwert der Kein-Zubehoer-Stufe (10=10 mit Menschen, 12=12 ohne
# Menschen), anders als bei VENUS/JUPITER (dort mit Personenkontakt ein
# echter Bereich von 10-11).
ENKI_PRODUCT_IDS = {4}

# Ballast-Tabellen (Ballast.pdf, LANG AG) - kg pro Stacker-Achse in
# Abhaengigkeit von der Wandhoehe (Cabinets), pro Produktfamilie. Eine
# "Stacker-Achse" ist ein Footbeam-Ankerpunkt (components["footbeams"] bzw.
# ["nobase_footbeams"] bei NoBase - Ruecksprache: "Footbeam-Ankerpunkte"),
# NICHT die Cabinet-Breite. "Ballast insgesamt" = kg pro Achse * Anzahl
# Achsen. Hoehen ohne Eintrag liefern bewusst keinen Wert (None), statt eine
# Zahl zu schaetzen.
def _build_ballast_table(base_value, base_max_height, discrete_steps):
    table = {h: base_value for h in range(1, base_max_height + 1)}
    table.update(discrete_steps)
    return table


BALLAST_TABLE_LUGH = _build_ballast_table(100, 6, {
    7: 140, 8: 200, 9: 220, 10: 250, 11: 200, 12: 230,
})
BALLAST_TABLE_AURA_ARUNA = _build_ballast_table(100, 6, {
    7: 140, 8: 220, 9: 250, 10: 280, 11: 200, 12: 230,
})
BALLAST_TABLE_AURA_FLEX = _build_ballast_table(110, 6, {
    7: 145, 8: 230, 9: 260, 10: 290, 11: 210, 12: 240,
})
BALLAST_TABLE_ENKI = _build_ballast_table(100, 7, {
    8: 120, 9: 150, 10: 180, 11: 190, 12: 300, 13: 320, 14: 350, 15: 380,
    16: 270, 17: 290, 18: 310,
})
BALLAST_TABLE_VENUS_JUPITER = _build_ballast_table(100, 7, {
    8: 110, 9: 140, 10: 170, 11: 210, 12: 270, 13: 290, 14: 310, 15: 340,
    16: 250, 17: 270, 18: 290,
})
# AR-Statik (AR3.9-Familie): laut Ballast.pdf nur Hoehen 3-6 hinterlegt,
# keine "bis"-Klausel fuer 1-2 - bewusst kein Fallback-Basiswert. Deckt sich
# mit NEW_AR_STACKING_INDOOR_MAX_HEIGHT (6) weiter unten: Hoehen > 6 werden
# fuer diese Produktfamilie inzwischen schon vor der Ballast-Berechnung
# blockiert (Statik-Sperre), koennen also nie erreicht werden - die Tabelle
# ist damit fuer alle erreichbaren Hoehen bereits vollstaendig. Avora Root
# nutzt laut Ruecksprache dieselbe Statik/Tabelle wie die AR-Familie.
BALLAST_TABLE_AR = {3: 100, 4: 215, 5: 280, 6: 255}

# Produkt -> Ballast-Tabelle. MERI 500x500 (18), MERI 500x1000 (17) und
# Avora (19, nicht Avora Root) bleiben laut Ruecksprache bewusst
# unzugeordnet ("bleibt erstmal offen") - kein Platzhalter-Fallback auf
# Aura/Aruna, bis echte Werte vorliegen.
BALLAST_TABLE_BY_PRODUCT = {
    8: BALLAST_TABLE_LUGH,     # LUGH
    3: BALLAST_TABLE_AURA_ARUNA,  # AURA
    2: BALLAST_TABLE_AURA_ARUNA,  # ARUNA
    1: BALLAST_TABLE_AR,       # AR3.91 Plus LE
    12: BALLAST_TABLE_AR,      # AR 10.41
    20: BALLAST_TABLE_AR,      # Avora Root (Ruecksprache: "hat die AR Statik")
    4: BALLAST_TABLE_ENKI,     # ENKI
    10: BALLAST_TABLE_VENUS_JUPITER,  # VENUS
    5: BALLAST_TABLE_VENUS_JUPITER,   # JUPITER
    16: BALLAST_TABLE_AURA_FLEX,      # AURA FLEX
}


def _calculate_ballast(product_id, height_cabinets, stacker_axis_count):
    table = BALLAST_TABLE_BY_PRODUCT.get(product_id)
    if table is None:
        return None
    per_axis_kg = table.get(height_cabinets)
    if per_axis_kg is None:
        return None
    return {
        "ballast_per_axis_kg": per_axis_kg,
        "ballast_total_kg": per_axis_kg * stacker_axis_count,
    }


# Neue AR3.9-Statiktabelle (Ruecksprache) - ersetzt die generische Aura-
# Zubehoer-Kaskade (_calculate_stacking_accessories) fuer AR3.91 Plus LE,
# AR 10.41 UND Avora Root (Ruecksprache: "hat die AR Statik"), aber NUR
# fuer Indoor-Stacking - Outdoor hat laut Ruecksprache eine eigene, noch
# nicht hinterlegte Statik und bleibt deshalb vorerst bei der alten,
# generischen Kaskade (bzw. bei Avora Root: es gibt gar keine Outdoor-
# Sonderbehandlung, Avora Root faellt dann auf die generische Aura-Kaskade
# zurueck). "Ausleger nach vorne" aus der Tabelle wird laut Ruecksprache nie
# automatisch gewaehlt (irrelevant) und deshalb hier nicht als eigene Stufe
# gefuehrt. Kaskade (guenstigste ausreichende Stufe gewinnt): kein Zubehoer
# -> K-Ausleger+Kurze Diagonale+Pipe+Rohrschellen -> L-Ausleger hinten+
# Lange Diagonale+Pipe+Rohrschellen. "Ausleger nach hinten" hat in beiden
# Personenkontakt-Faellen denselben Grenzwert wie "kein Zubehoer" und wird
# dadurch nie als eigene Stufe erreicht (siehe Tabelle) - bewusst nicht
# separat abgebildet.
NEW_AR_STACKING_PRODUCT_IDS = {
    1, 12, 20,   # AR3.91 Plus LE, AR 10.41, Avora Root
    79, 81,      # dieselben Panels als halbes Cabinet (500x500)
}
NEW_AR_STACKING_INDOOR_MAX_HEIGHT = 6

# Standard-Bauhoehe eines Cabinets im AR-/Avora-Baukasten. Alle Statik-
# Schwellen dieser Familie und der Outdoor-Stacker INFILED-ER-STACK-H1 sind
# auf dieses Mass bezogen (1 m). Seit es dieselben Panels auch als halbes
# Cabinet gibt (500x500, siehe ar_avora_500x500_setup.sql), muessen
# Cabinet-Stueckzahlen dafuer in Bauhoehe umgerechnet werden.
AR_REFERENCE_CABINET_HEIGHT_MM = 1000


def _ar_height_units(height_cabinets, cabinet_height_mm):
    # Cabinet-Anzahl -> "1-m-Einheiten", damit die AR-Statiktabellen
    # (Hoehengrenze, Zubehoer-Kaskade) unabhaengig von der Cabinet-Bauhoehe
    # gelten. Bei 1000-mm-Cabinets ist das die Identitaet - das bisherige
    # Verhalten bleibt fuer alle bestehenden Produkte exakt erhalten.
    # Aufgerundet, damit eine angebrochene Hoeheneinheit statisch wie eine
    # volle behandelt wird (sicherheitsgerichtet).
    if not cabinet_height_mm or cabinet_height_mm <= 0:
        return height_cabinets
    return math.ceil(height_cabinets * cabinet_height_mm / AR_REFERENCE_CABINET_HEIGHT_MM)


def _ar_stacker_span_rows(cabinet_height_mm):
    # Der Stacker ist 1 m lang und ueberspannt damit genau 1 m Wandhoehe -
    # bei 500er-Cabinets also zwei Reihen (Ruecksprache: "1 Stacker je 1 m
    # Hoehe"). Mindestens 1, damit ein groesseres Cabinet nie 0 ergibt.
    if not cabinet_height_mm or cabinet_height_mm <= 0:
        return 1
    return max(1, round(AR_REFERENCE_CABINET_HEIGHT_MM / cabinet_height_mm))
NEW_AR_STACKING_HEIGHT_TIERS = {
    True: {"ohne_ausleger": 3, "k_ausleger": 5, "l_ausleger": 6},   # mit Menschenkontakt
    False: {"ohne_ausleger": 4, "k_ausleger": 5, "l_ausleger": 6},  # ohne Menschenkontakt
}


def _new_ar_height_tier(height_cabinets, person_contact):
    tiers = NEW_AR_STACKING_HEIGHT_TIERS[person_contact]
    if height_cabinets <= tiers["ohne_ausleger"]:
        return "none"
    if height_cabinets <= tiers["k_ausleger"]:
        return "k"
    return "l"  # height_cabinets <= tiers["l_ausleger"], garantiert durch
                # die Statik-Sperre (NEW_AR_STACKING_INDOOR_MAX_HEIGHT) in
                # calculate_mechanics


def _calculate_new_ar_stacking_accessories(height_cabinets, footbeam_count, person_contact):
    tier = _new_ar_height_tier(height_cabinets, person_contact)
    if tier == "l":
        return {
            "ausleger_lang": footbeam_count,
            "ausleger_kurz": 0,
            "diagonale_lang": footbeam_count,
            "diagonale_kurz": 0,
            "rohrschellen": footbeam_count,
            "pipe_count": 1,
        }
    if tier == "k":
        return {
            "ausleger_lang": 0,
            "ausleger_kurz": footbeam_count,
            "diagonale_lang": 0,
            "diagonale_kurz": footbeam_count,
            "rohrschellen": footbeam_count,
            "pipe_count": 1,
        }
    return {
        "ausleger_lang": 0,
        "ausleger_kurz": 0,
        "diagonale_lang": 0,
        "diagonale_kurz": 0,
        "rohrschellen": 0,
        "pipe_count": 0,
    }


# rohrschellen_label: AR-Stacking (AR3.9/AR10.41) nennt die Rohrschellen
# "Attachment" (siehe _ar_stacking_setup_label), Avora Root laeuft ueber
# Standard-Stacking und behaelt die generische Bezeichnung "Rohrschellen".
def _new_ar_stacking_setup_label(height_cabinets, person_contact, rohrschellen_label="Rohrschellen"):
    tier = _new_ar_height_tier(height_cabinets, person_contact)
    if tier == "l":
        return f"L-Extension hinten mit Langer Diagonale, Pipe und {rohrschellen_label}"
    if tier == "k":
        return f"K-Extension mit Kurzer Diagonale, Pipe und {rohrschellen_label}"
    return "Kein Zubehör erforderlich"


def _calculate_stacking_accessories(height_cabinets, footbeam_count, person_contact):
    # Wandhoehe (in Cabinets) -> Ausleger/Diagonale/Pipe/Rohrschellen-
    # Zubehoer, automatisch anhand der Statik-Grenzwerte. Diagonale-Typ ist
    # fest an den Ausleger-Typ gekoppelt (Ruecksprache):
    #   "L-Ausleger hinten" -> immer "Lange Diagonale".
    #   "K-Ausleger" / "Kurzer Ausleger" -> immer "Kurze Diagonale" - ABER
    #     bei H == 7 (Personenkontakt-Sonderfall) bewusst OHNE Diagonale.
    #   H >= 12: L-Ausleger hinten + Lange Diagonale + Pipe + Rohrschellen.
    #   10 <= H <= 11: K-Ausleger + Kurze Diagonale + Pipe + Rohrschellen.
    #   8 <= H <= 9: Kurzer Ausleger + Kurze Diagonale, kein Pipe/Schellen.
    #   H == 7: NUR Kurzer Ausleger (Kippgefahr durch Personenkontakt),
    #            explizit ohne Diagonale/Pipe/Schellen.
    #   H < 7 (bzw. H == 7 ohne Personenkontakt): kein Zubehoer.
    # ausleger_lang/ausleger_kurz, diagonale_lang/diagonale_kurz und
    # rohrschellen skalieren alle mit footbeam_count (1 Set pro Footbeam).
    # Die Pipe ist dagegen EIN durchgehendes Bauteil ueber die ganze
    # Wandbreite (siehe calculate_mechanics fuer die Laengenberechnung in
    # Metern) - deshalb pipe_count immer 0 oder 1, nie mit footbeam_count
    # multipliziert.
    if height_cabinets >= 12:
        return {
            "ausleger_lang": footbeam_count,
            "ausleger_kurz": 0,
            "diagonale_lang": footbeam_count,
            "diagonale_kurz": 0,
            "rohrschellen": footbeam_count,
            "pipe_count": 1,
        }
    if height_cabinets >= 10:
        return {
            "ausleger_lang": 0,
            "ausleger_kurz": footbeam_count,
            "diagonale_lang": 0,
            "diagonale_kurz": footbeam_count,
            "rohrschellen": footbeam_count,
            "pipe_count": 1,
        }
    if 8 <= height_cabinets <= 9:
        return {
            "ausleger_lang": 0,
            "ausleger_kurz": footbeam_count,
            "diagonale_lang": 0,
            "diagonale_kurz": footbeam_count,
            "rohrschellen": 0,
            "pipe_count": 0,
        }
    if height_cabinets == 7 and person_contact:
        return {
            "ausleger_lang": 0,
            "ausleger_kurz": footbeam_count,
            "diagonale_lang": 0,
            "diagonale_kurz": 0,
            "rohrschellen": 0,
            "pipe_count": 0,
        }

    return {
        "ausleger_lang": 0,
        "ausleger_kurz": 0,
        "diagonale_lang": 0,
        "diagonale_kurz": 0,
        "rohrschellen": 0,
        "pipe_count": 0,
    }


# VENUS/JUPITER-eigene Ausleger/Diagonale/Pipe-Schwellen (LANG-AG-
# Datenblatt, Ruecksprache: "Nutze die Schwellwerte von Jupiter und
# Venus" statt der gemeinsamen Aura-Schwellen). Vier Stufen, je nach
# Personenkontakt an unterschiedlichen Hoehen:
#   Mit Personenkontakt:    <=9 kein Zubehoer, 10-11 Ausleger nach hinten
#     (nur Ausleger, ohne Diagonale/Pipe/Rohrschellen), 12-15 K-Ausleger
#     mit Kurzer Diagonale/Pipe/Rohrschellen, 16-18 L-Ausleger hinten mit
#     Langer Diagonale/Pipe/Rohrschellen.
#   Ohne Personenkontakt:   <=12 kein Zubehoer (die "Ausleger nach
#     hinten"-Stufe wird hier nie erreicht, ihr Grenzwert liegt bei
#     ebenfalls 12 und faellt damit mit der Kein-Zubehoer-Stufe
#     zusammen), 13-15 K-Ausleger.., 16-18 L-Ausleger..
# Ueber 18 Cabinets ist der Aufbau nicht mehr umsetzbar (siehe
# MAX_STACKING_HEIGHT_BY_PRODUCT).
# Annahme (noch nicht per Ruecksprache bestaetigt): "Ausleger nach
# hinten" ist ein reines Ausleger-Bauteil ohne Diagonale, da die
# Datenblatt-Spaltenkopfzeile - anders als bei K-/L-Ausleger - keine
# Diagonale erwaehnt.
def _calculate_venus_jupiter_stacking_accessories(height_cabinets, footbeam_count, person_contact):
    if height_cabinets >= 16:
        return {
            "ausleger_lang": footbeam_count,
            "ausleger_kurz": 0,
            "diagonale_lang": footbeam_count,
            "diagonale_kurz": 0,
            "rohrschellen": footbeam_count,
            "pipe_count": 1,
        }
    min_k_ausleger_height = 12 if person_contact else 13
    if height_cabinets >= min_k_ausleger_height:
        return {
            "ausleger_lang": 0,
            "ausleger_kurz": footbeam_count,
            "diagonale_lang": 0,
            "diagonale_kurz": footbeam_count,
            "rohrschellen": footbeam_count,
            "pipe_count": 1,
        }
    if person_contact and height_cabinets >= 10:
        return {
            "ausleger_lang": 0,
            "ausleger_kurz": footbeam_count,
            "diagonale_lang": 0,
            "diagonale_kurz": 0,
            "rohrschellen": 0,
            "pipe_count": 0,
        }

    return {
        "ausleger_lang": 0,
        "ausleger_kurz": 0,
        "diagonale_lang": 0,
        "diagonale_kurz": 0,
        "rohrschellen": 0,
        "pipe_count": 0,
    }


def _venus_jupiter_stacking_setup_label(height_cabinets, person_contact):
    if height_cabinets >= 16:
        return "L-Extension hinten mit Langer Diagonale, Pipe und Rohrschellen"
    min_k_ausleger_height = 12 if person_contact else 13
    if height_cabinets >= min_k_ausleger_height:
        return "K-Extension mit Kurzer Diagonale, Pipe und Rohrschellen"
    if person_contact and height_cabinets >= 10:
        return "Extension nach hinten (ohne Diagonale)"
    return "Kein Zubehör erforderlich"


# ENKI-eigene Ausleger/Diagonale/Pipe-Schwellen (LANG-AG-Datenblatt).
# Gleiche Grundstruktur wie VENUS/JUPITER (kein Zubehoer -> K-Ausleger ->
# L-Ausleger), aber die "Ausleger nach hinten"-Zwischenstufe entfaellt
# komplett - ihr Datenblatt-Grenzwert liegt bei ENKI in beiden
# Personenkontakt-Faellen exakt auf dem Grenzwert der Kein-Zubehoer-Stufe
# (10=10 bzw. 12=12), sie wird also nie als guenstigste ausreichende Stufe
# gewaehlt.
def _calculate_enki_stacking_accessories(height_cabinets, footbeam_count, person_contact):
    if height_cabinets >= 16:
        return {
            "ausleger_lang": footbeam_count,
            "ausleger_kurz": 0,
            "diagonale_lang": footbeam_count,
            "diagonale_kurz": 0,
            "rohrschellen": footbeam_count,
            "pipe_count": 1,
        }
    min_k_ausleger_height = 11 if person_contact else 13
    if height_cabinets >= min_k_ausleger_height:
        return {
            "ausleger_lang": 0,
            "ausleger_kurz": footbeam_count,
            "diagonale_lang": 0,
            "diagonale_kurz": footbeam_count,
            "rohrschellen": footbeam_count,
            "pipe_count": 1,
        }

    return {
        "ausleger_lang": 0,
        "ausleger_kurz": 0,
        "diagonale_lang": 0,
        "diagonale_kurz": 0,
        "rohrschellen": 0,
        "pipe_count": 0,
    }


def _enki_stacking_setup_label(height_cabinets, person_contact):
    if height_cabinets >= 16:
        return "L-Extension hinten mit Langer Diagonale, Pipe und Rohrschellen"
    min_k_ausleger_height = 11 if person_contact else 13
    if height_cabinets >= min_k_ausleger_height:
        return "K-Extension mit Kurzer Diagonale, Pipe und Rohrschellen"
    return "Kein Zubehör erforderlich"


def _stacking_setup_label(height_cabinets, person_contact):
    if height_cabinets >= 12:
        return "L-Extension hinten mit Langer Diagonale, Pipe und Rohrschellen"
    if height_cabinets >= 10:
        return "K-Extension mit Kurzer Diagonale, Pipe und Rohrschellen"
    if 8 <= height_cabinets <= 9:
        return "Kurze Extension mit Kurzer Diagonale (ohne Pipe)"
    if height_cabinets == 7 and person_contact:
        return "Kurze Extension (Personenkontakt möglich, ohne Diagonale)"
    return "Kein Zubehör erforderlich"


# AR3.9-eigene Variante von _stacking_setup_label - Umbenennung
# "Rohrschellen" -> "Attachment", damit der Auto-Konfigurations-Text nicht
# der Stueckliste widerspricht (siehe _calculate_ar_stacking_mechanics).
# Indoor nutzt die neue AR3.9-Statiktabelle (NEW_AR_STACKING_HEIGHT_TIERS,
# Ruecksprache), Outdoor bleibt vorerst bei den alten, generischen Aura-
# Schwellenwerten (eigene Outdoor-Statik noch nicht hinterlegt).
def _ar_stacking_setup_label(height_cabinets, person_contact, location=None):
    if location == "indoor":
        return _new_ar_stacking_setup_label(height_cabinets, person_contact, "Attachment")
    if height_cabinets >= 12:
        return "L-Extension hinten mit Langer Diagonale, Pipe und Attachment"
    if height_cabinets >= 10:
        return "K-Extension mit Kurzer Diagonale, Pipe und Attachment"
    if 8 <= height_cabinets <= 9:
        return "Kurze Extension mit Kurzer Diagonale (ohne Pipe)"
    if height_cabinets == 7 and person_contact:
        return "Kurze Extension (Personenkontakt möglich, ohne Diagonale)"
    return "Kein Zubehör erforderlich"


def _calculate_aura_mechanics(width_cabinets, height_cabinets, person_contact=False, curving_mode=None, stacker_span=2, product_id=None, location=None):
    basements_3, basements_2, basements_1 = _apply_curving_width_split(width_cabinets, curving_mode)
    is_curving = curving_mode in ("concave", "convex")

    # Footbeams: normal Anzahl Cabinets in der Breite, aufgerundet / 2 - im
    # Curving-Modus individualisiert auf Breite 1 (1:1 zum Cabinet-Raster),
    # passend zu den Einzel-Basements, an denen sie haengen.
    footbeams = width_cabinets if is_curving else math.ceil(width_cabinets / 2)

    # Single Foot jeweils links und rechts am Ende der Wand - bleibt auch im
    # Curving-Modus bestehen.
    single_feet = 2

    # Stacker sitzen ausschliesslich auf den vertikalen Fugen, an denen ein
    # Footbeam-Ankerpunkt existiert - pro Footbeam floor(Hoehe/stacker_span)
    # Stacker (bei nicht restlos teilbarer Wandhoehe bleiben die obersten
    # Reihen frei). stacker_span ist bei den meisten Produkten 2 (Aura-
    # Konzept) - VENUS/JUPITER kopieren die Aura-Logik 1:1, nur mit
    # stacker_span=3 (siehe STACKER_SPAN_BY_PRODUCT). Diese Formel gilt
    # unveraendert im Curving-Modus (Ruecksprache: "Stacker nach exakt
    # derselben Logik wie beim normalen Stacking") - da Footbeams dort bereits
    # individualisiert auf Breite 1 sind (footbeams = width_cabinets statt
    # ceil(width/2)), ergibt sich automatisch 1 Stacker-Spalte pro Cabinet-
    # Spalte, ohne eigenen Sonderfall noetig.
    stacker = footbeams * (height_cabinets // stacker_span)

    # Clamp-Typ: normale Clamps ODER Curving-Clamps. Bei Wandbreite 1 gibt es
    # nur eine einzelne Stacker-Spalte, keine zwei nebeneinanderliegenden
    # Stacker zum Verbinden - eine normale Clamp (fuer den Stoss zwischen
    # zwei Stacker-Spalten gedacht) passt hier nicht, stattdessen wird auch
    # OHNE aktives Curving die Curving-Clamp verwendet (Ruecksprache: "bei
    # Breite 1 Standard-Stacking muessen Curving-Clamps statt normaler
    # Clamps benutzt werden, der Rest bleibt gleich"). Gilt NUR fuer die
    # Clamp-Wahl - Footbeams/Basements/Stacker-Formel oben haengen weiterhin
    # ausschliesslich an is_curving, nicht an width_cabinets.
    use_curving_clamp = is_curving or width_cabinets == 1
    if use_curving_clamp:
        # Curving-Modus (Ruecksprache): normale Clamps entfallen - stattdessen
        # sitzt oben mittig auf jedem Cabinet eine Curving-Clamp, um die
        # Winkelverbindung der gebogenen Module abzufangen. Ausnahme bei
        # nicht restlos durch stacker_span teilbarer Wandhoehe: die obersten
        # Reihen haben baubedingt keinen Stacker (siehe stacker-Formel oben) -
        # dort darf folglich auch keine Curving-Clamp sitzen, da kein Bauteil
        # zum Befestigen vorhanden ist.
        curving_clamp_rows = (height_cabinets // stacker_span) * stacker_span
        clamps = 0
        curving_clamp = width_cabinets * curving_clamp_rows
    else:
        # Jeweils 2 Clamps pro Stacker.
        clamps = stacker * 2
        curving_clamp = 0

    components = {
        "basements_3": basements_3,
        "basements_2": basements_2,
        "basements_1": basements_1,
        "footbeams": footbeams,
        "single_feet": single_feet,
        "stacker": stacker,
        "clamps": clamps,
        "curving_clamp": curving_clamp,
    }
    # Ausleger/Diagonale/Pipe/Rohrschellen (Kipp-Statik nach Wandhoehe) sind
    # orthogonal zu Curving (horizontale Biegung) und bleiben unveraendert.
    # VENUS/JUPITER nutzen dabei ihre eigenen, abweichenden Hoehen-Schwellen
    # (siehe VENUS_JUPITER_PRODUCT_IDS) statt der gemeinsamen Aura-Schwellen.
    # ENKI hat ebenfalls eigene Schwellen (siehe ENKI_PRODUCT_IDS) - ENKI
    # nutzt kein NoBase (siehe product_mechanics), deshalb reicht hier die
    # Anbindung an _calculate_aura_mechanics.
    if product_id in VENUS_JUPITER_PRODUCT_IDS:
        components.update(_calculate_venus_jupiter_stacking_accessories(height_cabinets, footbeams, person_contact))
    elif product_id in ENKI_PRODUCT_IDS:
        components.update(_calculate_enki_stacking_accessories(height_cabinets, footbeams, person_contact))
    elif product_id in NEW_AR_STACKING_PRODUCT_IDS and location == "indoor":
        # Nur Avora Root (20) erreicht diesen Zweig ueberhaupt - AR3.91/
        # AR10.41 laufen ueber "AR-Stacking" (_calculate_ar_stacking_
        # mechanics), nicht ueber Standard-Stacking. Outdoor (oder Avora
        # Root ohne location="indoor") faellt bewusst auf die generische
        # Aura-Kaskade zurueck (Ruecksprache: eigene Outdoor-Statik noch
        # nicht hinterlegt).
        components.update(_calculate_new_ar_stacking_accessories(height_cabinets, footbeams, person_contact))
    else:
        components.update(_calculate_stacking_accessories(height_cabinets, footbeams, person_contact))
    return components


# AURA FLEX (Produkt LANG-016) - eigenes Stacking-System, das bewusst NICHT
# der 3-2-1-Basement-Optimierung der uebrigen Aura-Familie folgt: statt
# Basements in den Breiten 3/2/1 Cabinets gibt es bei Flex nur einen
# einzigen Basement-Typ mit fester Breite 0,5 Cabinets, der an jeder
# Schnittstelle zwischen zwei benachbarten Cabinets sitzt - also genau
# width_cabinets - 1 Stueck (bei Breite 1 gibt es keine Fuge, folglich 0).
# Single Foot bleibt strukturell unveraendert zum Aura-Konzept (2x, je einer
# an den Wandenden, gleiche Position) - heisst bei Flex nur "Flex Single
# Foot" statt "Single Foot". Footbeam/Stacker/Clamp und die Ausleger/
# Diagonale/Pipe/Rohrschellen-Zubehoerauswahl folgen unveraendert der
# generischen Aura-Formel, da hierzu keine Abweichung vereinbart wurde.
# Statische Maximalhoehe ist identisch zu AURA (siehe
# MAX_STACKING_HEIGHT_BY_PRODUCT).
def _calculate_aura_flex_mechanics(width_cabinets, height_cabinets, person_contact=False, stacker_span=2):
    basements_flex = max(width_cabinets - 1, 0)

    footbeams = math.ceil(width_cabinets / 2)
    flex_single_feet = 2
    stacker = footbeams * (height_cabinets // stacker_span)
    clamps = stacker * 2

    components = {
        "basements_flex": basements_flex,
        "footbeams": footbeams,
        "flex_single_feet": flex_single_feet,
        "stacker": stacker,
        "clamps": clamps,
    }
    components.update(_calculate_stacking_accessories(height_cabinets, footbeams, person_contact))
    return components


# AR3.9-Stacking (Produkt AR3.91 Plus LE) - baut 1:1 auf dem Aura-Konzept
# auf (Ruecksprache, Korrektur des vorherigen radikalen Resets): identische
# Struktur wie _calculate_aura_mechanics (Basements 3-2-1, Footbeam, Single
# Foot, Stacker, Clamp, Ausleger lang/kurz, Diagonale lang/kurz, Pipe) -
# genau DREI Abweichungen:
#   1. Footbeam ist 1:1 zum Cabinet-Raster (statt ceil(Breite / 2)).
#   2. Ein Stacker ist genau so GROSS wie ein Cabinet - das bezieht sich
#      auf die HOEHE (1 Cabinet-Reihe statt 2), NICHT auf die Grundflaeche
#      (Ruecksprache, Korrektur): der Stacker bleibt optisch duenn wie beim
#      Aura-Konzept, es gibt nur doppelt so viele davon (siehe Formel
#      unten), und pro Stacker nur noch 1 statt 2 Clamps.
#   3. "Rohrschellen" heisst bei AR3.9 "Attachment" - gleiche Formel/
#      Zaehlung, nur umbenannt.
def _calculate_ar_stacking_mechanics(width_cabinets, height_cabinets, person_contact=False, curving_mode=None, location=None, include_single_feet=True, cabinet_height_mm=AR_REFERENCE_CABINET_HEIGHT_MM):
    basements_3, basements_2, basements_1 = _apply_curving_width_split(width_cabinets, curving_mode)

    # Footbeams: 1:1 zum Cabinet-Raster (vorher beim Aura-Konzept
    # ceil(Breite / 2)) - die erste strukturelle Abweichung von
    # _calculate_aura_mechanics. Bereits Breite 1, deshalb im Curving-Modus
    # unveraendert (keine weitere Individualisierung noetig).
    footbeams = width_cabinets

    # Single Foot jeweils links und rechts am Ende der Wand. Im Outdoor-
    # Baukasten (AR-Outdoor-Stacking) gibt es ihn nicht (Ruecksprache: "die
    # Single foots muessen raus") - dort steht der Footbeam direkt auf dem
    # Boden, deshalb include_single_feet=False.
    single_feet = 2 if include_single_feet else 0

    # "Stacker = Groesse eines Cabinets" bezieht sich auf die HOEHE, nicht
    # die Grundflaeche (Ruecksprache, Korrektur): ein Stacker ueberspannt
    # genau 1 Cabinet-Reihe statt wie beim Aura-Konzept 2 Reihen - deshalb
    # pro Footbeam genau height_cabinets Stacker (statt floor(Hoehe/2)),
    # keine freie oberste Reihe mehr (1 teilt jede Hoehe restlos). Da ein
    # Stacker nur noch 1 Reihe statt 2 ueberspannt, gibt es dort auch keine
    # "mittlere Fuge" mehr - nur noch 1 Clamp pro Stacker (an dessen oberer
    # Fuge) statt 2.
    #
    # Curving-Modus (Ruecksprache, final): bei AR3.9 IDENTISCH zu Flat - keine
    # eigene Fallunterscheidung. Footbeam ist bei AR3.9 ohnehin immer Breite 1
    # (siehe oben), die Formel liefert dadurch bereits automatisch 1 Stacker +
    # 1 Clamp pro Cabinet-Spalte UND -Reihe, auch mit Curving aktiv - deshalb
    # bleibt curving_clamp bei AR3.9 immer 0 (keine separate Curving-Clamp).
    #
    # Halbe Cabinets (500x500): der Stacker ist ein 1-m-Bauteil und ueberspannt
    # dort zwei Reihen (Ruecksprache: "1 Stacker je 1 m Hoehe") - deshalb
    # floor(Hoehe / span) statt fix eine Reihe. Bei 1000er-Cabinets ist span=1
    # und die Formel bleibt exakt die bisherige.
    #
    # Geht die Wandhoehe nicht restlos in der Stacker-Laenge auf (z.B. 5 halbe
    # Cabinets = 2,5 m bei 1-m-Stackern), bleibt oben eine Reihe ohne Stacker.
    # Dieses oberste Cabinet bekommt dann auch KEINE Clamp (Ruecksprache: "bei
    # ungerader Hoehe keinen Stacker und keine Clamp bei dem obersten
    # Cabinet") - es gaebe dort schlicht kein Bauteil zum Befestigen. Die
    # Clamps zaehlen deshalb nur ueber die tatsaechlich von Stackern
    # abgedeckten Reihen. Bei span=1 ist covered_rows == height_cabinets, das
    # bisherige Verhalten der 1000er-Cabinets bleibt unveraendert.
    stacker_span = _ar_stacker_span_rows(cabinet_height_mm)
    stacker_rows = height_cabinets // stacker_span
    covered_rows = stacker_rows * stacker_span
    stacker = footbeams * stacker_rows
    clamps = footbeams * covered_rows
    curving_clamp = 0

    components = {
        "basements_3": basements_3,
        "basements_2": basements_2,
        "basements_1": basements_1,
        "footbeams": footbeams,
        "single_feet": single_feet,
        "stacker": stacker,
        "clamps": clamps,
        "curving_clamp": curving_clamp,
    }
    # Neue AR3.9-Statiktabelle (Ruecksprache) NUR Indoor - Outdoor hat eine
    # eigene, noch nicht hinterlegte Statik und bleibt vorerst bei der alten
    # generischen Aura-Kaskade (siehe NEW_AR_STACKING_PRODUCT_IDS).
    # Die Schwellen beider Kaskaden sind Bauhoehen in 1-m-Schritten, deshalb
    # bei halben Cabinets mit der umgerechneten Hoehe arbeiten (bei
    # 1000er-Cabinets identisch zu height_cabinets).
    statics_height = _ar_height_units(height_cabinets, cabinet_height_mm)
    if location == "indoor":
        accessories = _calculate_new_ar_stacking_accessories(statics_height, footbeams, person_contact)
    else:
        accessories = _calculate_stacking_accessories(statics_height, footbeams, person_contact)
    accessories["attachment"] = accessories.pop("rohrschellen")
    components.update(accessories)
    return components


# Harmonisierte Hanging-Statik: AURA, ARUNA und LUNA nutzen fuer den Modus
# 'Hanging' exakt dieselben Grenzwerte UND dieselbe 3-2-1-Basement-
# Stueckliste (Hanging-Truss) - keine produktindividuellen Werte mehr fuer
# diese drei. _get_hanging_statics() ist die einzige Quelle der Wahrheit,
# beide (bzw. alle drei) Produkte referenzieren im Code dieselbe Funktion.
# AURA FLEX (LANG-016) ist ebenfalls hier gelistet - identische Statik-
# Hoehengrenze wie AURA ("genau so hoch wie die normale Aura"), obwohl es
# im eigenen System Flex-Hanging eine abweichende Truss-Stueckliste nutzt
# (siehe _calculate_aura_flex_hanging_mechanics) statt der 3-2-1-Verteilung.
HARMONIZED_HANGING_STATICS_PRODUCT_IDS = {3, 2, 9, 16}  # AURA, ARUNA, LUNA, AURA FLEX


def _get_hanging_statics():
    # Bis zu welcher Wandhoehe (in Cabinets) 1 Oese pro Aufhaengungspunkt
    # reicht, und bis zu welcher Hoehe (mit Zusatz-Oese) 2 Oesen pro Punkt
    # reichen - LANG-AG-Datenblatt AURA, gilt identisch fuer ARUNA und LUNA.
    return {1: 13, 2: 18}


# Pro Produkt hinterlegte Statik-Grenzwerte (max. Wandhoehe in Cabinets)
# beim Hanging-Truss-System, fuer alle Produkte AUSSER den oben
# harmonisierten (AURA/ARUNA/LUNA - siehe _get_hanging_statics). Gleiche
# Bedeutung: bis zu welcher Hoehe 1 Oese pro Aufhaengungspunkt reicht, und
# bis zu welcher Hoehe (mit Zusatz-Oese) 2 Oesen pro Punkt reichen. Fehlt
# das 2-Oesen-Limit, gibt es keine Eskalation - ueberschreitet H bereits das
# 1-Oesen-Limit, ist der Aufbau direkt nicht umsetzbar.
# Platzhalterwerte: LUGH und MERI 500x500 folgen mechanisch exakt dem
# Aura-Konzept, echte Datenblatt-Grenzwerte liegen aber noch nicht vor - bis
# dahin werden hier die AURA-Werte uebernommen. Muss durch die LANG AG
# bestaetigt bzw. korrigiert werden.
HANGING_OESEN_LIMITS_BY_PRODUCT = {
    8: {1: 13, 2: 18},  # LUGH (Platzhalter, = AURA-Werte)
    18: {1: 13, 2: 18},  # MERI 500x500 (Platzhalter, = AURA-Werte)
    # Neu an Hanging-Truss angebunden fuers Curving-Feature (siehe
    # curving_setup.sql) - ebenfalls Platzhalter = AURA-Werte.
    # JUPITER/VENUS: NICHT mehr hier - eigenes, feinere Statik-Modell
    # (Zusatz-Oese nur fuers 3er-Modul), siehe VENUS_JUPITER_PRODUCT_IDS /
    # _calculate_venus_jupiter_hanging_mechanics.
    17: {1: 13, 2: 18},  # MERI 500x1000 (Platzhalter, = AURA-Werte)
    # Avora/Avora Root: echter Datenblatt-Wert (Datasheet_AVORA_rev5.pdf,
    # "Max. Overall height (hanging/standing): 18 Cabinets / 6 Cabinets") -
    # 18 Cabinets fuer den haengenden Aufbau. Datenblatt dokumentiert keine
    # zweite Oesen-Eskalationsstufe, deshalb nur Tier 1 hinterlegt.
    19: {1: 18},  # Avora
    20: {1: 18},  # Avora Root
    # ENKI: NICHT mehr hier - eigenes Statik-Modell (Zusatz-Oese je nach
    # Modulbreite, "aussen" statt "mittig" montiert), siehe
    # ENKI_PRODUCT_IDS / _calculate_enki_hanging_mechanics.
}

HANGING_STATIK_LIMIT_ERROR = "Statische Grenze für dieses Produkt überschritten, bitte wenden SIe sich an die LANG AG"


def _calculate_hanging_oesen_per_point(height_cabinets, product_id):
    # Prueft zuerst, ob 1 Oese pro Aufhaengungspunkt fuer die Wandhoehe
    # reicht, danach (falls fuer das Produkt hinterlegt) das 2-Oesen-Limit.
    # Ueberschreitet die Wandhoehe beide Limits (oder ist fuer das Produkt
    # gar kein Limit hinterlegt), liefert die Funktion None - der Aufbau ist
    # dann nicht umsetzbar.
    if product_id in HARMONIZED_HANGING_STATICS_PRODUCT_IDS:
        limits = _get_hanging_statics()
    else:
        limits = HANGING_OESEN_LIMITS_BY_PRODUCT.get(product_id)
    if limits is None:
        return None

    one_oese_limit = limits.get(1)
    if one_oese_limit is not None and height_cabinets <= one_oese_limit:
        return 1

    two_oesen_limit = limits.get(2)
    if two_oesen_limit is not None and height_cabinets <= two_oesen_limit:
        return 2

    return None


def _calculate_hanging_truss_mechanics(width_cabinets, oesen_per_point, curving_mode=None):
    # Gleiche Breiten-Optimierung (3-2-1) wie beim Standard-Stacking, aber
    # die Wand haengt an einem Traversensystem statt auf Basements zu
    # stehen: keine Footbeams/Single Feet und - da die Module fest an der
    # Traverse haengen statt aufeinandergestapelt zu werden - auch kein
    # Stacker/Clamp. Es gibt nur EINE Baugruppe, das Hanging-Truss-Modul
    # (3er/2er/1er): sie bildet sowohl die mechanische Breitensegmentierung
    # als auch die Aufhaengungspunkte - jedes Modul (unabhaengig von seiner
    # Groesse) ist genau 1 Aufhaengungspunkt. Reicht 1 Oese pro Punkt nicht,
    # kommt pro Aufhaengungspunkt genau 1 Zusatz-Oese dazu.
    # Curving-Modus (Ruecksprache): nur der Breite-1-Zwang greift hier -
    # kein neues Bauteil, da Hanging-Truss ohnehin schon kein Stacker/Clamp
    # kennt, das ersetzt werden muesste.
    basements_3, basements_2, basements_1 = _apply_curving_width_split(width_cabinets, curving_mode)
    aufhaengungspunkte = basements_3 + basements_2 + basements_1

    return {
        "basements_3": basements_3,
        "basements_2": basements_2,
        "basements_1": basements_1,
        "footbeams": 0,
        "single_feet": 0,
        "stacker": 0,
        "clamps": 0,
        "oesen_count": oesen_per_point,
        "zusatz_oese": aufhaengungspunkte if oesen_per_point == 2 else 0,
    }


# Aura Flex Hanging (LANG-016) - eigenes Hanging-System, analog zu Flex-
# Stacking bewusst NICHT ueber die 3-2-1-Hanging-Truss-Modul-Verteilung.
# Es gibt nur einen einzigen Truss-Typ ("Aura Truss"), der zwischen jeweils
# 2 benachbarten Cabinets befestigt wird - kein laengeres Modul verfuegbar,
# also genau width_cabinets - 1 Stueck (dieselbe Zaehlung/Position wie
# basements_flex in _calculate_aura_flex_mechanics). Jeder Truss ist -
# analog zum generischen Hanging-Truss-Modell - genau 1 Aufhaengungspunkt;
# reicht 1 Oese pro Punkt nicht, kommt pro Truss 1 Zusatz-Oese dazu.
# Statische Maximalhoehe ist identisch zu AURA (siehe
# HARMONIZED_HANGING_STATICS_PRODUCT_IDS / _get_hanging_statics).
def _calculate_aura_flex_hanging_mechanics(width_cabinets, oesen_per_point):
    flex_truss = max(width_cabinets - 1, 0)
    return {
        "flex_truss": flex_truss,
        "oesen_count": oesen_per_point,
        "zusatz_oese": flex_truss if oesen_per_point == 2 else 0,
    }


# VENUS/JUPITER-eigene Hanging-Truss-Statik (LANG-AG-Datenblatt,
# Ruecksprache: "Bar" = die bestehenden Hanging-Truss-Module, also 1er/2er/
# 3er = basements_1/2/3). Anders als beim generischen Modell (EIN
# Oesen-Tier fuer die gesamte Wand) braucht hier nur das 3er-Modul ab einer
# bestimmten Wandhoehe eine Zusatz-Oese - 1er/2er-Module kommen bei jeder
# Hoehe bis zum Gesamtlimit mit 1 Oese aus:
#   "1 Bar: 18" / "2 Bar 1 Oese: 18" / "2 Bar 2 Oesen: 18" -> 1er/2er-Module
#     erreichen mit nur 1 Oese bereits das volle Limit, eine zweite Oese
#     bringt dort keinen Hoehengewinn.
#   "3 Bar 1 Oese: 10" / "3 Bar 2 Oesen (mitte/aussen): 18" -> das 3er-Modul
#     braucht ab Hoehe 11 eine Zusatz-Oese, um ebenfalls bis 18 zu kommen;
#     mit nur 1 Oese ist bei Hoehe 10 Schluss. "mitte" vs. "aussen" ergeben
#     denselben Wert (18) - die Position des Aufhaengungspunkts im 3er-Modul
#     aendert nichts an der Zaehlung, deshalb hier nicht unterschieden.
# Gesamt-Limit ueber alle Konfigurationen hinweg: 18 Cabinets.
VENUS_JUPITER_HANGING_MAX_HEIGHT = 18
VENUS_JUPITER_HANGING_3BAR_ZUSATZ_OESE_MIN_HEIGHT = 11  # ab hier braucht das 3er-Modul 2 statt 1 Oese


def _calculate_venus_jupiter_hanging_mechanics(width_cabinets, height_cabinets, curving_mode=None):
    basements_3, basements_2, basements_1 = _apply_curving_width_split(width_cabinets, curving_mode)

    # Nur die 3er-Module (basements_3) brauchen ab der Grenzhoehe eine
    # Zusatz-Oese - 1er/2er-Module (basements_1/2) nie, da sie laut
    # Datenblatt bei jeder Hoehe bis 18 mit 1 Oese auskommen.
    needs_3bar_zusatz_oese = height_cabinets >= VENUS_JUPITER_HANGING_3BAR_ZUSATZ_OESE_MIN_HEIGHT
    zusatz_oese = basements_3 if needs_3bar_zusatz_oese else 0

    return {
        "basements_3": basements_3,
        "basements_2": basements_2,
        "basements_1": basements_1,
        "footbeams": 0,
        "single_feet": 0,
        "stacker": 0,
        "clamps": 0,
        "oesen_count": 1,
        "zusatz_oese": zusatz_oese,
    }


def _venus_jupiter_hanging_setup_label(zusatz_oese):
    # zusatz_oese ist bereits 0, wenn kein 3er-Modul in der Wand vorkommt
    # (siehe _calculate_venus_jupiter_hanging_mechanics) - der Hinweistext
    # erscheint deshalb nur, wenn tatsaechlich mindestens ein 3er-Modul die
    # Zusatz-Oese braucht, nicht schon bei bloss ausreichender Hoehe.
    if zusatz_oese > 0:
        return "Truss-System mit 1 Öse (3er-Module ab dieser Höhe: 2 Ösen)"
    return "Truss-System mit 1 Öse"


# ENKI-eigene Hanging-Truss-Statik (LANG-AG-Datenblatt, Ruecksprache: die
# Oese sitzt am Truss-Modul entweder mittig oder aussen - eine reine
# Montageposition derselben Zusatz-Oese, kein eigenes Bauteil. Aussen ist
# dabei immer mindestens gleich gut wie mittig (27 vs. 26 bei 3er-Modulen),
# deshalb wird hier IMMER aussen montiert, sobald eine Zusatz-Oese noetig
# ist - "mittig" wird nirgends bevorzugt, da es nie einen Vorteil bietet.
#   "1 Bar: 90" -> 1er-Module kommen bis 90 mit 1 Oese aus.
#   "2 Bar 1 Oese: 29" / "2 Bar 2 Oesen: 90" -> 2er-Module brauchen ab
#     Hoehe 30 eine Zusatz-Oese, erreichen damit ebenfalls 90.
#   "3 Bar 1 Oese: 12" / "3 Bar 2 Oesen aussen: 27" -> 3er-Module brauchen
#     ab Hoehe 13 eine Zusatz-Oese (aussen montiert), kommen damit aber nur
#     bis 27 - IMMER der begrenzende Faktor, sobald ein 3er-Modul in der
#     Wand vorkommt (die Wandhoehe ist ueber alle Aufhaengungspunkte
#     hinweg einheitlich, das schwaechste Modul bestimmt das Maximum).
# Die Breiten-Verteilung selbst (3-2-1-Greedy, siehe _optimal_basements)
# bleibt unveraendert - es wird hier NICHT versucht, 3er-Module durch
# 2er-Module zu ersetzen, um mehr Hoehe zu ermoeglichen.
ENKI_HANGING_MAX_HEIGHT_WITH_3BAR = 27
ENKI_HANGING_MAX_HEIGHT_WITHOUT_3BAR = 90
ENKI_HANGING_3BAR_ZUSATZ_OESE_MIN_HEIGHT = 13
ENKI_HANGING_2BAR_ZUSATZ_OESE_MIN_HEIGHT = 30


def _calculate_enki_hanging_max_height(basements_3):
    return ENKI_HANGING_MAX_HEIGHT_WITH_3BAR if basements_3 > 0 else ENKI_HANGING_MAX_HEIGHT_WITHOUT_3BAR


def _calculate_enki_hanging_mechanics(width_cabinets, height_cabinets, curving_mode=None):
    basements_3, basements_2, basements_1 = _apply_curving_width_split(width_cabinets, curving_mode)

    zusatz_oese_3bar = basements_3 if height_cabinets >= ENKI_HANGING_3BAR_ZUSATZ_OESE_MIN_HEIGHT else 0
    zusatz_oese_2bar = basements_2 if height_cabinets >= ENKI_HANGING_2BAR_ZUSATZ_OESE_MIN_HEIGHT else 0

    return {
        "basements_3": basements_3,
        "basements_2": basements_2,
        "basements_1": basements_1,
        "footbeams": 0,
        "single_feet": 0,
        "stacker": 0,
        "clamps": 0,
        "oesen_count": 1,
        "zusatz_oese": zusatz_oese_3bar + zusatz_oese_2bar,
    }


def _enki_hanging_setup_label(basements_3, basements_2, height_cabinets):
    notes = []
    if basements_3 > 0 and height_cabinets >= ENKI_HANGING_3BAR_ZUSATZ_OESE_MIN_HEIGHT:
        notes.append("3er-Module: 2 Ösen außen")
    if basements_2 > 0 and height_cabinets >= ENKI_HANGING_2BAR_ZUSATZ_OESE_MIN_HEIGHT:
        notes.append("2er-Module: 2 Ösen")
    if notes:
        return f"Truss-System mit 1 Öse ({', '.join(notes)})"
    return "Truss-System mit 1 Öse"


def _wandadapter_vertical_seam_count(width_cabinets):
    # Jede zweite vertikale Fuge zwischen zwei Cabinets (Fuge 1, 3, 5, ...)
    # - bei width_cabinets Cabinets gibt es (width_cabinets - 1) vertikale
    # Fugen.
    total_seams = max(0, width_cabinets - 1)
    count = (total_seams + 1) // 2

    # Randbefestigung: bei ungerader Wandbreite liegt die letzte Fuge
    # (zwischen dem vorletzten und dem letzten Cabinet, die Abschlusskante)
    # NICHT im Jedes-zweite-Fuge-Muster (sie ist dann geradzahlig) und muss
    # zusaetzlich gesichert werden, damit der Abschluss der Wand nicht
    # schwingt. Ergebnis entspricht ceil(width_cabinets / 2).
    if width_cabinets % 2 == 1 and total_seams >= 1:
        count += 1

    return count


def _calculate_wandadapter_mechanics(width_cabinets, height_cabinets):
    # Gleiche Breiten-Optimierung (3-2-1) wie beim Standard-Stacking fuer die
    # Basements, aber kein Footbeam/Single-Foot/Stacker/Clamp - die Wand
    # haengt stattdessen direkt an der Wand.
    basements_3, basements_2, basements_1 = _optimal_basements(width_cabinets)

    # Wandadapter sitzen an den Schnittpunkten von zwei Fugen-Rastern:
    # - horizontal: die vertikalen Fugen aus _wandadapter_vertical_seam_count
    #   (jede zweite Fuge plus ggf. Randbefestigung an der Abschlusskante).
    # - vertikal: jede horizontale Fuge zwischen zwei uebereinander
    #   liegenden Cabinets - bei height_cabinets Reihen sind das
    #   (height_cabinets - 1) Fugen. Die oberste Kante (oberhalb der
    #   obersten Reihe) und die unterste Kante (zur Basis/Boden) zaehlen
    #   NICHT mit, da dort kein Cabinet-zu-Cabinet-Stoss existiert.
    vertical_seams_with_adapter = _wandadapter_vertical_seam_count(width_cabinets)
    horizontal_seams_with_adapter = max(0, height_cabinets - 1)
    wandadapter = vertical_seams_with_adapter * horizontal_seams_with_adapter

    return {
        "basements_3": basements_3,
        "basements_2": basements_2,
        "basements_1": basements_1,
        "footbeams": 0,
        "single_feet": 0,
        "stacker": 0,
        "clamps": 0,
        "wandadapter": wandadapter,
    }


def _calculate_nobase_mechanics(width_cabinets, height_cabinets, person_contact=False, stacker_span=2, product_id=None):
    # Keine Basements, keine Single Feet. Stattdessen traegt fuer die
    # unteren stacker_span Cabinet-Reihen ein eigenstaendiges NoBase-System:
    # NoBase-Footbeams direkt am Boden (gleiche Berechnung wie normale
    # Footbeams, alle 2 Cabinets - auch am Rand, egal ob die Cabinet-Anzahl
    # in der Breite gerade oder ungerade ist), und darauf je Footbeam-
    # Ankerpunkt ein NoBase-Stacker - ein Uebergangsstueck, das funktional
    # den bisherigen untersten Standard-Stacker ersetzt und die untersten
    # stacker_span Reihen komplett abdeckt. stacker_span ist bei den meisten
    # Produkten 2 (Aura-Konzept) - VENUS/JUPITER kopieren die Aura-Logik 1:1,
    # nur mit stacker_span=3 (siehe STACKER_SPAN_BY_PRODUCT) - das NoBase-
    # Uebergangsstueck ist bei ihnen deshalb ebenfalls 3 Cabinets hoch
    # (Ruecksprache, Praezisierung), nicht mehr fest auf 2 Reihen begrenzt.
    #
    # Ab der (stacker_span + 1)-ten Reihe wird das normale Standard-Stacker/
    # Clamp-System unveraendert fortgesetzt (gleiche Formel wie bei Standard-
    # Stacking, nur um das bereits durch NoBase abgedeckte unterste Paket
    # nach oben verschoben) - physisch dasselbe Bauteil, nutzt deshalb
    # dieselbe Spannweite stacker_span.
    #
    # Jedes NoBase-Stacker-Modul ist eine eigenstaendige Baugruppe mit
    # (stacker_span + 1) festen Ankerpunkten auf sich selbst (Boden + je
    # eine Fuge zwischen den ueberspannten Reihen + oben) - IMMER,
    # unabhaengig davon, ob darueber noch ein Standard-Stacker folgt.
    #
    # Gemischte Clamp-Berechnung (Ruecksprache, praezisiert): NoBase-Modus
    # mischt zwei Stacker-Typen, jeder mit eigener Clamp-Zaehlung - keine
    # exklusive Wahl mehr:
    #   NoBase-Stacker (das Uebergangsstueck, = nobase_stacker Instanzen):
    #     bei stacker_span=2 (Aura-Standard, unveraendert) 3 NoBase-Clamps
    #     pro Instanz (oben/mitte/unten), weil die fehlenden Basements hier
    #     durch eine 3-Punkt-Anbindung kompensiert werden muessen.
    #     Bei stacker_span=3 (VENUS/JUPITER, Ruecksprache "spezielle Clamp-
    #     Regel fuer No Base"): nur die UNTEREN stacker_span Ankerpunkte
    #     (Boden + interne Fugen) sind NoBase-Clamps - die OBERSTE
    #     Befestigung (Anschluss zur Struktur ab der naechsten Reihe) ist
    #     stattdessen eine normale Clamp, mechanisch ein gewoehnlicher
    #     Stacker-zu-Stacker-Stoss wie bei Standard-Stacking. Diese eine
    #     Standard-Clamp pro Instanz wird oben in "clamps" mitgezaehlt
    #     (nobase_top_clamp), nicht in "nobase_clamps".
    #   Standard-Stacker (die regulaeren Baugruppen ab Reihe stacker_span+1,
    #     = stacker Instanzen): 2 Standard-Clamps pro Instanz, exakt wie bei
    #     Standard-Stacking. Standard-Clamps = 2 * stacker.
    # Beide Clamp-Typen werden separat gezaehlt und erscheinen beide in der
    # Stueckliste, da beide physisch verbaut werden.
    nobase_footbeams = math.ceil(width_cabinets / 2)

    has_transition = height_cabinets >= stacker_span
    nobase_stacker = nobase_footbeams if has_transition else 0

    if stacker_span == 2:
        nobase_clamps = 3 * nobase_stacker
        nobase_top_clamp = 0
    else:
        nobase_clamps = stacker_span * nobase_stacker
        nobase_top_clamp = nobase_stacker

    remaining_rows = max(0, height_cabinets - stacker_span)
    stacker_groups = remaining_rows // stacker_span
    stacker = nobase_footbeams * stacker_groups
    clamps = 2 * stacker + nobase_top_clamp

    components = {
        "basements_3": 0,
        "basements_2": 0,
        "basements_1": 0,
        "nobase_footbeams": nobase_footbeams,
        "nobase_stacker": nobase_stacker,
        "nobase_clamps": nobase_clamps,
        "stacker": stacker,
        "clamps": clamps,
    }
    # Ab sofort identische Statik-Hardware-Logik wie Standard-Stacking
    # (Ausleger/Diagonale/Pipe/Rohrschellen) - nobase_footbeams ist hier das
    # Aequivalent zu footbeams beim Standard-Stacking. VENUS (einziges
    # NoBase-faehiges Produkt aus VENUS_JUPITER_PRODUCT_IDS) nutzt auch hier
    # seine eigenen Hoehen-Schwellen.
    if product_id in VENUS_JUPITER_PRODUCT_IDS:
        components.update(_calculate_venus_jupiter_stacking_accessories(height_cabinets, nobase_footbeams, person_contact))
    else:
        components.update(_calculate_stacking_accessories(height_cabinets, nobase_footbeams, person_contact))
    return components


MAX_VANISH_STACKING_HEIGHT = 6  # Statik-Grenzwert (Ruecksprache): darueber nicht mehr umsetzbar
VANISH_STACKING_HEIGHT_LIMIT_ERROR = "ACHTUNG: Statik max. 6 m hoch"


def _calculate_vanish_mechanics(width_cabinets, height_cabinets):
    # Vanish-Stacking ist ein in sich geschlossenes Baukasten-System - hat
    # weder Basements/Footbeams/Single-Feet noch die Aura-Zubehoer-Logik
    # (Ausleger/Diagonale/Pipe/Rohrschellen). Genau 7 Bauteile, exakt nach
    # den vorgegebenen Formeln (B = Breite/Anzahl Spalten, H = Hoehe/Anzahl
    # Zeilen), am Beispiel Chronos:
    #   Stacking Bar (ROE-V8TBB1.0SRC):      B
    #   Foot Beam (ROE-XXXBT0.91RC):         B
    #   Unterster Stacker (ROE-XXXRT0.75RC): B
    #   Stacker (ROE-XXXRT1.0RC):            (H - 1) * B
    #   Verbinder (ROE-V8TRC):               H * B
    #   Splint (ROE-XXXTRSPRINGM) und
    #   Klammer (ROE-XXXTSPIGOTM) - beide identisch:
    #     2 * (Anzahl Stacking Bar) + 2 * (Anzahl Foot Beam)
    #       + 2 * (Anzahl Verbinder)
    b = width_cabinets
    h = height_cabinets

    stacking_bar = b
    foot_beam = b
    unterster_stacker = b
    stacker = (h - 1) * b
    verbinder = h * b
    splint_klammer = (2 * stacking_bar) + (2 * foot_beam) + (2 * verbinder)

    return {
        "stacking_bar": stacking_bar,
        "foot_beam": foot_beam,
        "unterster_stacker": unterster_stacker,
        "stacker": stacker,
        "verbinder": verbinder,
        "splint": splint_klammer,
        "klammer": splint_klammer,
    }


VANISH_HANGING_VALIDATION_NOTE = (
    "Statische Belastung des Traversensystems durch Anwender zu prüfen "
    "(1x Hanging Bar pro vertikaler Linie)."
)


def _calculate_vanish_hanging_mechanics(width_cabinets):
    # Finaler, exklusiver Hanging-Modus fuer Vanish V8T - ueberschreibt jede
    # vorherige Stacking-Betrachtung vollstaendig. Es gibt genau EINE
    # Stueckliste-Position (Hanging Bar = Breite B, 1x pro vertikaler
    # Linie). Alle Stacking-Bauteile aus _calculate_vanish_mechanics
    # (Stacker, Klammern, Splinte, Verbinder, Foot Beam, ...) sind hier
    # strukturell nicht vorhanden - kein Merge, kein Override einzelner
    # Felder, sondern ein komplett eigenes, frisches Dict pro Aufruf. Die
    # Hoehe (H) hat bewusst keinen Einfluss auf dieses System.
    return {"hanging_bar": width_cabinets}


def _calculate_ar_hanging_mechanics(width_cabinets, curving_mode=None):
    # AR3.9-Hanging (Produkt AR3.91 Plus LE, Korrektur): die Hanging Bar
    # gibt es in 3/2/1 Cabinet-Breiten - exakt dieselbe Breiten-Optimierung
    # (3-2-1 greedy) wie beim Aura-Konzept (siehe _optimal_basements),
    # NICHT 1:1 pro Cabinet-Spalte. Schluessel bewusst basements_3/2/1
    # genannt - gleiche Konvention wie bei Hanging-Truss
    # (_calculate_hanging_truss_mechanics), die Stueckliste zeigt sie unter
    # "Hanging Bar (3er/2er/1er)" (siehe MECHANICS_ROWS_BY_SYSTEM in
    # index.html). Hoehe (H) hat weiterhin keinen Einfluss. Curving-Modus:
    # nur der Breite-1-Zwang greift (kein neues Bauteil, siehe
    # _calculate_hanging_truss_mechanics).
    basements_3, basements_2, basements_1 = _apply_curving_width_split(width_cabinets, curving_mode)
    return {
        "basements_3": basements_3,
        "basements_2": basements_2,
        "basements_1": basements_1,
    }


def _get_cabinet_width_mm(conn, product_id):
    row = conn.execute(
        """
        SELECT ac.width_mm
        FROM configurator_product cp
        JOIN article_catalog_mock ac ON cp.product_article_id = ac.id
        WHERE cp.id = ?
        """,
        (product_id,),
    ).fetchone()
    return row["width_mm"] if row else None


# Cabinet-Hoehe wird gebraucht, seit es dasselbe Panel in zwei Bauhoehen gibt
# (500x1000 und 500x500, siehe ar_avora_500x500_setup.sql): Statik-Grenzen und
# die Laenge des Outdoor-Stackers sind physische Massangaben in Metern, keine
# Cabinet-Stueckzahlen - bei halber Cabinet-Hoehe passen in dieselbe Bauhoehe
# doppelt so viele Cabinets.
def _get_cabinet_height_mm(conn, product_id):
    row = conn.execute(
        """
        SELECT ac.height_mm
        FROM configurator_product cp
        JOIN article_catalog_mock ac ON cp.product_article_id = ac.id
        WHERE cp.id = ?
        """,
        (product_id,),
    ).fetchone()
    return row["height_mm"] if row else None


def calculate_mechanics(product_id, width_cabinets, height_cabinets, system_name, person_contact=False, location=None, curving_mode=None, curving_angle_deg=None, half_top_row=False):
    # half_top_row: oberste Reihe ist ein halbes Cabinet (500x500 auf einem
    # 1000er-Panel, siehe half_top_row_setup.sql). Sie braucht laut
    # Ruecksprache weder Stacker noch Clamp und geht deshalb NICHT in die
    # Stueckliste ein - height_cabinets zaehlt weiterhin nur die vollen
    # Reihen. Fuer die Statik zaehlt sie aber sehr wohl mit: eine Wand aus
    # 6 vollen + 1 halben Cabinet ist 6,5 m hoch, nicht 6 m.
    # curving_mode wird ausschliesslich fuer die vier Basement/Truss-Systeme
    # (CURVING_CAPABLE_SYSTEMS) sowie additiv fuer LIAM-Truss ausgewertet -
    # alle anderen Systeme ignorieren ihn (Wert bleibt "flat"/None, kein
    # Verhaltensunterschied zu vorher). "flat" wird wie "kein Curving"
    # behandelt.
    curving_mode = curving_mode if curving_mode in ("concave", "convex") else None
    if curving_mode is not None:
        if system_name not in CURVING_CAPABLE_SYSTEMS | {"LIAM-Truss"}:
            return {"error": CURVING_UNSUPPORTED_ERROR}
        allowed_degrees = CURVING_DEGREE_STEPS_BY_PRODUCT.get(product_id, [])
        if curving_angle_deg not in allowed_degrees:
            return {"error": CURVING_ANGLE_INVALID_ERROR}

    conn = get_db_connection()
    try:
        if not _product_uses_system(conn, product_id, system_name):
            return None

        stacking_setup_label = None
        validation_note = None
        grid = None
        stacker_band_rows = None
        ballast = None
        if system_name in ("Standard-Stacking", "NoBase", "AR-Stacking", "Flex-Stacking", AR_OUTDOOR_STACKING_SYSTEM):
            # Alle vier Systeme teilen sich dieselbe Statik-Hardware-Logik
            # (Hoehen-Limit, Ausleger/Diagonale/Pipe/Rohrschellen) - AR3.9
            # (AR-Stacking) und AURA FLEX (Flex-Stacking) uebernehmen diese
            # 1:1 von der Aura-Konfiguration, siehe _calculate_ar_stacking_
            # mechanics / _calculate_aura_flex_mechanics. Der Hoehen-Grenzwert
            # selbst kommt pro Produkt aus MAX_STACKING_HEIGHT_BY_PRODUCT.
            # Fehlt er (Produkt an dieses System angebunden, aber kein
            # Grenzwert hinterlegt), ist der Aufbau sicherheitshalber nicht
            # umsetzbar.
            max_stacking_height = MAX_STACKING_HEIGHT_BY_PRODUCT.get(product_id)
            # Cabinet-Bauhoehe: 1000 mm im AR-/Avora-Standard, 500 mm bei den
            # halben Cabinets. Wird sowohl fuer die Hoehengrenze als auch fuer
            # die Stacker-Laenge gebraucht (siehe _ar_stacker_span_rows).
            cabinet_height_mm = _get_cabinet_height_mm(conn, product_id) or AR_REFERENCE_CABINET_HEIGHT_MM
            # Neue AR3.9-Statiktabelle (Ruecksprache): AR3.91 Plus LE,
            # AR 10.41 und Avora Root duerfen Indoor nur noch 6 m hoch gebaut
            # werden (echte Statik, ersetzt den alten 12er-Platzhalter fuer
            # AR3.9/AR10.41) - Outdoor hat eine eigene, noch nicht hinterlegte
            # Statik und bleibt beim bisherigen Grenzwert. Der Grenzwert ist
            # eine BAUHOEHE: bei halben Cabinets sind das doppelt so viele
            # Cabinets (6 -> 12), deshalb ueber die Cabinet-Hoehe umgerechnet.
            if product_id in NEW_AR_STACKING_PRODUCT_IDS and location == "indoor":
                max_stacking_height = (
                    NEW_AR_STACKING_INDOOR_MAX_HEIGHT
                    * AR_REFERENCE_CABINET_HEIGHT_MM
                    // cabinet_height_mm
                )
            # Eine halbe oberste Reihe traegt zwar keine Mechanik, macht die
            # Wand aber trotzdem hoeher - fuer den Grenzwert zaehlt sie
            # deshalb als angebrochene volle Reihe (sicherheitsgerichtet
            # aufgerundet).
            statics_rows = height_cabinets + (1 if half_top_row else 0)
            if max_stacking_height is None or statics_rows > max_stacking_height:
                return {"error": STACKING_HEIGHT_LIMIT_ERROR}
            # stacker_span: 2 fuer die meisten Produkte (Aura-Konzept), 3 fuer
            # VENUS/JUPITER (siehe STACKER_SPAN_BY_PRODUCT) - gilt sowohl fuer
            # Standard-Stacking als auch fuer den regulaeren Stacker oberhalb
            # des NoBase-Uebergangsstuecks, da es physisch dasselbe Bauteil ist.
            stacker_span = STACKER_SPAN_BY_PRODUCT.get(product_id, 2)
            stacker_band_rows = stacker_span
            if system_name == "Standard-Stacking":
                components = _calculate_aura_mechanics(width_cabinets, height_cabinets, person_contact, curving_mode, stacker_span, product_id, location)
            elif system_name == "NoBase":
                # NoBase ist nicht curving-faehig (siehe CURVING_CAPABLE_SYSTEMS) -
                # curving_mode wurde oben bereits als None normalisiert, falls
                # das Frontend ihn faelschlich mitschickt, greift die
                # Validierung am Funktionsanfang.
                components = _calculate_nobase_mechanics(width_cabinets, height_cabinets, person_contact, stacker_span, product_id)
            elif system_name == "Flex-Stacking":
                # Flex ist ebenfalls nicht curving-faehig (nicht in
                # CURVING_CAPABLE_SYSTEMS gelistet) - curving_mode wurde oben
                # bereits als None normalisiert.
                components = _calculate_aura_flex_mechanics(width_cabinets, height_cabinets, person_contact, stacker_span)
            else:
                # "AR-Stacking" (Indoor) und "AR-Outdoor-Stacking" teilen sich
                # denselben Rechenweg - Unterschiede sind allein die
                # Artikelnummern (siehe AR_OUTDOOR_STACKING_SYSTEM) und der
                # fehlende Single Foot im Outdoor-Baukasten.
                components = _calculate_ar_stacking_mechanics(
                    width_cabinets, height_cabinets, person_contact, curving_mode, location,
                    include_single_feet=system_name != AR_OUTDOOR_STACKING_SYSTEM,
                    cabinet_height_mm=cabinet_height_mm,
                )
                # Die AR-Systeme haben ihre eigene Stacker-Spannweite (1 m
                # Bauteil, siehe _ar_stacker_span_rows) - sie ersetzt den
                # generischen Aura-Wert, damit die Visualisierung den
                # Stacker-Balken genauso hoch zeichnet, wie die Stueckliste
                # ihn zaehlt.
                stacker_band_rows = _ar_stacker_span_rows(cabinet_height_mm)
            # Die Pipe ist ein einzelnes durchgehendes Bauteil ueber die
            # gesamte Wandbreite - Laenge in Metern statt Stueckzahl.
            if components["pipe_count"] > 0:
                cabinet_width_mm = _get_cabinet_width_mm(conn, product_id)
                components["pipe_length_m"] = round((cabinet_width_mm * width_cabinets) / 1000, 2)
            else:
                components["pipe_length_m"] = 0
            # Ballast (Ballast.pdf, LANG AG): kg pro Stacker-Achse * Anzahl
            # Achsen - eine Achse ist ein Footbeam-Ankerpunkt, bei NoBase
            # heisst das Feld "nobase_footbeams" statt "footbeams" (siehe
            # _calculate_nobase_mechanics), sonst identisch. None, wenn fuer
            # Produkt/Hoehe noch keine Ballast-Daten hinterlegt sind (siehe
            # BALLAST_TABLE_BY_PRODUCT) - Frontend zeigt dann "keine Daten
            # hinterlegt" statt einer geschaetzten Zahl.
            stacker_axis_count = components["nobase_footbeams"] if system_name == "NoBase" else components["footbeams"]
            ballast = _calculate_ballast(product_id, height_cabinets, stacker_axis_count)
            if system_name in ("AR-Stacking", AR_OUTDOOR_STACKING_SYSTEM):
                stacking_setup_label = _ar_stacking_setup_label(height_cabinets, person_contact, location)
            elif product_id in NEW_AR_STACKING_PRODUCT_IDS and location == "indoor":
                # Nur Avora Root (20) erreicht diesen Zweig - AR3.91/AR10.41
                # sind bereits oben ueber system_name == "AR-Stacking"
                # abgedeckt. Generische Bezeichnung "Rohrschellen" (Default),
                # da Avora Root ueber Standard-Stacking laeuft.
                stacking_setup_label = _new_ar_stacking_setup_label(height_cabinets, person_contact)
            elif product_id in VENUS_JUPITER_PRODUCT_IDS:
                stacking_setup_label = _venus_jupiter_stacking_setup_label(height_cabinets, person_contact)
            elif product_id in ENKI_PRODUCT_IDS:
                stacking_setup_label = _enki_stacking_setup_label(height_cabinets, person_contact)
            else:
                stacking_setup_label = _stacking_setup_label(height_cabinets, person_contact)
        elif system_name == "Hanging-Truss":
            if product_id in VENUS_JUPITER_PRODUCT_IDS:
                # VENUS/JUPITER: eigenes Modell (Zusatz-Oese nur fuers
                # 3er-Modul, siehe _calculate_venus_jupiter_hanging_mechanics)
                # statt des generischen einheitlichen Oesen-Tiers.
                if height_cabinets > VENUS_JUPITER_HANGING_MAX_HEIGHT:
                    return {"error": HANGING_STATIK_LIMIT_ERROR}
                components = _calculate_venus_jupiter_hanging_mechanics(
                    width_cabinets, height_cabinets, curving_mode
                )
                stacking_setup_label = _venus_jupiter_hanging_setup_label(components["zusatz_oese"])
            elif product_id in ENKI_PRODUCT_IDS:
                # ENKI: das schwaechste vorkommende Modul (insbesondere ein
                # 3er-Modul) begrenzt die gesamte Wandhoehe, siehe
                # _calculate_enki_hanging_max_height.
                basements_3, _, _ = _apply_curving_width_split(width_cabinets, curving_mode)
                max_height = _calculate_enki_hanging_max_height(basements_3)
                if height_cabinets > max_height:
                    return {"error": HANGING_STATIK_LIMIT_ERROR}
                components = _calculate_enki_hanging_mechanics(width_cabinets, height_cabinets, curving_mode)
                stacking_setup_label = _enki_hanging_setup_label(
                    components["basements_3"], components["basements_2"], height_cabinets
                )
            else:
                oesen_per_point = _calculate_hanging_oesen_per_point(height_cabinets, product_id)
                if oesen_per_point is None:
                    return {"error": HANGING_STATIK_LIMIT_ERROR}
                components = _calculate_hanging_truss_mechanics(width_cabinets, oesen_per_point, curving_mode)
                oesen_word = "Öse" if oesen_per_point == 1 else "Ösen"
                stacking_setup_label = f"Truss-System mit {oesen_per_point} {oesen_word}"
        elif system_name == "Flex-Hanging":
            # Aura Flex Hanging: identische Statik-Hoehengrenze wie AURA
            # (product_id 16 gehoert zu HARMONIZED_HANGING_STATICS_PRODUCT_
            # IDS), aber eigene Truss-Zaehlung statt der 3-2-1-Verteilung
            # (siehe _calculate_aura_flex_hanging_mechanics). Nicht curving-
            # faehig (nicht in CURVING_CAPABLE_SYSTEMS gelistet) - curving_
            # mode wurde oben bereits als None normalisiert.
            oesen_per_point = _calculate_hanging_oesen_per_point(height_cabinets, product_id)
            if oesen_per_point is None:
                return {"error": HANGING_STATIK_LIMIT_ERROR}
            components = _calculate_aura_flex_hanging_mechanics(width_cabinets, oesen_per_point)
            oesen_word = "Öse" if oesen_per_point == 1 else "Ösen"
            stacking_setup_label = f"Truss-System mit {oesen_per_point} {oesen_word}"
        elif system_name == "LIAM-Truss":
            # Eigenstaendiges Hanging-Only-Modul (liam_truss.py) - kein
            # Stacking, keine Beruehrung mit der Aura-Zubehoer-Logik. width_
            # /height_cabinets sind fuer LIAM identisch zu Metern (1 LIAM-
            # Cabinet = 1m x 1m), location ('indoor'/'outdoor') steuert
            # Ebenen-Raster und Outdoor-Sicherheitsfaktor.
            result = calculate_liam_truss_mechanics(width_cabinets, height_cabinets, location, curving_mode)
            components = result["components"]
            validation_note = result["validation_note"]
            grid = result["grid"]
        elif system_name == "Vanish-Stacking":
            # Eigenstaendiges, geschlossenes System - bewusst KEINE
            # Beruehrung mit der Aura-Zubehoer-Logik (Ausleger, Diagonale,
            # Pipe, Rohrschellen) und keine Aura-Statik-Hoehengrenze
            # (MAX_STACKING_HEIGHT_BY_PRODUCT gilt hier nicht). Eigener,
            # blockierender Statik-Grenzwert (Ruecksprache: "mehr ist
            # statisch nicht moeglich") - oberhalb von MAX_VANISH_STACKING_
            # HEIGHT wird der Aufbau NICHT mehr berechnet, analog zu
            # STACKING_HEIGHT_LIMIT_ERROR bei den anderen Stacking-Systemen.
            if height_cabinets > MAX_VANISH_STACKING_HEIGHT:
                return {"error": VANISH_STACKING_HEIGHT_LIMIT_ERROR}
            components = _calculate_vanish_mechanics(width_cabinets, height_cabinets)
        elif system_name == "Vanish-Hanging":
            # Finaler, exklusiver Hanging-Modus fuer Vanish V8T - ersetzt
            # jede Stacking-Betrachtung vollstaendig (frisches Dict, siehe
            # _calculate_vanish_hanging_mechanics). Hoehe (H) hat hier
            # bewusst keinen Einfluss.
            components = _calculate_vanish_hanging_mechanics(width_cabinets)
            validation_note = VANISH_HANGING_VALIDATION_NOTE
        elif system_name == "AR-Hanging":
            # AR3.9-Hanging: Hanging Bar in 3-2-1-Breiten-Optimierung wie
            # beim Aura-Konzept (siehe _calculate_ar_hanging_mechanics) -
            # KEIN "1x pro vertikaler Linie" mehr (das war das alte 1:1-
            # Modell, siehe Vanish-Hanging), daher auch keine
            # VANISH_HANGING_VALIDATION_NOTE hier. Hoehe (H) hat weiterhin
            # keinen Einfluss.
            components = _calculate_ar_hanging_mechanics(width_cabinets, curving_mode)
        else:  # "Wandadapter"
            components = _calculate_wandadapter_mechanics(width_cabinets, height_cabinets)

        return {
            "system": system_name,
            "components": components,
            "stacking_setup_label": stacking_setup_label,
            "validation_note": validation_note,
            "grid": grid,
            # Echo, damit Frontend-Stueckliste/Visualizer denselben Zustand
            # sehen wie das Backend, das die Komponenten berechnet hat.
            "curving_mode": curving_mode,
            "curving_angle_deg": curving_angle_deg if curving_mode is not None else None,
            # Wie viele Cabinet-Reihen EIN Stacker ueberspannt - Echo fuers
            # Frontend, damit der Canvas-Visualizer (Standard-Stacking/
            # NoBase) dieselbe Spannweite zeichnet wie das Backend rechnet
            # (2 = Aura-Standard, 3 = VENUS/JUPITER, siehe
            # STACKER_SPAN_BY_PRODUCT). None fuer alle anderen Systeme.
            "stacker_band_rows": stacker_band_rows,
            # Ballast (Ballast.pdf): nur fuer die vier Aura-basierten
            # Stacking-Systeme gesetzt (siehe BALLAST_TABLE_BY_PRODUCT) -
            # None fuer alle anderen Systeme (Hanging/Wandadapter/Vanish-*)
            # UND wenn fuer Produkt/Hoehe noch keine Daten hinterlegt sind.
            "ballast": ballast,
        }
    finally:
        conn.close()


@app.route("/api/mechanics-options")
def api_mechanics_options():
    # Liefert pro Produkt, welche der drei festen UI-Modi (Stacking/Hanging/
    # Wall-Adapter) ueberhaupt sichtbar sein sollen, und welche Systeme sich
    # jeweils dahinter verbergen. Ein Modus taucht nur auf, wenn das Produkt
    # mindestens ein System in diesem Modus unterstuetzt (product_mechanics)
    # - z.B. hat Vanish V8T nur "Stacking" (exklusiv Vanish-Stacking, kein
    # NoBase/Wandadapter), waehrend die Aura-Familie "Stacking" mit zwei
    # Systemen (Standard-Stacking/NoBase) sowie "Hanging" und "Wall-Adapter"
    # anbietet. Das Frontend rendert Modus-Buttons nur fuer die
    # zurueckgelieferten Eintraege und eine Sub-Auswahl nur, wenn ein Modus
    # mehr als ein System enthaelt.
    product_id = request.args.get("product_id", type=int)
    if product_id is None:
        return jsonify({"error": "product_id ist erforderlich"}), 400
    # Einsatzort steuert zusaetzlich, welche Systeme ueberhaupt angeboten
    # werden (siehe SYSTEM_LOCATION_ONLY) - Outdoor bekommt die AR-Familie
    # den ER-Baukasten statt des Indoor-Systems.
    location = request.args.get("location")

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT ms.ui_mode AS mode, ms.name AS system_name
        FROM product_mechanics pm
        JOIN mechanical_systems ms ON ms.id = pm.system_id
        WHERE pm.product_id = ?
        ORDER BY ms.id
        """,
        (product_id,),
    ).fetchall()
    conn.close()

    systems_by_mode = {}
    for row in rows:
        # Systeme, die an einen anderen Einsatzort gebunden sind, fallen raus.
        required_location = SYSTEM_LOCATION_ONLY.get(row["system_name"])
        if required_location is not None and required_location != location:
            continue
        systems_by_mode.setdefault(row["mode"], []).append(row["system_name"])

    # Ist ein einsatzort-exklusives System uebrig geblieben, verdraengt es die
    # von ihm abgeloesten Indoor-Systeme, statt zusaetzlich zur Wahl zu stehen.
    replaced = set()
    for systems in systems_by_mode.values():
        for name in systems:
            replaced |= SYSTEM_REPLACED_BY.get(name, set())
    if replaced:
        for mode, systems in systems_by_mode.items():
            systems_by_mode[mode] = [name for name in systems if name not in replaced]
        systems_by_mode = {mode: systems for mode, systems in systems_by_mode.items() if systems}

    mode_order = ["Stacking", "Hanging", "Wall-Adapter"]
    modes = [
        {"mode": mode, "systems": systems_by_mode[mode]}
        for mode in mode_order
        if mode in systems_by_mode
    ]
    # Gradstufen fuers Curving-Dropdown (Frontend) - leeres Array bedeutet
    # "Produkt unterstuetzt kein Curving", das Dropdown bleibt dann
    # versteckt, unabhaengig vom gewaehlten System.
    curving_degree_steps = CURVING_DEGREE_STEPS_BY_PRODUCT.get(product_id, [])
    return jsonify({"modes": modes, "curving_degree_steps": curving_degree_steps})


@app.route("/api/calculate_mechanics")
def api_calculate_mechanics():
    product_id = request.args.get("product_id", type=int)
    width_cabinets = request.args.get("width_cabinets", type=int)
    height_cabinets = request.args.get("height_cabinets", type=int)
    system_name = request.args.get("system_name")
    person_contact = request.args.get("person_contact", "").lower() in ("1", "true")
    location = request.args.get("location")  # "indoor" | "outdoor" - nur fuer LIAM-Truss relevant
    curving_mode = request.args.get("curving_mode")  # "flat" | "concave" | "convex"
    curving_angle_deg = request.args.get("curving_angle_deg", type=float)
    # Oberste Reihe als halbes Cabinet (siehe calculate_mechanics)
    half_top_row = request.args.get("half_top_row", "").lower() in ("1", "true")

    if product_id is None or width_cabinets is None or height_cabinets is None or not system_name:
        return jsonify({"error": "product_id, width_cabinets, height_cabinets und system_name sind erforderlich"}), 400
    if width_cabinets < 1 or height_cabinets < 1:
        return jsonify({"error": "width_cabinets und height_cabinets muessen >= 1 sein"}), 400

    result = calculate_mechanics(
        product_id, width_cabinets, height_cabinets, system_name, person_contact, location,
        curving_mode, curving_angle_deg, half_top_row,
    )
    if result is None:
        return jsonify({"error": f"Produkt unterstuetzt das System '{system_name}' nicht"}), 400
    if "error" in result:
        return jsonify({"error": result["error"]}), 400

    return jsonify({
        "product_id": product_id,
        "width_cabinets": width_cabinets,
        "height_cabinets": height_cabinets,
        "system": result["system"],
        "components": result["components"],
        "stacking_setup_label": result["stacking_setup_label"],
        "validation_note": result["validation_note"],
        "grid": result["grid"],
        "curving_mode": result["curving_mode"],
        "curving_angle_deg": result["curving_angle_deg"],
        "stacker_band_rows": result["stacker_band_rows"],
        "ballast": result["ballast"],
    })


if __name__ == "__main__":
    # Host/Port/Debug per Umgebungsvariable, damit derselbe Start auch fuer
    # den Zugriff von aussen taugt (Cloudflare-Tunnel, siehe start_tunnel.ps1).
    #
    # WICHTIG: debug ist standardmaessig AUS. Der Werkzeug-Debugger blendet bei
    # jedem Fehler eine interaktive Python-Konsole ein - waere der Konfigurator
    # damit oeffentlich erreichbar, koennte darueber beliebiger Code auf diesem
    # Rechner ausgefuehrt werden. Fuer die lokale Entwicklung bewusst wieder
    # einschaltbar:  $env:KONFIGURATOR_DEBUG = "1"
    debug = os.environ.get("KONFIGURATOR_DEBUG") == "1"
    host = os.environ.get("KONFIGURATOR_HOST", "127.0.0.1")
    port = int(os.environ.get("KONFIGURATOR_PORT", "5000"))
    app.run(host=host, port=port, debug=debug)