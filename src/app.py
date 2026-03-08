from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
# Using a local path for the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///real_track.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    square_footage = db.Column(db.Float, nullable=True)
    asset_class_id = db.Column(db.Integer, db.ForeignKey('asset_class.id'), nullable=False)

with app.app_context():
    db.create_all()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Track | Map View</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        #map { height: 500px; width: 100%; z-index: 1; }
    </style>
</head>
<body class="bg-gray-100 p-6">
    <div class="max-w-6xl mx-auto">
        <h1 class="text-3xl font-bold mb-6 text-emerald-600">Real Track</h1>
        
        <!-- Map Section -->
        <div class="bg-white p-6 rounded-lg shadow-md mb-8">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                <h2 class="text-xl font-semibold">Location Map</h2>
                <div class="flex flex-wrap items-center gap-4">
                    <div class="flex items-center gap-2">
                        <label class="text-sm font-medium text-gray-600">Display:</label>
                        <select id="mapMode" onchange="updateMapMarkers()" class="border rounded p-2 text-sm bg-white">
                            <option value="pins">Standard Pins</option>
                            <option value="sqft">Square Footage (Circles)</option>
                        </select>
                    </div>
                    <div class="flex items-center gap-2">
                        <label class="text-sm font-medium text-gray-600">Filter Asset:</label>
                        <select id="mapFilter" onchange="updateMapMarkers()" class="border rounded p-2 text-sm bg-white">
                            <option value="all">All Assets</option>
                        </select>
                    </div>
                </div>
            </div>
            <div id="map" class="rounded-lg border"></div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <!-- Asset Classes Section -->
            <div class="md:col-span-1">
                <div class="bg-white p-6 rounded-lg shadow-md mb-6">
                    <h2 class="text-xl font-semibold mb-4">Asset Classes</h2>
                    <div id="assetClassList" class="space-y-2 mb-4"></div>
                    <div class="flex gap-2">
                        <input type="text" id="newAssetClass" placeholder="New Class..." class="flex-1 border rounded p-2 text-sm">
                        <button onclick="addAssetClass()" class="bg-emerald-500 text-white px-3 py-1 rounded hover:bg-emerald-600 text-sm">Add</button>
                    </div>
                </div>
            </div>

            <!-- Locations Section -->
            <div class="md:col-span-2">
                <div class="bg-white p-6 rounded-lg shadow-md mb-6">
                    <h2 class="text-xl font-semibold mb-4">Locations</h2>
                    
                    <div class="bg-gray-50 p-4 rounded mb-6 border border-gray-200">
                        <p class="text-sm font-bold text-gray-700 mb-3">Add New Location</p>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                            <input type="text" id="locName" placeholder="Location Name" class="border rounded p-2 text-sm">
                            <input type="text" id="locAddress" placeholder="Address" class="border rounded p-2 text-sm">
                            <input type="number" step="any" id="locLat" placeholder="Latitude" class="border rounded p-2 text-sm">
                            <input type="number" step="any" id="locLng" placeholder="Longitude" class="border rounded p-2 text-sm">
                            <input type="number" step="any" id="locSqFt" placeholder="Square Footage" class="border rounded p-2 text-sm">
                            <select id="locAssetClass" class="border rounded p-2 text-sm bg-white"></select>
                        </div>
                        <button onclick="addLocation()" class="w-full bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 text-sm font-bold transition">Add Location</button>
                    </div>

                    <div id="locationList" class="space-y-4"></div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        let map;
        let markers = [];
        let allLocations = [];

        function initMap() {
            map = L.map('map').setView([20, 0], 2);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
        }

        async function fetchAll() {
            const [classesRes, locsRes] = await Promise.all([
                fetch('/api/asset-classes'),
                fetch('/api/locations')
            ]);
            const classes = await classesRes.json();
            allLocations = await locsRes.json();
            
            renderClasses(classes);
            renderLocations(allLocations, classes);
            updateAssetClassDropdowns(classes);
            updateMapMarkers();
        }

        function renderClasses(classes) {
            const list = document.getElementById('assetClassList');
            list.innerHTML = classes.map(c => `
                <div class="flex justify-between items-center bg-gray-50 p-2 rounded border border-gray-100">
                    <span class="text-sm font-medium">${c.name}</span>
                    <button onclick="deleteAssetClass(${c.id})" class="text-red-500 hover:text-red-700 text-xs">Delete</button>
                </div>
            `).join('') || '<p class="text-gray-400 text-sm italic">No classes</p>';
        }

        function renderLocations(locs, classes) {
            const list = document.getElementById('locationList');
            const classMap = Object.fromEntries(classes.map(c => [c.id, c.name]));
            
            list.innerHTML = locs.map(l => `
                <div class="border-l-4 border-emerald-500 bg-white p-4 rounded shadow-sm flex justify-between items-center">
                    <div>
                        <h3 class="font-bold text-gray-800">${l.name}</h3>
                        <p class="text-sm text-gray-500">${l.address || 'No address'}</p>
                        <div class="flex flex-wrap gap-2 mt-2">
                            <span class="bg-emerald-100 text-emerald-800 text-xs px-2 py-1 rounded">${classMap[l.asset_class_id] || 'Unknown'}</span>
                            <span class="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">SF: ${l.square_footage?.toLocaleString() || '0'}</span>
                            ${l.latitude ? `<span class="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded">Lat: ${l.latitude}</span>` : ''}
                            ${l.longitude ? `<span class="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded">Lng: ${l.longitude}</span>` : ''}
                        </div>
                    </div>
                    <button onclick="deleteLocation(${l.id})" class="bg-red-50 text-red-600 px-3 py-1 rounded hover:bg-red-100 text-sm transition">Delete</button>
                </div>
            `).join('') || '<p class="text-gray-400 italic">No locations found</p>';
        }

        function updateAssetClassDropdowns(classes) {
            const formSelect = document.getElementById('locAssetClass');
            const mapFilter = document.getElementById('mapFilter');
            const options = classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
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

            const bounds = [];
            
            // Scaling logic for Square Footage mode
            const maxSqFt = Math.max(...filteredLocs.map(l => l.square_footage || 0), 1);

            filteredLocs.forEach(l => {
                if (l.latitude && l.longitude) {
                    let layer;
                    const popupContent = `
                        <div class="text-sm">
                            <b class="text-emerald-700">${l.name}</b><br>
                            ${l.address || ''}<br>
                            <span class="font-bold">Area:</span> ${l.square_footage?.toLocaleString() || 0} sq ft
                        </div>
                    `;

                    if (mode === 'pins') {
                        layer = L.marker([l.latitude, l.longitude]).bindPopup(popupContent);
                    } else {
                        // Calculate radius: Min 5px, Max 40px relative to largest property in view
                        const minRadius = 5;
                        const maxRadius = 40;
                        const radius = minRadius + ((l.square_footage || 0) / maxSqFt) * (maxRadius - minRadius);

                        layer = L.circleMarker([l.latitude, l.longitude], {
                            radius: radius,
                            fillColor: "#10b981",
                            color: "#059669",
                            weight: 1,
                            opacity: 1,
                            fillOpacity: 0.6
                        }).bindPopup(popupContent);
                    }

                    layer.addTo(map);
                    markers.push(layer);
                    bounds.push([l.latitude, l.longitude]);
                }
            });

            if (bounds.length > 0) {
                map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
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
            if (!confirm('Deleting this asset class will delete ALL associated locations. Continue?')) return;
            await fetch(`/api/asset-classes/${id}`, {method: 'DELETE'});
            fetchAll();
        }

        async function addLocation() {
            const name = document.getElementById('locName').value;
            const address = document.getElementById('locAddress').value;
            const lat = document.getElementById('locLat').value;
            const lng = document.getElementById('locLng').value;
            const sqft = document.getElementById('locSqFt').value;
            const asset_class_id = document.getElementById('locAssetClass').value;
            
            if (!name || !asset_class_id) {
                alert("Please provide at least a name and asset class.");
                return;
            }
            
            await fetch('/api/locations', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name, 
                    address, 
                    latitude: lat ? parseFloat(lat) : null,
                    longitude: lng ? parseFloat(lng) : null,
                    square_footage: sqft ? parseFloat(sqft) : 0,
                    asset_class_id: parseInt(asset_class_id)
                })
            });
            
            // Reset fields
            ['locName', 'locAddress', 'locLat', 'locLng', 'locSqFt'].forEach(id => {
                document.getElementById(id).value = '';
            });
            fetchAll();
        }

        async function deleteLocation(id) {
            await fetch(`/api/locations/${id}`, {method: 'DELETE'});
            fetchAll();
        }

        initMap();
        fetchAll();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/asset-classes', methods=['GET'])
def get_asset_classes():
    classes = AssetClass.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in classes])

@app.route('/api/asset-classes', methods=['POST'])
def add_asset_class():
    data = request.json
    new_class = AssetClass(name=data['name'])
    db.session.add(new_class)
    db.session.commit()
    return jsonify({'id': new_class.id, 'name': new_class.name}), 201

@app.route('/api/asset-classes/<int:id>', methods=['DELETE'])
def delete_asset_class(id):
    ac = AssetClass.query.get_or_404(id)
    db.session.delete(ac)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/locations', methods=['GET'])
def get_locations():
    locs = Location.query.all()
    return jsonify([{
        'id': l.id, 
        'name': l.name, 
        'address': l.address, 
        'latitude': l.latitude,
        'longitude': l.longitude,
        'square_footage': l.square_footage,
        'asset_class_id': l.asset_class_id
    } for l in locs])

@app.route('/api/locations', methods=['POST'])
def add_location():
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
    return jsonify({'id': new_loc.id, 'name': new_loc.name}), 201

@app.route('/api/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    loc = Location.query.get_or_404(id)
    db.session.delete(loc)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)