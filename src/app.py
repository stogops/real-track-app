print('REAL TRACK VERSION 2.0')
from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# 1. PERSISTENCE: Absolute path to the /data mount point
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/real_track.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class AssetClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    locations = db.relationship('Location', backref='asset_class', lazy=True, cascade="all, delete-orphan")

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    square_footage = db.Column(db.Float, default=0)
    asset_class_id = db.Column(db.Integer, db.ForeignKey('asset_class.id'), nullable=False)

# Create database and tables
with app.app_context():
    # Ensure directory exists for sqlite (though usually /data is a mount point)
    os.makedirs('/data', exist_ok=True)
    db.create_all()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Track | Portfolio Map</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        #map { height: 500px; width: 100%; z-index: 1; border-radius: 0.5rem; }
    </style>
</head>
<body class="bg-slate-50 min-h-screen p-4 md:p-8">
    <div class="max-w-6xl mx-auto">
        <header class="mb-8 flex justify-between items-center">
            <h1 class="text-3xl font-extrabold text-slate-800">Real<span class="text-emerald-600">Track</span></h1>
            <div class="text-sm text-slate-500 font-medium">Location Asset Management</div>
        </header>
        
        <!-- Map Control Panel -->
        <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-8">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                <h2 class="text-lg font-bold text-slate-700">Portfolio Visualization</h2>
                <div class="flex flex-wrap items-center gap-4">
                    <div class="flex items-center gap-2">
                        <label class="text-xs font-bold uppercase tracking-wider text-slate-400">View Mode:</label>
                        <select id="mapMode" onchange="updateMapMarkers()" class="border-slate-200 rounded-lg p-2 text-sm bg-slate-50 focus:ring-2 focus:ring-emerald-500 outline-none">
                            <option value="pins">📍 Standard Pins</option>
                            <option value="sqft">⭕ Square Footage (Relative)</option>
                        </select>
                    </div>
                    <div class="flex items-center gap-2">
                        <label class="text-xs font-bold uppercase tracking-wider text-slate-400">Asset Class:</label>
                        <select id="mapFilter" onchange="updateMapMarkers()" class="border-slate-200 rounded-lg p-2 text-sm bg-slate-50 focus:ring-2 focus:ring-emerald-500 outline-none">
                            <option value="all">All Assets</option>
                        </select>
                    </div>
                </div>
            </div>
            <div id="map"></div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Asset Class Management -->
            <div class="lg:col-span-1">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h2 class="text-lg font-bold text-slate-700 mb-4">Asset Classes</h2>
                    <div id="assetClassList" class="space-y-2 mb-6"></div>
                    <div class="flex gap-2">
                        <input type="text" id="newAssetClass" placeholder="e.g. Industrial" class="flex-1 border-slate-200 rounded-lg p-2 text-sm bg-slate-50">
                        <button onclick="addAssetClass()" class="bg-slate-800 text-white px-4 py-2 rounded-lg hover:bg-slate-700 text-sm font-bold transition">Add</button>
                    </div>
                </div>
            </div>

            <!-- Location Management -->
            <div class="lg:col-span-2">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h2 class="text-lg font-bold text-slate-700 mb-4">Add New Location</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div class="space-y-1">
                            <label class="text-xs font-bold text-slate-500 uppercase">Property Name</label>
                            <input type="text" id="locName" placeholder="Tech Plaza" class="w-full border-slate-200 rounded-lg p-2 text-sm bg-slate-50">
                        </div>
                        <div class="space-y-1">
                            <label class="text-xs font-bold text-slate-500 uppercase">Address</label>
                            <input type="text" id="locAddress" placeholder="123 Main St" class="w-full border-slate-200 rounded-lg p-2 text-sm bg-slate-50">
                        </div>
                        <div class="space-y-1">
                            <label class="text-xs font-bold text-slate-500 uppercase">Square Footage</label>
                            <input type="number" id="locSqFt" placeholder="50000" class="w-full border-slate-200 rounded-lg p-2 text-sm bg-slate-50">
                        </div>
                        <div class="space-y-1">
                            <label class="text-xs font-bold text-slate-500 uppercase">Asset Class</label>
                            <select id="locAssetClass" class="w-full border-slate-200 rounded-lg p-2 text-sm bg-slate-50"></select>
                        </div>
                        <div class="space-y-1">
                            <label class="text-xs font-bold text-slate-500 uppercase">Latitude</label>
                            <input type="number" step="any" id="locLat" placeholder="34.05" class="w-full border-slate-200 rounded-lg p-2 text-sm bg-slate-50">
                        </div>
                        <div class="space-y-1">
                            <label class="text-xs font-bold text-slate-500 uppercase">Longitude</label>
                            <input type="number" step="any" id="locLng" placeholder="-118.24" class="w-full border-slate-200 rounded-lg p-2 text-sm bg-slate-50">
                        </div>
                    </div>
                    <button onclick="addLocation()" class="w-full bg-emerald-600 text-white px-6 py-3 rounded-lg hover:bg-emerald-700 font-bold transition shadow-lg shadow-emerald-100 mb-8">Save Location</button>

                    <h2 class="text-lg font-bold text-slate-700 mb-4">Location Registry</h2>
                    <div id="locationList" class="space-y-3"></div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        let map;
        let markers = [];
        let allLocations = [];
        let allAssetClasses = [];

        function initMap() {
            map = L.map('map').setView([37.09, -95.71], 4);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap'
            }).addTo(map);
        }

        async function fetchAll() {
            const [classesRes, locsRes] = await Promise.all([
                fetch('/api/asset-classes'),
                fetch('/api/locations')
            ]);
            allAssetClasses = await classesRes.json();
            allLocations = await locsRes.json();
            
            renderClasses();
            renderLocations();
            updateAssetClassDropdowns();
            updateMapMarkers();
        }

        function renderClasses() {
            const list = document.getElementById('assetClassList');
            list.innerHTML = allAssetClasses.map(c => `
                <div class="flex justify-between items-center bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <span class="text-sm font-bold text-slate-700">${c.name}</span>
                    <button onclick="deleteAssetClass(${c.id})" class="text-red-400 hover:text-red-600 transition">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </div>
            `).join('') || '<p class="text-slate-400 text-sm italic">No asset classes defined.</p>';
        }

        function renderLocations() {
            const list = document.getElementById('locationList');
            const classMap = Object.fromEntries(allAssetClasses.map(c => [c.id, c.name]));
            
            list.innerHTML = allLocations.map(l => `
                <div class="group border border-slate-100 bg-white p-4 rounded-xl shadow-sm hover:shadow-md transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <h3 class="font-bold text-slate-800">${l.name}</h3>
                            <span class="text-[10px] uppercase font-black px-2 py-0.5 rounded bg-emerald-50 text-emerald-600 border border-emerald-100">${classMap[l.asset_class_id] || 'N/A'}</span>
                        </div>
                        <p class="text-xs text-slate-500 mb-2">${l.address || 'No address provided'}</p>
                        <div class="flex flex-wrap gap-3">
                            <span class="text-sm font-semibold text-slate-700">${l.square_footage.toLocaleString()} <span class="text-slate-400 font-normal">sq ft</span></span>
                            ${l.latitude ? `<span class="text-[11px] text-slate-400">📍 ${l.latitude.toFixed(4)}, ${l.longitude.toFixed(4)}</span>` : ''}
                        </div>
                    </div>
                    <button onclick="deleteLocation(${l.id})" class="text-slate-300 hover:text-red-500 transition px-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
            `).join('') || '<p class="text-slate-400 italic text-center py-8">No locations added yet.</p>';
        }

        function updateAssetClassDropdowns() {
            const formSelect = document.getElementById('locAssetClass');
            const mapFilter = document.getElementById('mapFilter');
            const options = allAssetClasses.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            formSelect.innerHTML = options;
            mapFilter.innerHTML = '<option value="all">All Assets</option>' + options;
        }

        function updateMapMarkers() {
            markers.forEach(m => map.removeLayer(m));
            markers = [];

            const filterId = document.getElementById('mapFilter').value;
            const mode = document.getElementById('mapMode').value;

            const filteredLocs = filterId === 'all' 
                ? allLocations 
                : allLocations.filter(l => l.asset_class_id == filterId);

            // Group by asset class to find max square footage per class
            const classMaxSqFt = {};
            allLocations.forEach(loc => {
                if (!classMaxSqFt[loc.asset_class_id] || loc.square_footage > classMaxSqFt[loc.asset_class_id]) {
                    classMaxSqFt[loc.asset_class_id] = loc.square_footage;
                }
            });

            const bounds = [];
            filteredLocs.forEach(l => {
                if (l.latitude && l.longitude) {
                    let layer;
                    const popupContent = `
                        <div class="p-2">
                            <div class="text-[10px] font-black uppercase text-emerald-600 mb-1">${allAssetClasses.find(c => c.id == l.asset_class_id)?.name || 'Asset'}</div>
                            <div class="font-bold text-slate-800 text-sm">${l.name}</div>
                            <div class="text-xs text-slate-500 mb-2">${l.address || ''}</div>
                            <div class="text-xs font-bold text-slate-700 border-t pt-2">${l.square_footage.toLocaleString()} sq ft</div>
                        </div>
                    `;

                    if (mode === 'pins') {
                        layer = L.marker([l.latitude, l.longitude]).bindPopup(popupContent);
                    } else {
                        // RADIUS LOGIC: Relative to max in its own asset class
                        const classMax = classMaxSqFt[l.asset_class_id] || 1;
                        const minRadius = 8;
                        const maxRadius = 45;
                        // Calculate radius ratio (min 0, max 1) then scale to pixel range
                        const ratio = l.square_footage / classMax;
                        const radius = minRadius + (ratio * (maxRadius - minRadius));

                        layer = L.circleMarker([l.latitude, l.longitude], {
                            radius: radius,
                            fillColor: "#10b981",
                            color: "#059669",
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.5
                        }).bindPopup(popupContent);
                    }

                    layer.addTo(map);
                    markers.push(layer);
                    bounds.push([l.latitude, l.longitude]);
                }
            });

            if (bounds.length > 0) {
                map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
            }
        }

        async function addAssetClass() {
            const name = document.getElementById('newAssetClass').value;
            if (!name) return;
            await fetch('/api/asset-classes', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name})
            });
            document.getElementById('newAssetClass').value = '';
            fetchAll();
        }

        async function deleteAssetClass(id) {
            if (!confirm('This will delete all locations in this class. Proceed?')) return;
            await fetch(`/api/asset-classes/${id}`, {method: 'DELETE'});
            fetchAll();
        }

        async function addLocation() {
            const data = {
                name: document.getElementById('locName').value,
                address: document.getElementById('locAddress').value,
                latitude: parseFloat(document.getElementById('locLat').value) || null,
                longitude: parseFloat(document.getElementById('locLng').value) || null,
                square_footage: parseFloat(document.getElementById('locSqFt').value) || 0,
                asset_class_id: parseInt(document.getElementById('locAssetClass').value)
            };
            
            if (!data.name || !data.asset_class_id) {
                alert("Name and Asset Class are required.");
                return;
            }
            
            await fetch('/api/locations', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            ['locName', 'locAddress', 'locLat', 'locLng', 'locSqFt'].forEach(id => document.getElementById(id).value = '');
            fetchAll();
        }

        async function deleteLocation(id) {
            if (!confirm('Delete this location?')) return;
            await fetch(`/api/locations/${id}`, {method: 'DELETE'});
            fetchAll();
        }

        initMap();
        fetchAll();
    </script>
</body>
</html>
'''

# --- API ROUTES ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/asset-classes', methods=['GET', 'POST'])
def handle_asset_classes():
    if request.method == 'POST':
        data = request.json
        new_class = AssetClass(name=data['name'])
        db.session.add(new_class)
        db.session.commit()
        return jsonify({'id': new_class.id, 'name': new_class.name}), 201
    
    classes = AssetClass.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in classes])

@app.route('/api/asset-classes/<int:id>', methods=['DELETE'])
def delete_asset_class(id):
    ac = AssetClass.query.get_or_404(id)
    db.session.delete(ac)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/locations', methods=['GET', 'POST'])
def handle_locations():
    if request.method == 'POST':
        data = request.json
        new_loc = Location(
            name=data['name'], 
            address=data.get('address'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            square_footage=data.get('square_footage', 0),
            asset_class_id=data['asset_class_id']
        )
        db.session.add(new_loc)
        db.session.commit()
        return jsonify({
            'id': new_loc.id, 'name': new_loc.name, 'address': new_loc.address,
            'latitude': new_loc.latitude, 'longitude': new_loc.longitude,
            'square_footage': new_loc.square_footage, 'asset_class_id': new_loc.asset_class_id
        }), 201
    else:
        locs = Location.query.all()
        return jsonify([{
            'id': l.id, 'name': l.name, 'address': l.address,
            'latitude': l.latitude, 'longitude': l.longitude,
            'square_footage': l.square_footage, 'asset_class_id': l.asset_class_id
        } for l in locs])

@app.route('/api/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    loc = Location.query.get_or_404(id)
    db.session.delete(loc)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)