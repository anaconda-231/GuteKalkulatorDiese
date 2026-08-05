"""
LIAM-Traversensystem: eigenstaendiges Mechanik-Modul fuer den LIAM-Hanging-
Modus. Bewusst getrennt von server.py's Stacking/Hanging-Logik (Aura-Konzept,
Vanish), da LIAM ausschliesslich haengt - es gibt kein Stacking und keine der
dortigen Stacking-Bauteile (Basements, Footbeams, Stacker, Clamps, ...).

Struktur (Ebenen-Positionen ueber _raster_positions_from_top mit
Indoor-Raster=2m / Outdoor-Raster=1m - dieser Ebenen-Raster steuert
AUSSCHLIESSLICH, WIE VIELE horizontale Ebenen es gibt, NICHT wie eine
einzelne Ebene intern aus Modulen zusammengesetzt ist, siehe naechster
Punkt):
  - B vertikale LIAM-Truss-Strings, jeder endet oben mit genau einer
    LIAM-Hanging-Bar. Die oberste Verbindung der Strings ist AUSSCHLIESSLICH
    die Hanging-Bar - direkt am oberen Rand gibt es keine horizontale
    Traversen-Ebene. Die unterste Ebene liegt IMMER exakt am Boden (0m) -
    _raster_positions_from_top kappt die letzte Position garantiert auf 0.
  - Pro horizontaler Ebene werden die B Strings NICHT durch eine einzelne
    durchgehende Linie verbunden, sondern durch einzelne horizontale
    Bruecken-Segmente. Ein Corner-Knoten entsteht nur dort, wo eine Bruecke
    tatsaechlich an einem String endet - bei 2m-Schrittweite ueberspringt
    eine Bruecke einen dazwischenliegenden String (der dort auf dieser
    Ebene nur 'Truss' ist, kein Corner). Die Bauweise EINER Ebene ist
    zwischen Indoor und Outdoor bewusst UNTERSCHIEDLICH:
      Indoor: JEDE Ebene folgt demselben Muster (BRIDGE_RASTER_M=2m) -
      links nach rechts zuerst 2m-Bruecken, ein 1m-Rest ausschliesslich als
      Abschluss ganz rechts.
      Outdoor (final, Ruecksprache): die Ebenen wechseln sich im Muster
      1m-Reihe/2m-Reihe strikt ab, gezaehlt von OBEN nach UNTEN - Ebene 1
      (ganz oben, direkt unter den Hanging-Bars) ist eine reine 1m-Reihe
      (jede Spalte ist auf dieser Ebene Corner), Ebene 2 eine reine
      2m-Reihe (links nach rechts 2m-Bruecken, 1m-Rest ganz rechts falls B
      ungerade), Ebene 3 wieder 1m, Ebene 4 wieder 2m usw. (siehe
      _outdoor_row_types). Sonderregel "letzte Reihe": unabhaengig vom
      Alternations-Rhythmus ist die ALLERLETZTE Ebene (die Boden-Ebene bei
      0m) immer zwingend eine 2m-Reihe.
    Welche Strings insgesamt eine eigene vertikale 2m/1m-Zerlegung bekommen,
    ist die Vereinigungsmenge aller ueber alle Ebenen beruehrten Spalten -
    bei Outdoor sorgt allein schon die erste 1m-Reihe (Ebene 1) dafuer, dass
    das (ausser im Sonderfall einer einzigen Ebene) immer alle B Spalten
    sind.
  - Corner-Exklusivitaet (Ruecksprache, unveraenderliche Regel, strikte
    Trennung von Corner und Clamp): ein LIAM-Truss-Corner darf NUR an einem
    physischen Modul-Endpunkt entstehen, an dem sich ein vertikales UND ein
    horizontales Modul-ENDE tatsaechlich treffen (da, wo die Bolzen sitzen)
    - NIE mittig auf einem Truss-System-2m-Modul, selbst wenn sich dort
    rechnerisch eine vertikale und eine horizontale Linie kreuzen wuerden.
    Fuer Indoor ist das automatisch immer der Fall (INDOOR_RASTER_M ==
    BRIDGE_RASTER_M == 2, jede Ebene liegt also zwangslaeufig auf einer
    vertikalen Modul-Grenze). Fuer Outdoor NICHT automatisch, weil die
    Ebenen (1m-Raster) enger stehen als die vertikalen 2m-Modul-Grenzen:
    eine '2m'-Ebene (siehe oben) liegt dank der identischen Konstruktion
    von _outdoor_row_types und den vertikalen Modul-Grenzen (beide zaehlen
    vom oberen Rand in 2m-Schritten abwaerts, mit derselben Kappung auf 0
    ganz unten) IMMER exakt auf einer echten vertikalen Modul-Grenze - dort
    entstehen also echte Corner. Eine '1m'-Ebene liegt dagegen IMMER exakt
    in der Mitte eines vertikalen 2m-Moduls - jede Beruehrung dort ist KEIN
    Corner, sondern eine LIAM-Clamp (Alternative-Regel). Ebenso wird die
    von einer 2m-Bruecke uebersprungene Mitte eines horizontalen 2m-Moduls
    NIE zum Corner, sondern zur Clamp. Ergebnis: auf jeder Ebene ist jede
    Spalte entweder Corner oder Clamp, niemals beides und nie unmarkiert.

Stueckliste - Hanging-Bar ist fuer Indoor/Outdoor nach demselben
Grundmodell berechnet (1x je Spalte). Corner unterscheidet sich bewusst:
Indoor zaehlt JEDE beruehrte Spalte jeder Ebene (dort immer ein echter
Endpunkt, s.o.); Outdoor zaehlt NUR die Beruehrungen auf '2m'-Ebenen (die
auf '1m'-Ebenen werden zu Clamp umklassifiziert, s.o.). Truss-2m/1m
unterscheidet sich in der Bauweise JE Ebene bewusst zwischen Indoor (immer
BRIDGE_RASTER_M) und Outdoor (alternierendes 1m-/2m-Zeilenschema, s.o.).
Conn/Bolzen/Clamp/Nut unterscheiden sich ebenfalls bewusst zwischen Indoor
und Outdoor:
  Outdoor (Ruecksprache, final/unveraenderlich):
    - Truss-2m/1m = Summe ueber alle Ebenen gemaess alternierendem
      Zeilenschema (1m-Reihe traegt nur zu Truss-1m bei, 2m-Reihe zu
      Truss-2m plus ggf. 1x Truss-1m als Rest-Abschluss falls B ungerade)
      PLUS die vertikale Zerlegung der insgesamt beruehrten Spalten (s.o.).
    - Corner = Summe ueber alle '2m'-Ebenen der dort beruehrten Spalten
      (echte Modul-End-Schnittpunkte, s.o.) - Beruehrungen auf '1m'-Ebenen
      zaehlen NICHT mit (siehe Clamp).
    - Conn = exakt B - genau 1x je String-Oberkante (koppelt vertikalen
      String mit seiner Hanging-Bar). KEINE internen Modul-Verbinder mehr
      Teil dieser Zahl (Korrektur - vorherige Version zaehlte zusaetzlich
      Modul-zu-Modul-Stoesse mit, das ist jetzt bewusst entfernt).
    - Clamp = Corner (Korrektur, Ruecksprache: "ueberall wo ein Corner ist,
      muss auch eine Clamp sein" - Corner und Clamp sind NICHT exklusiv,
      jeder Corner-Knoten bekommt zusaetzlich zur Bolzenverbindung eine
      eigene Clamp) PLUS exakt 1x in der exakten Mitte jedes Truss-System-
      2m-Moduls (vertikal UND horizontal) = liam_truss_2m (NICHT zusaetzlich
      die Beruehrungen auf '1m'-Ebenen separat aufaddieren - die sind
      mathematisch identisch mit der vertikalen 2m-Modul-Zerlegung und
      damit schon in liam_truss_2m enthalten, sonst doppelt gezaehlt).
      Ergebnis: jede Spalte jeder Ebene bekommt eine Clamp, an echten
      Modul-Enden zusaetzlich einen Corner (Grid: Clamp-Marker liegt dort
      sichtbar hinter dem Corner-Marker).
    - Bolzen: JEDE Verbindung - Corner UND (Modul-Mitten-)Clamp
      gleichermassen, zusammen exakt levels*width_m Punkte - bekommt 2
      Bolzen, Typ nach Knotentyp wie Indoor (s.u.): an einer INTERIOR Spalte (nicht
      die erste/letzte der insgesamt beruehrten Spalten) UND auf einer
      NICHT-Boden-Ebene (echtes Kreuz, 4 Traversen treffen zusammen) sitzen
      2x Bold-150; an allen uebrigen Verbindungen (Rand-Spalte ODER
      Boden-Ebene) sitzen 2x Bold-100. NICHT mehr an Conn gekoppelt.
    - Nut = 4x je Corner + 2x je Conn + 1x je Bolzen (100 oder 150) -
      dasselbe Grundmodell wie Indoor (s.u.), nicht mehr Cabinet-basiert.
  Indoor (Ruecksprache): LIAM-Truss-Clamp bleibt entfernt (keine Berechnung/
  Stueckliste/Visualisierung). LIAM-Truss-Conn ist als reiner
  Stueckliste-Wert wieder da - OHNE Visualisierung (kein Grid-Marker):
    - Conn = 1 je ungerader Hanging-Bar-Spalte (1-indexiert: 1, 3, 5, ...)
      PLUS 1 an der letzten Spalte B, falls B gerade ist. B=5 -> Spalten
      1,3,5 (3 Stueck); B=6 -> Spalten 1,3,5,6 (4 Stueck).
    - Bolzen unterscheiden nach Knotentyp: an einem Corner, an dem 4
      Traversen zusammentreffen (echtes Kreuz = interior Corner-Spalte UND
      nicht die Boden-Ebene), sitzen 2x Bold-150; an allen uebrigen Corner
      (Rand-Spalte ODER Boden-Ebene = nur 3 Traversen treffen zusammen)
      sitzen 2x Bold-100.
    - Nut = 4 je Corner + 2 je Conn + 1 je Bolzen (100 oder 150).
"""
import math

