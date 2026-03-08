HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Track - Asset Manager</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        #map { height: 400px; width: 100%; border-radius: 0.5rem; }
        .sidebar-item.active { background-color: #3b82f6; color: white; }
    </style>
</head>
<body class="bg-gray-50 text-gray-900">

    <div class="flex flex-col h-screen">
        <!-- Top Map Section -->
        <header class="bg-white border-b p-4">
            <div class="max-w-7xl mx-auto flex justify-between items-center mb-4">
                <h1 class="text-2xl font-bold text-blue-600">Real Track</h1>
                <div class="flex items-center space-x-2">
                    <label for="mapMode" class="text-sm font-medium">Visualization:</label>
                    <select id="mapMode" onchange="updateMarkers()" class="border rounded px-2 py-1 bg-white">
                        <option value="pins">Pins</option>
                        <option value="sqft">Square Footage</option>
                    </select>
                </div>
            </div>
            <div id="map" class="shadow-inner"></div>
        </header>

        <div class="flex flex-1 overflow-hidden">
            <!-- Sidebar -->
            <aside class="w-64 bg-white border-r overflow-y-auto p-4 space-y-8">
                <div>
                    <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Asset Classes</h2>
                    <ul id="assetClassList" class="space-y-1">
                        <!-- JS Rendered -->
                    </ul>
                </div>
                <div>
                    <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Counties (Filtered)</h2>
                    <ul id="countyList" class="space-y-1 text-sm text-gray-600">
                        <!-- JS Rendered -->
                    </ul>
                </div>
            </aside>

            <!-- Main Content Area -->
            <main class="flex-1 overflow-y-auto p-6">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    
                    <!-- Add Location Form -->
                    <section class="bg-white p-6 rounded-lg shadow-sm border">
                        <h2 class="text-lg font-semibold mb-4">Add New Location</h2>
                        <form id="locationForm" onsubmit="addLocation(event)" class="grid grid-cols-2 gap-4">
                            <div class="col-span-2">
                                <label class="block text-xs font-medium">Name</label>
                                <input type="text" id="form_name" required class="w-full border rounded p-2 mt-1">
                            </div>
                            <div class="col-span-2">
                                <label class="block text-xs font-medium">Address</label>
                                <input type="text" id="form_address" required class="w-full border rounded p-2 mt-1">
                            </div>
                            <div>
                                <label class="block text-xs font-medium">Latitude</label>
                                <input type="number" step="any" id="form_lat" required class="w-full border rounded p-2 mt-1">
                            </div>
                            <div>
                                <label class="block text-xs font-medium">Longitude</label>
                                <input type="number" step="any" id="form_lng" required class="w-full border rounded p-2 mt-1">
                            </div>
                            <div>
                                <label class="block text-xs font-medium">Square Footage</label>
                                <input type="number" id="form_sqft" required class="w-full border rounded p-2 mt-1">
                            </div>
                            <div>
                                <label class="block text-xs font-medium">Lot Size (Acres)</label>
                                <input type="number" step="any" id="form_lot" required class="w-full border rounded p-2 mt-1">
                            </div>
                            <div>
                                <label class="block text-xs font-medium">Annual Tax ($)</label>
                                <input type="number" id="form_tax" required class="w-full border rounded p-2 mt-1">
                            </div>
                            <div>
                                <label class="block text-xs font-medium">Asset Class</label>
                                <select id="form_asset_class" class="w-full border rounded p-2 mt-1"></select>
                            </div>
                            <div class="col-span-2">
                                <label class="block text-xs font-medium">County</label>
                                <select id="form_county" class="w-full border rounded p-2 mt-1"></select>
                            </div>
                            <button type="submit" class="col-span-2 bg-blue-600 text-white font-bold py-2 rounded hover:bg-blue-700 transition">Save Location</button>
                        </form>
                    </section>

                    <!-- Location List -->
                    <section>
                        <h2 class="text-lg font-semibold mb-4">Locations</h2>
                        <div id="locationList" class="space-y-3">
                            <!-- JS Rendered -->
                        </div>
                    </section>

                </div>
            </main>
        </div>
    </div>

    <script>
        let map, markersGroup;
        let currentAssetClassId = null;
        let data = {
            assetClasses: [],
            counties: [],
            locations: []
        };

        function initMap() {
            map = L.map('map').setView([37.0902, -95.7129], 4);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);
            markersGroup = L.layerGroup().addTo(map);
        }

        async function fetchAll() {
            try {
                const [acRes, cRes, lRes] = await Promise.all([
                    fetch('/api/asset-classes'),
                    fetch('/api/counties'),
                    fetch('/api/locations')
                ]);
                data.assetClasses = await acRes.json();
                data.counties = await cRes.json();
                data.locations = await lRes.json();

                if (currentAssetClassId === null && data.assetClasses.length > 0) {
                    currentAssetClassId = data.assetClasses[0].id;
                }
                
                renderUI();
                populateFormSelects();
            } catch (err) {
                console.error("Error fetching data:", err);
            }
        }

        function selectClass(id) {
            currentAssetClassId = id;
            renderUI();
        }

        function getVisibleLocations() {
            return data.locations.filter(l => {
                if (l.asset_class_id !== currentAssetClassId) return false;
                return Number.isFinite(l.latitude) && Number.isFinite(l.longitude);
            });
        }

        function renderUI() {
            // Render Sidebar Asset Classes
            const acList = document.getElementById('assetClassList');
            acList.innerHTML = data.assetClasses.map(ac => `
                <li>
                    <button onclick="selectClass(${ac.id})" class="sidebar-item w-full text-left px-3 py-2 rounded-md text-sm transition ${currentAssetClassId === ac.id ? 'active' : 'hover:bg-gray-100 text-gray-700'}">
                        ${ac.name}
                    </button>
                </li>
            `).join('');

            // Filter data
            const filteredCounties = data.counties.filter(c => c.asset_class_id === currentAssetClassId);
            const visibleLocations = getVisibleLocations();

            // Render Sidebar Counties
            const cList = document.getElementById('countyList');
            cList.innerHTML = filteredCounties.length 
                ? filteredCounties.map(c => `<li class="px-3 py-1">• ${c.county_name}, ${c.state}</li>`).join('')
                : '<li class="px-3 py-1 italic">No counties found</li>';

            // Render Location List
            const lList = document.getElementById('locationList');
            lList.innerHTML = visibleLocations.length
                ? visibleLocations.map(l => `
                <div class="bg-white p-4 border rounded shadow-sm">
                    <div class="font-bold">${l.name}</div>
                    <div class="text-xs text-gray-500">${l.address}</div>
                    <div class="mt-2 text-sm grid grid-cols-2 gap-1">
                        <span>SqFt: ${l.square_footage.toLocaleString()}</span>
                        <span>Lot: ${l.lot_size} ac</span>
                    </div>
                </div>
            `).join('')
                : '<div class="bg-white p-4 border rounded shadow-sm text-sm text-gray-500 italic">No mappable locations found for this asset class.</div>';

            updateMarkers();
        }

        function updateMarkers() {
            markersGroup.clearLayers();
            const mode = document.getElementById('mapMode').value;
            const visibleLocations = getVisibleLocations();

            if (visibleLocations.length === 0) return;

            const maxSqFt = Math.max(...visibleLocations.map(l => l.square_footage || 1));
            const bounds = L.latLngBounds();

            visibleLocations.forEach(l => {
                const pos = [l.latitude, l.longitude];
                bounds.extend(pos);

                if (mode === 'pins') {
                    L.marker(pos)
                        .bindPopup(`<b>${l.name}</b><br>${l.address}`)
                        .addTo(markersGroup);
                } else {
                    // Circle radius scaled to square footage relative to max in class
                    // We use sqrt for area-based scaling and a multiplier for visibility
                    const scaleFactor = 500; 
                    const radius = Math.sqrt(l.square_footage / maxSqFt) * scaleFactor;
                    
                    L.circle(pos, {
                        radius: radius,
                        color: '#3b82f6',
                        fillColor: '#3b82f6',
                        fillOpacity: 0.5
                    })
                    .bindPopup(`<b>${l.name}</b><br>SqFt: ${l.square_footage.toLocaleString()}`)
                    .addTo(markersGroup);
                }
            });

            if (bounds.isValid()) {
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        }

        function populateFormSelects() {
            const acSelect = document.getElementById('form_asset_class');
            const coSelect = document.getElementById('form_county');
            
            acSelect.innerHTML = data.assetClasses.map(ac => `<option value="${ac.id}">${ac.name}</option>`).join('');
            coSelect.innerHTML = data.counties.map(c => `<option value="${c.id}">${c.county_name}, ${c.state}</option>`).join('');
        }

        async function addLocation(e) {
            e.preventDefault();
            const payload = {
                name: document.getElementById('form_name').value,
                address: document.getElementById('form_address').value,
                latitude: parseFloat(document.getElementById('form_lat').value),
                longitude: parseFloat(document.getElementById('form_lng').value),
                square_footage: parseInt(document.getElementById('form_sqft').value),
                lot_size: parseFloat(document.getElementById('form_lot').value),
                annual_tax: parseFloat(document.getElementById('form_tax').value),
                asset_class_id: parseInt(document.getElementById('form_asset_class').value),
                county_id: parseInt(document.getElementById('form_county').value)
            };

            const res = await fetch('/api/locations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                document.getElementById('locationForm').reset();
                fetchAll();
            }
        }

        window.onload = () => {
            initMap();
            fetchAll();
        };
    </script>
</body>
</html>'''

from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/real_track.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class AssetClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    counties = db.relationship('County', backref='asset_class', lazy=True, cascade="all, delete-orphan")
    locations = db.relationship('Location', backref='asset_class', lazy=True, cascade="all, delete-orphan")

class County(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    county_name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(10), nullable=False)
    asset_class_id = db.Column(db.Integer, db.ForeignKey('asset_class.id'), nullable=False)
    locations = db.relationship('Location', backref='county', lazy=True)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    square_footage = db.Column(db.Float, default=0)
    lot_size = db.Column(db.Float, default=0)
    tax_value = db.Column(db.Float, default=0)
    asset_class_id = db.Column(db.Integer, db.ForeignKey('asset_class.id'), nullable=False)
    county_id = db.Column(db.Integer, db.ForeignKey('county.id'), nullable=True)

with app.app_context():
    db.create_all()

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
    return jsonify([{'id': c.id, 'name': c.name} for c in AssetClass.query.all()])

@app.route('/api/asset-classes/<int:id>', methods=['DELETE'])
def delete_asset_class(id):
    ac = AssetClass.query.get_or_404(id)
    db.session.delete(ac)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/counties', methods=['GET', 'POST'])
def handle_counties():
    if request.method == 'POST':
        data = request.json
        new_county = County(county_name=data['county_name'], state=data['state'], asset_class_id=data['asset_class_id'])
        db.session.add(new_county)
        db.session.commit()
        return jsonify({'id': new_county.id, 'county_name': new_county.county_name, 'state': new_county.state}), 201
    
    acid = request.args.get('asset_class_id')
    query = County.query
    if acid: query = query.filter_by(asset_class_id=acid)
    return jsonify([{'id': c.id, 'county_name': c.county_name, 'state': c.state, 'asset_class_id': c.asset_class_id} for c in query.all()])

@app.route('/api/counties/<int:id>', methods=['DELETE'])
def delete_county(id):
    c = County.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/locations', methods=['GET', 'POST'])
def handle_locations():
    if request.method == 'POST':
        data = request.json
        new_loc = Location(
            name=data['name'], address=data.get('address'),
            latitude=data.get('latitude'), longitude=data.get('longitude'),
            square_footage=data.get('square_footage', 0),
            lot_size=data.get('lot_size', 0), tax_value=data.get('tax_value', 0),
            asset_class_id=data['asset_class_id'], county_id=data.get('county_id')
        )
        db.session.add(new_loc)
        db.session.commit()
        return jsonify({'id': new_loc.id}), 201
    
    locs = Location.query.all()
    return jsonify([{
        'id': l.id, 'name': l.name, 'address': l.address,
        'latitude': l.latitude, 'longitude': l.longitude,
        'square_footage': l.square_footage, 'lot_size': l.lot_size,
        'tax_value': l.tax_value, 'asset_class_id': l.asset_class_id,
        'county_id': l.county_id
    } for l in locs])

@app.route('/api/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    loc = Location.query.get_or_404(id)
    db.session.delete(loc)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
