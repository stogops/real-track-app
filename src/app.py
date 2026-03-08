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
    counties = db.relationship('County', backref='asset_class', lazy=True, cascade="all, delete-orphan")
    locations = db.relationship('Location', backref='asset_class', lazy=True, cascade="all, delete-orphan")

class County(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    asset_class_id = db.Column(db.Integer, db.ForeignKey('asset_class.id'), nullable=False)
    locations = db.relationship('Location', backref='county', lazy=True)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    square_footage = db.Column(db.Float, default=0)
    lot_size = db.Column(db.Float, default=0)
    tax_value = db.Column(db.Float, default=0)
    asset_class_id = db.Column(db.Integer, db.ForeignKey('asset_class.id'), nullable=False)
    county_id = db.Column(db.Integer, db.ForeignKey('county.id'), nullable=True)


# Create database and tables
with app.app_context():
    # Ensure directory exists for sqlite (though usually /data is a mount point)
    os.makedirs('/data', exist_ok=True)
    db.create_all()

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Track Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        #map { height: 400px; width: 100%; border-radius: 0.5rem; }
        .custom-scroll::-webkit-scrollbar { width: 4px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    </style>
</head>
<body class="bg-gray-50 font-sans">
    <div class="max-w-7xl mx-auto px-4 py-6">
        <header class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold text-slate-800">Real Track</h1>
            <div class="flex items-center gap-4">
                <span class="text-sm font-medium text-gray-600">Map Mode:</span>
                <select id="mapMode" onchange="renderMap()" class="border rounded px-2 py-1 text-sm bg-white">
                    <option value="pins">Pins</option>
                    <option value="sqft">SqFt Heatmap</option>
                </select>
                <button onclick="fetchAll()" class="bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700 transition">Refresh Data</button>
            </div>
        </header>

        <!-- Map Section -->
        <div class="bg-white p-2 rounded-xl shadow-sm mb-6">
            <div id="map"></div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <!-- Left Column: Settings -->
            <div class="space-y-6">
                <!-- Asset Classes -->
                <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h2 class="text-lg font-semibold mb-4 text-slate-700">Asset Classes</h2>
                    <div class="flex gap-2 mb-4">
                        <input id="newClassName" type="text" placeholder="e.g. Industrial" class="flex-1 border rounded px-3 py-1.5 text-sm">
                        <button onclick="addClass()" class="bg-green-600 text-white px-3 py-1.5 rounded text-sm hover:bg-green-700">+</button>
                    </div>
                    <ul id="classList" class="space-y-2 max-h-48 overflow-y-auto custom-scroll"></ul>
                </div>

                <!-- Counties -->
                <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h2 class="text-lg font-semibold mb-4 text-slate-700">Counties of Interest</h2>
                    <div class="flex gap-2 mb-4">
                        <input id="newCountyName" type="text" placeholder="e.g. Cook County" class="flex-1 border rounded px-3 py-1.5 text-sm">
                        <button onclick="addCounty()" class="bg-green-600 text-white px-3 py-1.5 rounded text-sm hover:bg-green-700">+</button>
                    </div>
                    <ul id="countyList" class="space-y-2 max-h-48 overflow-y-auto custom-scroll"></ul>
                </div>
            </div>

            <!-- Right Column: Locations Management -->
            <div class="lg:col-span-2 space-y-6">
                <!-- Add Location Form -->
                <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h2 class="text-lg font-semibold mb-4 text-slate-700">Add New Location</h2>
                    <form id="locationForm" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <input type="text" id="locName" placeholder="Name" required class="border rounded px-3 py-2 text-sm">
                        <input type="text" id="locAddress" placeholder="Address" required class="border rounded px-3 py-2 text-sm">
                        <input type="number" step="any" id="locLat" placeholder="Latitude" required class="border rounded px-3 py-2 text-sm">
                        <input type="number" step="any" id="locLng" placeholder="Longitude" required class="border rounded px-3 py-2 text-sm">
                        <input type="number" id="locSqFt" placeholder="SqFt" class="border rounded px-3 py-2 text-sm">
                        <input type="number" id="locLot" placeholder="Lot Size (Acres)" class="border rounded px-3 py-2 text-sm">
                        <input type="number" id="locTax" placeholder="Tax Value ($)" class="border rounded px-3 py-2 text-sm">
                        
                        <select id="locClass" onchange="filterCountyDropdown()" required class="border rounded px-3 py-2 text-sm bg-white">
                            <option value="">Select Asset Class</option>
                        </select>
                        
                        <select id="locCounty" required class="border rounded px-3 py-2 text-sm bg-white">
                            <option value="">Select County</option>
                        </select>

                        <button type="submit" class="md:col-span-3 bg-blue-600 text-white font-bold py-2 rounded-lg hover:bg-blue-700 transition shadow-md mt-2">
                            Save Location
                        </button>
                    </form>
                </div>

                <!-- Locations List -->
                <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h2 class="text-lg font-semibold mb-4 text-slate-700">Stored Locations</h2>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-sm">
                            <thead>
                                <tr class="border-b text-gray-400">
                                    <th class="pb-3 font-medium">Name</th>
                                    <th class="pb-3 font-medium">Class</th>
                                    <th class="pb-3 font-medium">SqFt</th>
                                    <th class="pb-3 font-medium">County</th>
                                    <th class="pb-3 font-medium">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="locationTableBody" class="divide-y divide-gray-50"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let map, markersLayer;
        let data = { classes: [], counties: [], locations: [] };

        // Initialize Map
        function initMap() {
            map = L.map('map').setView([39.8283, -98.5795], 4);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            markersLayer = L.layerGroup().addTo(map);
        }

        async function fetchAll() {
            try {
                const [cRes, coRes, lRes] = await Promise.all([
                    fetch('/api/asset-classes'),
                    fetch('/api/counties'),
                    fetch('/api/locations')
                ]);
                data.classes = await cRes.json();
                data.counties = await coRes.json();
                data.locations = await lRes.json();
                
                renderClasses();
                renderCounties();
                renderLocations();
                renderMap();
                updateDropdowns();
            } catch (err) { console.error("Fetch error:", err); }
        }

        function renderClasses() {
            const list = document.getElementById('classList');
            list.innerHTML = data.classes.map(c => `
                <li class="flex justify-between items-center text-sm p-2 bg-slate-50 rounded">
                    <span>${c.name}</span>
                    <button onclick="deleteItem('asset-classes', ${c.id})" class="text-red-500 hover:text-red-700">&times;</button>
                </li>
            `).join('');
        }

        function renderCounties() {
            const list = document.getElementById('countyList');
            list.innerHTML = data.counties.map(c => `
                <li class="flex justify-between items-center text-sm p-2 bg-slate-50 rounded">
                    <span>${c.name}</span>
                    <button onclick="deleteItem('counties', ${c.id})" class="text-red-500 hover:text-red-700">&times;</button>
                </li>
            `).join('');
        }

        function renderLocations() {
            const tbody = document.getElementById('locationTableBody');
            tbody.innerHTML = data.locations.map(l => `
                <tr class="hover:bg-gray-50 transition">
                    <td class="py-3 font-medium">${l.name}</td>
                    <td class="py-3 text-gray-600">${l.asset_class_name || 'N/A'}</td>
                    <td class="py-3 text-gray-600">${Number(l.sqft).toLocaleString()}</td>
                    <td class="py-3 text-gray-600">${l.county_name || 'N/A'}</td>
                    <td class="py-3">
                        <button onclick="deleteItem('locations', ${l.id})" class="text-red-500 hover:underline">Delete</button>
                    </td>
                </tr>
            `).join('');
        }

        function updateDropdowns() {
            const classSel = document.getElementById('locClass');
            const countySel = document.getElementById('locCounty');
            
            const classVal = classSel.value;
            const countyVal = countySel.value;

            classSel.innerHTML = '<option value="">Select Asset Class</option>' + 
                data.classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            
            countySel.innerHTML = '<option value="">Select County</option>' + 
                data.counties.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

            classSel.value = classVal;
            countySel.value = countyVal;
        }

        function filterCountyDropdown() {
            // Functional hook for logic if assets were strictly linked to counties
            // For this app, we ensure the dropdowns are current
            console.log("Filtering based on class:", document.getElementById('locClass').value);
        }

        function renderMap() {
            markersLayer.clearLayers();
            const mode = document.getElementById('mapMode').value;
            const bounds = [];

            data.locations.forEach(loc => {
                const pos = [loc.lat, loc.lng];
                bounds.push(pos);

                if (mode === 'sqft') {
                    const radius = Math.sqrt(loc.sqft || 1000) * 0.5;
                    L.circle(pos, {
                        color: '#3b82f6',
                        fillColor: '#3b82f6',
                        fillOpacity: 0.4,
                        radius: radius
                    }).addTo(markersLayer).bindPopup(`<b>${loc.name}</b><br>${loc.sqft} SqFt`);
                } else {
                    L.marker(pos).addTo(markersLayer).bindPopup(`<b>${loc.name}</b><br>${loc.address}`);
                }
            });

            if (bounds.length > 0) map.fitBounds(bounds, { padding: [50, 50] });
        }

        async function addClass() {
            const name = document.getElementById('newClassName').value;
            if (!name) return;
            await fetch('/api/asset-classes', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name })
            });
            document.getElementById('newClassName').value = '';
            fetchAll();
        }

        async function addCounty() {
            const name = document.getElementById('newCountyName').value;
            if (!name) return;
            await fetch('/api/counties', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name })
            });
            document.getElementById('newCountyName').value = '';
            fetchAll();
        }

        document.getElementById('locationForm').onsubmit = async (e) => {
            e.preventDefault();
            const payload = {
                name: document.getElementById('locName').value,
                address: document.getElementById('locAddress').value,
                lat: parseFloat(document.getElementById('locLat').value),
                lng: parseFloat(document.getElementById('locLng').value),
                sqft: parseInt(document.getElementById('locSqFt').value) || 0,
                lot_size: parseFloat(document.getElementById('locLot').value) || 0,
                tax_value: parseFloat(document.getElementById('locTax').value) || 0,
                asset_class_id: parseInt(document.getElementById('locClass').value),
                county_id: parseInt(document.getElementById('locCounty').value)
            };

            await fetch('/api/locations', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            e.target.reset();
            fetchAll();
        };

        async function deleteItem(endpoint, id) {
            if (!confirm('Are you sure?')) return;
            await fetch(`/api/${endpoint}/${id}`, { method: 'DELETE' });
            fetchAll();
        }

        window.onload = () => {
            initMap();
            fetchAll();
        };
    </script>
</body>
</html>'''

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



@app.route('/api/counties', methods=['GET', 'POST'])
def handle_counties():
    if request.method == 'POST':
        data = request.json
        new_county = County(name=data['name'], asset_class_id=data['asset_class_id'])
        db.session.add(new_county)
        db.session.commit()
        return jsonify({'id': new_county.id, 'name': new_county.name, 'asset_class_id': new_county.asset_class_id}), 201
    else:
        acid = request.args.get('asset_class_id')
        if acid:
            counties = County.query.filter_by(asset_class_id=acid).all()
        else:
            counties = County.query.all()
        return jsonify([{'id': c.id, 'name': c.name, 'asset_class_id': c.asset_class_id} for c in counties])

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
            name=data['name'], 
            address=data.get('address'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            square_footage=data.get('square_footage', 0),
            county_id=data.get('county_id'),
            lot_size=data.get('lot_size', 0),
            tax_value=data.get('tax_value', 0),
            asset_class_id=data['asset_class_id']
        )
        db.session.add(new_loc)
        db.session.commit()
        return jsonify({
            'id': new_loc.id, 'name': new_loc.name, 'address': new_loc.address,
            'latitude': new_loc.latitude, 'longitude': new_loc.longitude,
            'square_footage': new_loc.square_footage, 'county_id': new_loc.county_id, 'lot_size': new_loc.lot_size,
            'tax_value': new_loc.tax_value, 'asset_class_id': new_loc.asset_class_id
        }), 201
    else:
        locs = Location.query.all()
        return jsonify([{
            'id': l.id, 'name': l.name, 'address': l.address,
            'latitude': l.latitude, 'longitude': l.longitude,
            'square_footage': l.square_footage, 'county_id': l.county_id, 'lot_size': l.lot_size,
            'tax_value': l.tax_value, 'asset_class_id': l.asset_class_id
        } for l in locs])

@app.route('/api/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    loc = Location.query.get_or_404(id)
    db.session.delete(loc)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)