INDOOR_RASTER_M = 2
OUTDOOR_RASTER_M = 1

# Bauweise EINER "2m-Reihe" (links nach rechts: 2m-Module zuerst, ein
# 1m-Rest ausschliesslich als Abschluss ganz rechts) - bewusst UNABHAENGIG
# vom Ebenen-Raster (INDOOR_RASTER_M/OUTDOOR_RASTER_M, der nur steuert, wie
# viele Ebenen es uebereinander gibt). Indoor nutzt dieses Muster fuer JEDE
# Ebene; Outdoor nutzt es nur fuer die "2m-Reihen" des alternierenden
# Zeilenschemas (siehe _outdoor_row_types) - dessen "1m-Reihen" werden
# stattdessen mit Raster=1 gebaut (jede Spalte ist Corner, reines
# OUTDOOR_RASTER_M-Muster, siehe _bridge_positions_for_row).
BRIDGE_RASTER_M = 2

# Sicherheitsfaktor fuer die Outdoor-Skalierung der sicherheitsrelevanten
# Verbinder (LIAM-Truss-Conn, LIAM-Truss-Bold-100/150) gemaess Windlast-
# vorgaben. Reale Datenblatt-Werte liegen von der LANG AG noch nicht vor -
# bis dahin bleibt der Faktor bei 1.0 (Ruecksprache, keine Skalierung), soll
# aber leicht austauschbar bleiben, sobald die Werte vorliegen.
OUTDOOR_SAFETY_FACTOR = 1.0

