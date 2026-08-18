import os

template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "index.html")
print("Template-Pfad:", template_path)

if os.path.exists(template_path):
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"Dateigröße: {len(content)} Zeichen")
    print("\nErste 350 Zeichen:")
    print(content[:350])
    
    if "CACHE BUSTER" in content:
        print("\n✓ CACHE BUSTER in der Datei gefunden!")
    else:
        print("\n✗ CACHE BUSTER NICHT in der Datei!")
else:
    print(f"ERROR: Datei nicht gefunden: {template_path}")
