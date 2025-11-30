import pandas as pd
import folium
import webbrowser
import os
from folium.plugins import Search

# === Dossier de travail relatif au script ===
base_dir = os.path.dirname(os.path.abspath(__file__))

# === CSV ===
csv_path = os.path.join(base_dir, "classeur11.csv")
data = pd.read_csv(csv_path, encoding='utf-8', sep=';')
data.columns = data.columns.str.strip()

for col in ['x','y','X','Y']:
    if col in data.columns:
        data[col] = data[col].astype(str).str.replace('\xa0','',regex=False).str.strip()

col_x = 'x' if 'x' in data.columns else 'X'
col_y = 'y' if 'y' in data.columns else 'Y'

print("Colonnes utilisées :", col_x, col_y)

# === Carte ===
m = folium.Map(location=[34.0, 9.0], zoom_start=7)

# === Ajouter logo (chemin relatif) ===
logo_path = os.path.join(base_dir, "image", "logo_atlas.jpg")  # image/logo_atlas.jpg
logo_url = 'file:///' + os.path.abspath(logo_path).replace('\\','/')
m.get_root().html.add_child(folium.Element(f"""
<div style="position: absolute; top: 5px; left: 5px; z-index:9999;">
    <img src="{logo_url}" width="80">
</div>
"""))

# === Liste pour GeoJSON ===
features = []
offsets = {}
delta = 0.01

for i, row in data.iterrows():
    try:
        lat = float(row[col_y].replace(',', '.'))
        lon = float(row[col_x].replace(',', '.'))

        key = (lat, lon)
        if key in offsets:
            count = offsets[key]
            lat += delta * (count % 3)
            lon += delta * (count // 3)
            offsets[key] += 1
        else:
            offsets[key] = 1

        popup_html = f"""
        <div style="direction: rtl; text-align: right; font-family: Arial;">
        <b>المدخل:</b> {row.get('المدخل','')}<br>
        <b>الكتابة الصّوتيّة:</b> {row.get('الكتابة الصّوتية','')}<br>
        <b>الموقع:</b> {row.get('الموقع/المواقع الجغرافي(ة)','')}<br>
        <b>الدلالة:</b> {row.get('الدلالة','')}<br>
        </div>
        """

        # === Image relative ===
        if pd.notna(row.get('صورة')) and str(row['صورة']).strip():
            img_rel = str(row['صورة']).strip()
            img_path = os.path.join(base_dir, img_rel)
            img_url = 'file:///' + os.path.abspath(img_path).replace('\\','/')
            popup_html += f"<img src='{img_url}' width='230'><br>"

        # === Audio relatif ===
        if pd.notna(row.get('تسجيل صوتي')) and str(row['تسجيل صوتي']).strip():
            audio_rel = str(row['تسجيل صوتي']).strip()
            audio_path = os.path.join(base_dir, audio_rel)
            audio_url = 'file:///' + os.path.abspath(audio_path).replace('\\','/')
            popup_html += f"<audio controls style='width:230px;'><source src='{audio_url}' type='audio/mpeg'></audio><br>"

        search_text = f"{row.get('المدخل','')} {row.get('الكتابة الصّوتية','')}"

        feature = {
            "type": "Feature",
            "properties": {
                "search_text": search_text,
                "popup": popup_html
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }
        features.append(feature)

    except Exception as e:
        print(f"⚠️ Erreur ligne {i}: {e}")

# === GeoJSON Layer ===
geojson = folium.GeoJson(
    {"type":"FeatureCollection", "features":features},
    popup=folium.GeoJsonPopup(fields=["popup"]),
    tooltip=folium.GeoJsonTooltip(fields=["search_text"])
).add_to(m)

# === Barre de recherche unique ===
Search(
    layer=geojson,
    search_label='search_text',
    placeholder="🔍 Rechercher un المدخل ou الكتابة الصّوتية...",
    collapsed=False
).add_to(m)

# === Surlignage rouge du marker trouvé ===
m.get_root().html.add_child(folium.Element("""
<script>
var lastMarker = null;
map.on('search:locationfound', function(e) {
    if (lastMarker) { lastMarker.setStyle({color:'blue'}); }
    e.layer.setStyle({color:'red'});
    lastMarker = e.layer;
});
</script>
"""))

# === Sauvegarde et ouverture ===
output_html = os.path.join(base_dir, "carte_interactive.html")
m.save(output_html)
webbrowser.open('file://'+os.path.realpath(output_html))

print("👉 Carte prête avec recherche et logo :", output_html)