VALIDATION_NOTE = (
    "Statische Belastung des Traversensystems durch Anwender zu prüfen "
    "(1x Hanging Bar pro vertikaler Linie)."
)


def _line_modules(length_m):
    # Greedy-Laengenoptimierung einer einzelnen Linie (vertikal ODER
    # horizontal, Laenge in Metern): so viele 2m-Module wie moeglich, ein
    # 1m-Modul fuer den Rest. Verbinder sitzen zwischen zwei aufeinander-
    # folgenden Modulen derselben Linie -> (Modulanzahl - 1). Eine Linie aus
    # genau einem Modul braucht keinen Verbinder.
    truss_2m = length_m // 2
    truss_1m = length_m % 2
    connectors = max((truss_2m + truss_1m) - 1, 0)
    return truss_2m, truss_1m, connectors


def _raster_positions(span_m, raster_m):
    # Raster-Schrittfunktion fuer die horizontale Achse (Bruecken-Positionen
    # zwischen dem ersten und letzten String, span_m=B-1): Positionen bei 0,
    # Raster, 2*Raster, ..., letzte Position auf span_m gekappt. Da Raster
    # nie exakt in span_m aufgeht, wenn aufgerundet wurde, bleibt die
    # gekappte letzte Position garantiert von der vorletzten verschieden
    # (keine doppelte Position). span_m=0 (z.B. B=1, keine Nachbarn) liefert
    # genau eine Position (0).
    steps = math.ceil(span_m / raster_m) + 1
    return [min(i * raster_m, span_m) for i in range(steps)]


