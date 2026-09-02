from server import app

c = app.test_client()

# Muss mit SYSTEM_LABELS in templates/index.html uebereinstimmen - die
# Label-Zuordnung lebt bewusst im Frontend, das Backend filtert generisch
# ueber Systemnamen (mounting_systems).
SYSTEM_LABELS = {
    "Standard-Stacking": "Stacking",
    "NoBase": "No-Base",
    "AR-Stacking": "Stacking",
    "AR-Outdoor-Stacking": "Stacking",
    "Flex-Stacking": "Stacking",
    "Vanish-Stacking": "Stacking",
    "Hanging-Truss": "Hanging",
    "Flex-Hanging": "Hanging",
    "Vanish-Hanging": "Hanging",
    "AR-Hanging": "Hanging",
    "LIAM-Truss": "Hanging",
    "Wandadapter": "Wandadapter",
}


def get(url):
    r = c.get(url)
    assert r.status_code == 200, (url, r.status_code, r.data[:200])
    return r.get_json()


def names(rows):
    return [p["product_name"] for p in rows]


def labels_of(systems):
    out = []
    for s in systems:
        label = SYSTEM_LABELS.get(s, s)
        if label not in out:
            out.append(label)
    return out


def systems_for(label, systems):
    return [s for s in systems if SYSTEM_LABELS.get(s, s) == label]


# --- Filteroptionen -------------------------------------------------------
# Alle Parameter sind optional (freie Eingabereihenfolge), auch ganz ohne.
for url in ["/api/product-filters", "/api/product-filters?location=outdoor",
            "/api/product-filters?usage=temporaer",
            "/api/product-filters?location=indoor&usage=fest",
            "/api/product-filters?location=outdoor&usage=temporaer"]:
    data = get(url)
    print(f"{url:52s} -> {labels_of(data['mounting_systems'])} "
          f"{data['pixelpitch_min']}..{data['pixelpitch_max']}")

base = get("/api/product-filters")
# No-Base muss von Anfang an als eigene Montageart auftauchen (nicht in
# "Stacking" verschluckt werden).
assert "No-Base" in labels_of(base["mounting_systems"]), base["mounting_systems"]
assert labels_of(base["mounting_systems"]) == ["Stacking", "No-Base", "Hanging", "Wandadapter"]
# Outdoor kann weder Wandadapter noch (bei diesen Produkten) No-Base.
outdoor = labels_of(get("/api/product-filters?location=outdoor&usage=fest")["mounting_systems"])
print("outdoor labels                                       ->", outdoor)
assert "Wandadapter" not in outdoor

# --- Produktliste: jede Teilmenge von Parametern muss funktionieren -------
allp = get("/api/product-series")
print("series ohne filter      ", len(allp))
nobase = ",".join(systems_for("No-Base", base["mounting_systems"]))
stacking = ",".join(systems_for("Stacking", base["mounting_systems"]))
for url in [
    f"/api/product-series?mounting_systems={nobase}",
    f"/api/product-series?mounting_systems={stacking}",
    "/api/product-series?pixelpitch_max=1.5",
    "/api/product-series?location=outdoor",
    "/api/product-series?usage=temporaer",
    f"/api/product-series?mounting_systems={nobase}&pixelpitch_min=2&pixelpitch_max=4",
]:
    got = get(url)
    print(f"  {len(got):3d} {names(got)[:5]}  <- {url}")
    assert len(got) <= len(allp)

# No-Base ist eine echte Teilmenge von Stacking -> der Filter muss beissen.
n_nobase = len(get(f"/api/product-series?mounting_systems={nobase}"))
n_stacking = len(get(f"/api/product-series?mounting_systems={stacking}"))
print("No-Base / Stacking      ", n_nobase, "/", n_stacking)
assert 0 < n_nobase < n_stacking

# Outdoor Wandadapter ist gesperrt -> leere Liste, konsistent zu den
# Filteroptionen oben.
assert get("/api/product-series?location=outdoor&mounting_systems=Wandadapter") == []

# Flache Liste (temporaerer Einsatz) verhaelt sich identisch.
print("products temp           ", len(get("/api/products?usage=temporaer")))
for label in labels_of(base["mounting_systems"]):
    sel = ",".join(systems_for(label, base["mounting_systems"]))
    got = get(f"/api/products?usage=temporaer&mounting_systems={sel}")
    print(f"  {label:12s}", len(got), names(got)[:4])

pp = get("/api/products?usage=temporaer&pixelpitch_min=2.5&pixelpitch_max=3")
print("products pp 2.5..3      ", [(p["product_name"], p["pixelpitch_mm"]) for p in pp])
assert all(2.5 <= p["pixelpitch_mm"] <= 3 for p in pp)

# --- Filter und Montageart-Dropdown muessen deckungsgleich sein ----------
for location in ("indoor", "outdoor"):
    avail = get(f"/api/product-filters?location={location}")["mounting_systems"]
    for label in labels_of(avail):
        sel = ",".join(systems_for(label, avail))
        filtered = {p["product_id"] for p in get(
            f"/api/product-series?location={location}&mounting_systems={sel}")}
        for product_id in {p["product_id"] for p in get(f"/api/product-series?location={location}")}:
            modes = get(f"/api/mechanics-options?product_id={product_id}&location={location}")["modes"]
            product_labels = labels_of([s for m in modes for s in m["systems"]])
            assert (product_id in filtered) == (label in product_labels), (label, location, product_id)
print("Filter == Montageart-Dropdown fuer alle Produkte/Montagearten/Orte: OK")

# --- Modell-Dropdown innerhalb einer Serie -------------------------------
series_id = allp[0]["product_id"]
models_all = get(f"/api/product-models?product_id={series_id}")
models_pp = get(f"/api/product-models?product_id={series_id}&pixelpitch_max=2")
print("models all/<=2mm        ", [m["pixelpitch_mm"] for m in models_all],
      [m["pixelpitch_mm"] for m in models_pp])
assert all(m["pixelpitch_mm"] <= 2 for m in models_pp)
print("OK")
