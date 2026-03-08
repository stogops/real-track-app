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
        #map { height: 62vh; min-height: 420px; width: 100%; border-radius: 0.75rem; }
        .sidebar-item.active { background-color: #2563eb; color: white; }
        .modal-backdrop { background: rgba(17, 24, 39, 0.55); }
    </style>
</head>
<body class="bg-slate-100 text-gray-900">
    <div class="min-h-screen flex flex-col">
        <header class="bg-white border-b">
            <div class="max-w-7xl mx-auto px-4 py-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 class="text-2xl font-bold text-blue-700">Real Track</h1>
                    <p id="selectionSummary" class="text-sm text-gray-600">Loading filters...</p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <button onclick="openModal('locationModal')" class="bg-blue-600 text-white text-sm font-semibold px-4 py-2 rounded hover:bg-blue-700">Add Location</button>
                    <button onclick="openModal('assetClassModal')" class="bg-white border border-gray-300 text-sm font-semibold px-4 py-2 rounded hover:bg-gray-50">Add Asset Class</button>
                    <button onclick="openModal('countyModal')" class="bg-white border border-gray-300 text-sm font-semibold px-4 py-2 rounded hover:bg-gray-50">Add County</button>
                    <label for="mapMode" class="text-sm font-medium ml-1">Map:</label>
                    <select id="mapMode" onchange="updateMarkers()" class="border rounded px-2 py-2 bg-white text-sm">
                        <option value="pins">Pins</option>
                        <option value="sqft">Square Footage</option>
                    </select>
                </div>
            </div>
        </header>

        <main class="max-w-7xl w-full mx-auto px-4 py-4 flex-1 flex flex-col gap-4">
            <section class="bg-white p-3 rounded-xl border shadow-sm">
                <div id="map"></div>
            </section>
            <section class="grid grid-cols-1 lg:grid-cols-12 gap-4 pb-4">
                <aside class="lg:col-span-4 xl:col-span-3 bg-white border rounded-xl p-4 shadow-sm space-y-6">
                    <div>
                        <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Asset Classes</h2>
                        <ul id="assetClassList" class="space-y-1"></ul>
                    </div>
                    <div>
                        <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Counties</h2>
                        <ul id="countyList" class="space-y-1"></ul>
                    </div>
                </aside>
                <section class="lg:col-span-8 xl:col-span-9 bg-white border rounded-xl p-4 shadow-sm">
                    <div class="flex items-center justify-between mb-3">
                        <h2 class="text-lg font-semibold">Locations</h2>
                        <span id="locationCount" class="text-sm text-gray-600"></span>
                    </div>
                    <div id="locationList" class="space-y-3"></div>
                </section>
            </section>
        </main>
    </div>

    <div id="assetClassModal" class="fixed inset-0 modal-backdrop hidden items-center justify-center p-4 z-40" onclick="backdropClose(event, 'assetClassModal')">
        <div class="w-full max-w-md bg-white rounded-lg shadow-xl border p-5">
            <h3 class="text-lg font-semibold mb-4">Add Asset Class</h3>
            <form id="assetClassForm" onsubmit="addAssetClass(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-gray-700">Asset Class Name</label>
                    <input type="text" id="asset_class_name" required class="w-full border rounded p-2 mt-1">
                </div>
                <div class="flex justify-end gap-2">
                    <button type="button" onclick="closeModal('assetClassModal')" class="px-3 py-2 text-sm border rounded">Cancel</button>
                    <button type="submit" class="px-3 py-2 text-sm bg-blue-600 text-white rounded">Save</button>
                </div>
            </form>
        </div>
    </div>

    <div id="countyModal" class="fixed inset-0 modal-backdrop hidden items-center justify-center p-4 z-40" onclick="backdropClose(event, 'countyModal')">
        <div class="w-full max-w-md bg-white rounded-lg shadow-xl border p-5">
            <h3 class="text-lg font-semibold mb-4">Add County of Interest</h3>
            <form id="countyForm" onsubmit="addCounty(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-gray-700">Asset Class</label>
                    <select id="county_asset_class" required class="w-full border rounded p-2 mt-1"></select>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-700">County</label>
                    <input type="text" id="county_name" required class="w-full border rounded p-2 mt-1">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-700">State</label>
                    <input type="text" id="county_state" required maxlength="10" class="w-full border rounded p-2 mt-1">
                </div>
                <div class="flex justify-end gap-2">
                    <button type="button" onclick="closeModal('countyModal')" class="px-3 py-2 text-sm border rounded">Cancel</button>
                    <button type="submit" class="px-3 py-2 text-sm bg-blue-600 text-white rounded">Save</button>
                </div>
            </form>
        </div>
    </div>

    <div id="locationModal" class="fixed inset-0 modal-backdrop hidden items-center justify-center p-4 z-40 overflow-y-auto" onclick="backdropClose(event, 'locationModal')">
        <div class="w-full max-w-2xl bg-white rounded-lg shadow-xl border p-5 my-8">
            <h3 class="text-lg font-semibold mb-4">Add New Location</h3>
            <form id="locationForm" onsubmit="addLocation(event)" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="md:col-span-2">
                    <label class="block text-xs font-medium">Name</label>
                    <input type="text" id="form_name" required class="w-full border rounded p-2 mt-1">
                </div>
                <div class="md:col-span-2">
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
                    <select id="form_asset_class" required class="w-full border rounded p-2 mt-1"></select>
                </div>
                <div class="md:col-span-2">
                    <label class="block text-xs font-medium">County</label>
                    <select id="form_county" class="w-full border rounded p-2 mt-1"></select>
                </div>
                <div class="md:col-span-2 flex justify-end gap-2">
                    <button type="button" onclick="closeModal('locationModal')" class="px-3 py-2 text-sm border rounded">Cancel</button>
                    <button type="submit" class="px-3 py-2 text-sm bg-blue-600 text-white rounded">Save Location</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let map;
        let markersGroup;
        let currentAssetClassId = null;
        let currentCountyId = null;
        let data = {
            assetClasses: [],
            counties: [],
            locations: []
        };

        function openModal(id) {
            const modal = document.getElementById(id);
            if (!modal) return;
            if (id === 'locationModal') {
                syncLocationModalOptions();
            }
            if (id === 'countyModal') {
                syncCountyModalOptions();
            }
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }

        function closeModal(id) {
            const modal = document.getElementById(id);
            if (!modal) return;
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }

        function backdropClose(event, id) {
            if (event.target.id === id) {
                closeModal(id);
            }
        }

        function parseUrlIntParam(key) {
            const raw = new URLSearchParams(window.location.search).get(key);
            if (!raw) return null;
            const parsed = parseInt(raw, 10);
            return Number.isNaN(parsed) ? null : parsed;
        }

        function syncFiltersToUrl() {
            const params = new URLSearchParams(window.location.search);
            if (currentAssetClassId) {
                params.set('assetClass', String(currentAssetClassId));
            } else {
                params.delete('assetClass');
            }
            if (currentCountyId) {
                params.set('county', String(currentCountyId));
            } else {
                params.delete('county');
            }
            const query = params.toString();
            const nextUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
            window.history.replaceState({}, '', nextUrl);
        }

        function ensureSelectedFilters() {
            if (data.assetClasses.length === 0) {
                currentAssetClassId = null;
                currentCountyId = null;
                return;
            }

            const urlAssetClassId = parseUrlIntParam('assetClass');
            const urlCountyId = parseUrlIntParam('county');

            const validAsset = data.assetClasses.some(ac => ac.id === currentAssetClassId) ? currentAssetClassId : null;
            currentAssetClassId = data.assetClasses.some(ac => ac.id === urlAssetClassId) ? urlAssetClassId : validAsset;
            if (!currentAssetClassId) {
                currentAssetClassId = data.assetClasses[0].id;
            }

            const filteredCounties = data.counties.filter(c => c.asset_class_id === currentAssetClassId);
            if (filteredCounties.some(c => c.id === urlCountyId)) {
                currentCountyId = urlCountyId;
            } else if (!filteredCounties.some(c => c.id === currentCountyId)) {
                currentCountyId = null;
            }
        }

        function initMap() {
            map = L.map('map').setView([37.0902, -95.7129], 4);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);
            markersGroup = L.layerGroup().addTo(map);
        }

        function getFilteredLocations() {
            return data.locations.filter(l => {
                if (l.asset_class_id !== currentAssetClassId) return false;
                if (currentCountyId !== null && l.county_id !== currentCountyId) return false;
                return true;
            });
        }

        function getMappableLocations() {
            return getFilteredLocations().filter(l => Number.isFinite(l.latitude) && Number.isFinite(l.longitude));
        }

        function getSelectedAssetClass() {
            return data.assetClasses.find(ac => ac.id === currentAssetClassId) || null;
        }

        function getSelectedCounty() {
            return data.counties.find(c => c.id === currentCountyId) || null;
        }

        function selectClass(id) {
            currentAssetClassId = id;
            const validCounty = data.counties.some(c => c.id === currentCountyId && c.asset_class_id === id);
            if (!validCounty) {
                currentCountyId = null;
            }
            syncFiltersToUrl();
            renderUI();
        }

        function selectCounty(id) {
            currentCountyId = id;
            syncFiltersToUrl();
            renderUI();
        }

        function renderUI() {
            const selectedAssetClass = getSelectedAssetClass();
            const selectedCounty = getSelectedCounty();
            const filteredCounties = data.counties.filter(c => c.asset_class_id === currentAssetClassId);
            const filteredLocations = getFilteredLocations();

            document.getElementById('selectionSummary').textContent = selectedAssetClass
                ? `Viewing ${selectedAssetClass.name}${selectedCounty ? ` in ${selectedCounty.county_name}, ${selectedCounty.state}` : ' across all counties'}`
                : 'No asset class selected';

            const acList = document.getElementById('assetClassList');
            acList.innerHTML = data.assetClasses.map(ac => `
                <li>
                    <button onclick="selectClass(${ac.id})" class="sidebar-item w-full text-left px-3 py-2 rounded-md text-sm transition ${currentAssetClassId === ac.id ? 'active' : 'hover:bg-gray-100 text-gray-700'}">
                        ${ac.name}
                    </button>
                </li>
            `).join('');

            const cList = document.getElementById('countyList');
            if (filteredCounties.length === 0) {
                cList.innerHTML = '<li class="px-3 py-2 text-sm text-gray-500 italic">No counties for this asset class.</li>';
            } else {
                const allActive = currentCountyId === null;
                cList.innerHTML = `
                    <li>
                        <button onclick="selectCounty(null)" class="sidebar-item w-full text-left px-3 py-2 rounded-md text-sm transition ${allActive ? 'active' : 'hover:bg-gray-100 text-gray-700'}">
                            All Counties
                        </button>
                    </li>
                ` + filteredCounties.map(c => `
                    <li>
                        <button onclick="selectCounty(${c.id})" class="sidebar-item w-full text-left px-3 py-2 rounded-md text-sm transition ${currentCountyId === c.id ? 'active' : 'hover:bg-gray-100 text-gray-700'}">
                            ${c.county_name}, ${c.state}
                        </button>
                    </li>
                `).join('');
            }

            document.getElementById('locationCount').textContent = `${filteredLocations.length} location${filteredLocations.length === 1 ? '' : 's'}`;

            const lList = document.getElementById('locationList');
            lList.innerHTML = filteredLocations.length
                ? filteredLocations.map(l => `
                    <div class="p-4 border rounded-lg">
                        <div class="font-semibold">${l.name}</div>
                        <div class="text-xs text-gray-500">${l.address || ''}</div>
                        <div class="mt-2 text-sm grid grid-cols-1 sm:grid-cols-3 gap-1 text-gray-700">
                            <span>SqFt: ${(l.square_footage || 0).toLocaleString()}</span>
                            <span>Lot: ${l.lot_size || 0} ac</span>
                            <span>Tax: $${(l.tax_value || 0).toLocaleString()}</span>
                        </div>
                    </div>
                `).join('')
                : '<div class="p-4 border rounded-lg text-sm text-gray-500 italic">No locations match the selected filters.</div>';

            syncCountyModalOptions();
            syncLocationModalOptions();
            updateMarkers();
        }

        function updateMarkers() {
            markersGroup.clearLayers();
            const mode = document.getElementById('mapMode').value;
            const visibleLocations = getMappableLocations();

            if (visibleLocations.length === 0) return;

            const maxSqFt = Math.max(...visibleLocations.map(l => l.square_footage || 1));
            const bounds = L.latLngBounds();

            visibleLocations.forEach(l => {
                const pos = [l.latitude, l.longitude];
                bounds.extend(pos);

                if (mode === 'pins') {
                    L.marker(pos)
                        .bindPopup(`<b>${l.name}</b><br>${l.address || ''}`)
                        .addTo(markersGroup);
                } else {
                    const scaleFactor = 500;
                    const radius = Math.sqrt((l.square_footage || 1) / maxSqFt) * scaleFactor;

                    L.circle(pos, {
                        radius: radius,
                        color: '#2563eb',
                        fillColor: '#2563eb',
                        fillOpacity: 0.45
                    })
                    .bindPopup(`<b>${l.name}</b><br>SqFt: ${(l.square_footage || 0).toLocaleString()}`)
                    .addTo(markersGroup);
                }
            });

            if (bounds.isValid()) {
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        }

        function syncCountyModalOptions() {
            const select = document.getElementById('county_asset_class');
            select.innerHTML = data.assetClasses.map(ac => `<option value="${ac.id}">${ac.name}</option>`).join('');
            if (currentAssetClassId) {
                select.value = String(currentAssetClassId);
            }
        }

        function renderLocationCountyOptions(assetClassId) {
            const acSelect = document.getElementById('form_asset_class');
            const coSelect = document.getElementById('form_county');
            const selectedId = assetClassId || parseInt(acSelect.value, 10);
            const filteredCounties = data.counties.filter(c => c.asset_class_id === selectedId);
            coSelect.innerHTML = filteredCounties.map(c => `<option value="${c.id}">${c.county_name}, ${c.state}</option>`).join('');
            if (filteredCounties.length === 0) {
                coSelect.innerHTML = '<option value="">No counties available</option>';
            } else if (currentCountyId && filteredCounties.some(c => c.id === currentCountyId)) {
                coSelect.value = String(currentCountyId);
            }
        }

        function syncLocationModalOptions() {
            const acSelect = document.getElementById('form_asset_class');
            acSelect.innerHTML = data.assetClasses.map(ac => `<option value="${ac.id}">${ac.name}</option>`).join('');
            if (currentAssetClassId) {
                acSelect.value = String(currentAssetClassId);
            }
            renderLocationCountyOptions(parseInt(acSelect.value, 10));
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

                ensureSelectedFilters();
                syncFiltersToUrl();
                renderUI();
            } catch (err) {
                console.error('Error fetching data:', err);
            }
        }

        async function addAssetClass(e) {
            e.preventDefault();
            const payload = { name: document.getElementById('asset_class_name').value.trim() };
            if (!payload.name) return;
            const res = await fetch('/api/asset-classes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                document.getElementById('assetClassForm').reset();
                closeModal('assetClassModal');
                await fetchAll();
            }
        }

        async function addCounty(e) {
            e.preventDefault();
            const payload = {
                county_name: document.getElementById('county_name').value.trim(),
                state: document.getElementById('county_state').value.trim(),
                asset_class_id: parseInt(document.getElementById('county_asset_class').value, 10)
            };
            const res = await fetch('/api/counties', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                document.getElementById('countyForm').reset();
                closeModal('countyModal');
                await fetchAll();
            }
        }

        async function addLocation(e) {
            e.preventDefault();
            const countyValue = document.getElementById('form_county').value;
            const payload = {
                name: document.getElementById('form_name').value,
                address: document.getElementById('form_address').value,
                latitude: parseFloat(document.getElementById('form_lat').value),
                longitude: parseFloat(document.getElementById('form_lng').value),
                square_footage: parseInt(document.getElementById('form_sqft').value, 10),
                lot_size: parseFloat(document.getElementById('form_lot').value),
                tax_value: parseFloat(document.getElementById('form_tax').value),
                asset_class_id: parseInt(document.getElementById('form_asset_class').value, 10),
                county_id: countyValue ? parseInt(countyValue, 10) : null
            };

            const res = await fetch('/api/locations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                document.getElementById('locationForm').reset();
                closeModal('locationModal');
                await fetchAll();
            }
        }

        document.addEventListener('change', (event) => {
            if (event.target.id === 'form_asset_class') {
                renderLocationCountyOptions(parseInt(event.target.value, 10));
            }
        });

        window.onload = () => {
            initMap();
            fetchAll();
        };

        window.addEventListener('popstate', () => {
            ensureSelectedFilters();
            renderUI();
        });
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