def _raster_positions_from_top(span_m, raster_m):
    # Ebenen-Positionen (Indoor UND Outdoor, nur raster_m unterscheidet
    # sich): gezaehlt wird vom OBEREN Rand nach unten, nicht vom Boden nach
    # oben. Der obere Rand selbst (span_m) ist bewusst NICHT in der Liste -
    # dort sitzt ausschliesslich die Hanging-Bar. Die erste Ebene liegt bei
    # span_m - raster_m, danach im Raster-Abstand weiter abwaerts. Die
    # letzte (unterste) Position wird auf 0 gekappt und ist damit IMMER
    # Teil des Ergebnisses (das unterste Raster-Vielfache liegt wegen
    # steps=ceil(span_m/raster_m) immer bei <= 0). Da raster_m*(steps-1) <
    # span_m garantiert gilt, ist die vorletzte Position immer > 0 und damit
    # von der gekappten letzten (0) verschieden - keine doppelte Position.
    steps = math.ceil(span_m / raster_m)
    positions = [span_m - raster_m * i for i in range(1, steps + 1)]
    if positions:
        positions[-1] = max(positions[-1], 0)
    return positions


def _outdoor_row_types(levels):
    # Alternierendes Zeilenschema fuer Outdoor (Ruecksprache, final):
    # level_y_positions ist top-down sortiert (Index 0 = Ebene 1 = oberste
    # Ebene direkt unter den Hanging-Bars, letzter Index = Boden-Ebene) -
    # dieselbe Reihenfolge gilt hier. Ebene 1 = '1m', danach strikt
    # abwechselnd '2m'/'1m'/... (gerader Index -> '1m', ungerader -> '2m').
    # Sonderregel "letzte Reihe": die Boden-Ebene (letzter Eintrag) wird
    # IMMER auf '2m' erzwungen, unabhaengig davon, wo die Alternation sie
    # sonst hingelegt haette - auch wenn dadurch zwei '2m'-Reihen direkt
    # aufeinanderfolgen. Bei genau 1 Ebene (levels=1) ist diese eine Ebene
    # gleichzeitig Ebene 1 UND Boden-Ebene -> die Sonderregel gewinnt, sie
    # wird '2m'.
    row_types = ["1m" if i % 2 == 0 else "2m" for i in range(levels)]
    if row_types:
        row_types[-1] = "2m"
    return row_types


def _bridge_positions_for_row(width_m, row_type):
    # Bruecken-Positionen EINER Ebene gemaess ihrem Zeilentyp: '1m' baut mit
    # Raster=1 (jede Spalte ist Corner, siehe OUTDOOR_RASTER_M), '2m' baut
    # mit Raster=BRIDGE_RASTER_M (links nach rechts 2m-Module zuerst, 1m-Rest
    # ganz rechts falls B ungerade).
    span = max(width_m - 1, 0)
    raster = OUTDOOR_RASTER_M if row_type == "1m" else BRIDGE_RASTER_M
    return _raster_positions(span, raster)


def _build_grid(width_m, height_m, level_y_positions, corner_positions_by_level, clamp_positions_by_level):
    # Node-Grid fuer die Visualisierung: Zeilen = Meter-Positionen entlang H
    # (0..H), Spalten = die B vertikalen Strings. Jede Spalte traegt
    # durchgehend einen vertikalen String. corner_positions_by_level und
    # clamp_positions_by_level sind beide parallel zu level_y_positions -
    # JEDE Ebene hat ihre eigenen Corner- UND Clamp-Spalten (Ruecksprache,
    # strikte Trennung): 'Corner' NUR an echten Modul-End-Schnittpunkten
    # (Vertikal- UND Horizontal-Modul enden dort gemeinsam), 'Clamp' an
    # allen anderen belegten Punkten (Mitte eines 2m-Moduls, vertikal ODER
    # horizontal - siehe calculate_liam_truss_mechanics). 'Truss' bleibt nur
    # dort, wo gar keine Ebene liegt (z.B. der oberste Rand direkt unter der
    # Hanging-Bar).
    corner_x_by_y = {
        y: set(cols) for y, cols in zip(level_y_positions, corner_positions_by_level)
    }
    clamp_x_by_y = {
        y: set(cols) for y, cols in zip(level_y_positions, clamp_positions_by_level)
    }
    grid = []
    for y in range(height_m + 1):
        row = []
        for x in range(width_m):
            if x in corner_x_by_y.get(y, ()):
                row.append("Corner")
            elif x in clamp_x_by_y.get(y, ()):
                row.append("Clamp")
            else:
                row.append("Truss")
        grid.append(row)
    return grid


def calculate_liam_truss_mechanics(width_m, height_m, location, curving_mode=None):
    """
    Berechnet Stueckliste und Visualisierungs-Grid fuer den LIAM-Hanging-
    Modus. width_m/height_m sind Breite/Hoehe in Metern (1 LIAM-Cabinet =
    1m, daher identisch zu width_cabinets/height_cabinets). location ist
    'indoor' oder 'outdoor' - siehe Modul-Docstring fuer die genauen
    Unterschiede bei Conn/Bolzen/Clamp/Nut.

    curving_mode ('concave'/'convex'/None) ist eine eigene, rein additive
    Erweiterung (Ruecksprache: "LIAM curvt separat") - sie aendert NICHTS an
    den obigen Corner/Clamp/Bolzen/Nut/Conn-Formeln (die bleiben exakt wie
    dokumentiert final/unveraenderlich), sondern ergaenzt lediglich ein
    zusaetzliches Bauteil: zwischen den Cabinets wird bei Biegung ein fester
    Winkel-Bracket eingeschraubt - 1x pro gebogener vertikaler Fuge (also
    (width_m - 1) Fugen) UND pro Cabinet-Reihe (height_m).
    """
    is_outdoor = location == "outdoor"
    raster_m = OUTDOOR_RASTER_M if is_outdoor else INDOOR_RASTER_M

    # Horizontale Ebenen: vom oberen Rand aus im aktiven Raster nach unten,
    # inkl. garantierter Boden-Ebene bei 0m (siehe _raster_positions_from_top).
    # Index 0 = Ebene 1 (oberste Ebene), letzter Index = Boden-Ebene.
    level_y_positions = _raster_positions_from_top(height_m, raster_m)
    levels = len(level_y_positions)

    v_truss2, v_truss1, _ = _line_modules(height_m)

    if is_outdoor:
        # Outdoor (final, Ruecksprache - strikte Corner/Clamp-Trennung):
        # alternierendes 1m-/2m-Zeilenschema pro Ebene - siehe
        # _outdoor_row_types/_bridge_positions_for_row und den Modul-
        # Docstring oben. WICHTIG: eine '2m'-Ebene liegt (dank der exakt
        # gegenlaeufigen Konstruktion von _outdoor_row_types und der
        # vertikalen 2m-Modul-Grenzen - beide starten am oberen Rand und
        # zaehlen in 2m-Schritten abwaerts, mit identischer Kappung auf 0
        # ganz unten) IMMER exakt auf einer echten vertikalen Modul-Grenze;
        # eine '1m'-Ebene liegt IMMER exakt in der Mitte eines vertikalen
        # 2m-Moduls. Deshalb gilt: NUR auf '2m'-Ebenen sind beruehrte
        # Spalten echte Corner (Vertikal- UND Horizontal-Modul enden dort
        # gemeinsam - "physische Endpunkte, da wo die Bolzenverbindungen
        # sitzen"); auf '1m'-Ebenen ist JEDE Beruehrung zwangslaeufig mittig
        # auf einem vertikalen 2m-Modul und wird daher NIE zum Corner,
        # sondern zur Clamp (Alternative-Regel).
        row_types = _outdoor_row_types(levels)
        bridge_positions_by_level = [
            _bridge_positions_for_row(width_m, row_type) for row_type in row_types
        ]

        horizontal_truss2m_total = 0
        horizontal_truss1m_total = 0
        corner_nodes = 0
        corner_positions_by_level = []
        clamp_positions_by_level = []
        touched_columns = set()
        for bridges, row_type in zip(bridge_positions_by_level, row_types):
            touched_columns.update(bridges)
            segment_lengths = [
                bridges[i + 1] - bridges[i] for i in range(len(bridges) - 1)
            ]
            horizontal_truss2m_total += segment_lengths.count(2)
            horizontal_truss1m_total += segment_lengths.count(1)

            if row_type == "2m":
                # Beruehrte Spalten = echte Modul-End-Schnittpunkte -> Corner.
                # Unberuehrte (von einer 2m-Bruecke uebersprungene) Spalten
                # sitzen exakt in der Mitte eines horizontalen 2m-Moduls ->
                # Clamp (nie 'Truss', da bei 2m-Raster jede Luecke genau
                # eine Modul-Mitte ist).
                corner_nodes += len(bridges)
                corner_positions_by_level.append(bridges)
                bridge_set = set(bridges)
                clamp_positions_by_level.append(
                    [x for x in range(width_m) if x not in bridge_set]
                )
            else:
                # '1m'-Ebene: JEDE Beruehrung liegt mittig auf einem
                # vertikalen 2m-Modul -> ausnahmslos Clamp, kein Corner.
                corner_positions_by_level.append([])
                clamp_positions_by_level.append(bridges)

        # Vertikale Zerlegung: die Vereinigungsmenge aller ueber alle Ebenen
        # tatsaechlich beruehrten Spalten (touched_columns) bekommt ihre
        # eigene vertikale 2m/1m-Zerlegung - dank der ersten 1m-Reihe (Ebene
        # 1, beruehrt IMMER jede Spalte) sind das ausser im Sonderfall
        # levels=1 immer alle B Spalten.
        corner_columns = len(touched_columns)
        vertical_truss2m_total = corner_columns * v_truss2
        vertical_truss1m_total = corner_columns * v_truss1

        truss_2m_total = vertical_truss2m_total + horizontal_truss2m_total
        truss_1m_total = vertical_truss1m_total + horizontal_truss1m_total
    else:
        # Indoor: JEDE Ebene folgt demselben Bruecken-Muster
        # (BRIDGE_RASTER_M), unveraendert. Indoor-Ebenen liegen wegen
        # INDOOR_RASTER_M=BRIDGE_RASTER_M=2 immer exakt auf einer vertikalen
        # Modul-Grenze - die Corner/Clamp-Problematik von Outdoor tritt hier
        # gar nicht auf, jede Beruehrung bleibt ein echter Corner.
        bridge_x_positions = _raster_positions(max(width_m - 1, 0), BRIDGE_RASTER_M)
        bridge_positions_by_level = [bridge_x_positions] * levels
        corner_positions_by_level = bridge_positions_by_level
        clamp_positions_by_level = [[] for _ in range(levels)]
        corner_columns = len(bridge_x_positions)
        segment_lengths = [
            bridge_x_positions[i + 1] - bridge_x_positions[i]
            for i in range(len(bridge_x_positions) - 1)
        ]
        truss2m_per_level = segment_lengths.count(2)
        truss1m_per_level = segment_lengths.count(1)

        vertical_truss2m_total = corner_columns * v_truss2
        vertical_truss1m_total = corner_columns * v_truss1

        horizontal_truss2m_total = levels * truss2m_per_level
        horizontal_truss1m_total = levels * truss1m_per_level

        truss_2m_total = vertical_truss2m_total + horizontal_truss2m_total
        truss_1m_total = vertical_truss1m_total + horizontal_truss1m_total

        corner_nodes = levels * corner_columns

    components = {
        "liam_truss_2m": truss_2m_total,
        "liam_truss_1m": truss_1m_total,
        # Eigene Stueckliste-Position (nicht nur ein interner Zwischenwert
        # fuer die Bolzen-Formel) - dieselbe corner_nodes-Zahl, die auch das
        # Grid als 'Corner'-Zellen zeichnet (siehe _build_grid).
        "liam_truss_corner": corner_nodes,
        # Eine Hanging-Bar pro vertikalem String (oben), unabhaengig von
        # H/Raster/Outdoor-Faktor.
        "liam_hanging_bar": width_m,
    }

    if is_outdoor:
        # Clamp-Basis: exakt 1x in der exakten Mitte jedes Truss-System 2m
        # Moduls (vertikal UND horizontal) - das ist exakt truss_2m_total
        # (die Beruehrungen auf '1m'-Ebenen sind mathematisch identisch mit
        # vertical_truss2m_total und daher hier schon enthalten, nicht
        # nochmal zusaetzlich aufaddieren). NIE an 1m-Modulen.
        clamp_module_middles = truss_2m_total

        # Korrektur (Ruecksprache): "ueberall wo ein Corner ist, muss auch
        # eine Clamp sein" - Clamp und Corner sind NICHT exklusiv, jeder
        # Corner-Knoten bekommt zusaetzlich zur Bolzenverbindung eine eigene
        # Clamp zur Fixierung. Corner + Clamp ergibt damit zusammen immer
        # exakt levels * width_m (jede Spalte jeder Ebene bekommt eine
        # Clamp, an echten Modul-Enden zusaetzlich einen Corner).
        clamp = corner_nodes + clamp_module_middles

        # Conn = exakt B (1x je String-Oberkante/Hanging-Bar, keine
        # internen Modul-Verbinder mehr).
        conn_raw = width_m

        # Bolzen (Ruecksprache, final): JEDE Verbindung - Corner UND
        # (Modul-Mitten-)Clamp gleichermassen, zusammen exakt
        # levels*width_m Punkte - bekommt 2 Bolzen, Typ nach Knotentyp wie
        # bei Indoor: an einer INTERIOR Spalte (nicht die erste/letzte der
        # insgesamt beruehrten Spalten) UND auf einer NICHT-Boden-Ebene
        # sitzen 2x Bold-150 (echtes Kreuz, 4 Traversen treffen zusammen);
        # an allen uebrigen Verbindungen (Rand-Spalte ODER Boden-Ebene)
        # sitzen 2x Bold-100.
        total_connections = corner_nodes + clamp_module_middles
        interior_columns = max(corner_columns - 2, 0)
        non_ground_levels = levels - 1
        four_way_connections = interior_columns * non_ground_levels
        three_way_connections = total_connections - four_way_connections

        bold_150_raw = four_way_connections * 2
        bold_100_raw = three_way_connections * 2

        factor = OUTDOOR_SAFETY_FACTOR
        conn = math.ceil(conn_raw * factor)
        bold_150 = math.ceil(bold_150_raw * factor)
        bold_100 = math.ceil(bold_100_raw * factor)

        components["liam_truss_conn"] = conn
        components["liam_truss_bold_100"] = bold_100
        components["liam_truss_bold_150"] = bold_150
        components["liam_truss_clamp"] = clamp
        # Nuten = 4 je Corner + 2 je Conn + 1 je Bolzen (100 oder 150) -
        # dasselbe Grundmodell wie Indoor (s.u.), jetzt auch fuer Outdoor.
        components["liam_nut"] = corner_nodes * 4 + conn * 2 + (bold_100 + bold_150)
    else:
        # Indoor (Ruecksprache): LIAM-Truss-Clamp bleibt entfernt (keine
        # Berechnung/Stueckliste/Visualisierung mehr). LIAM-Truss-Conn ist
        # NEU als reiner Stueckliste-Wert wieder da - OHNE jede Visualisierung
        # (kein Grid-Marker, siehe drawLiamTrussGrid im Frontend): 1 Conn je
        # UNGERADER Hanging-Bar-Spalte (1-indexiert: 1, 3, 5, ...) UND
        # zusaetzlich IMMER an der letzten Spalte B, falls B gerade ist
        # (0-indexiert: x % 2 == 0 or x == B - 1). B=5 -> Spalten 1,3,5 (3
        # Stueck); B=6 -> Spalten 1,3,5,6 (4 Stueck).
        connector_columns = [
            x for x in range(width_m) if x % 2 == 0 or x == width_m - 1
        ]
        conn = len(connector_columns)

        # Bolzen nach Knotentyp: ein Corner an einer INTERIOR Corner-Spalte
        # (nicht die erste/letzte) UND auf einer NICHT-Boden-Ebene (die
        # Ebene bei y=0 hat keine Traverse mehr darunter) ist ein echtes
        # Kreuz (4 Traversen treffen zusammen) -> 2x Bold-150. Alle uebrigen
        # Corner (Rand-Spalte ODER Boden-Ebene, nur 3 Traversen treffen
        # zusammen) -> 2x Bold-100.
        interior_columns = max(corner_columns - 2, 0)
        non_ground_levels = levels - 1  # Boden-Ebene (y=0) ist immer genau 1 der Ebenen
        four_way_corners = interior_columns * non_ground_levels
        three_way_corners = corner_nodes - four_way_corners

        bold_150 = four_way_corners * 2
        bold_100 = three_way_corners * 2

        components["liam_truss_conn"] = conn
        components["liam_truss_bold_100"] = bold_100
        components["liam_truss_bold_150"] = bold_150
        # 4 Nuten je Corner + 2 je Conn + 1 je Bolzen (100 oder 150).
        components["liam_nut"] = corner_nodes * 4 + conn * 2 + (bold_100 + bold_150)

    if curving_mode in ("concave", "convex"):
        # Additiv, siehe Docstring - beruehrt keine der obigen Zahlen.
        components["liam_curving_bracket"] = max(width_m - 1, 0) * height_m

    return {
        "components": components,
        "grid": _build_grid(
            width_m, height_m, level_y_positions,
            corner_positions_by_level, clamp_positions_by_level,
        ),
        "validation_note": VALIDATION_NOTE,
    }
