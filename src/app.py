
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
    locations = db.relationship('Location', backref='asset_class', lazy=True, cascade="all, delete-orphan")

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    asset_class_id = db.Column(db.Integer, db.ForeignKey('asset_class.id'), nullable=False)

with app.app_context():
    db.create_all()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Track</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-6">
    <div class="max-w-5xl mx-auto">
        <h1 class="text-3xl font-bold mb-6 text-emerald-600">Real Track</h1>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <!-- Asset Classes Section -->
            <div class="md:col-span-1">
                <div class="bg-white p-6 rounded-lg shadow-md mb-6">
                    <h2 class="text-xl font-semibold mb-4">Asset Classes</h2>
                    <div id="assetClassList" class="space-y-2 mb-4"></div>
                    <div class="flex gap-2">
                        <input type="text" id="newAssetClass" placeholder="New Asset Class..." class="flex-1 border rounded p-2 text-sm">
                        <button onclick="addAssetClass()" class="bg-emerald-500 text-white px-3 py-1 rounded hover:bg-emerald-600 text-sm">Add</button>
                    </div>
                </div>
            </div>

            <!-- Locations Section -->
            <div class="md:col-span-2">
                <div class="bg-white p-6 rounded-lg shadow-md mb-6">
                    <h2 class="text-xl font-semibold mb-4">Locations</h2>
                    
                    <div class="bg-gray-50 p-4 rounded mb-6 flex flex-col md:flex-row gap-4">
                        <input type="text" id="locName" placeholder="Location Name" class="flex-1 border rounded p-2 text-sm">
                        <input type="text" id="locAddress" placeholder="Address" class="flex-1 border rounded p-2 text-sm">
                        <select id="locAssetClass" class="border rounded p-2 text-sm"></select>
                        <button onclick="addLocation()" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">Add Location</button>
                    </div>

                    <div id="locationList" class="space-y-4"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function fetchAll() {
            const [classesRes, locsRes] = await Promise.all([
                fetch('/api/asset-classes'),
                fetch('/api/locations')
            ]);
            const classes = await classesRes.json();
            const locs = await locsRes.json();
            renderClasses(classes);
            renderLocations(locs, classes);
            updateAssetClassDropdown(classes);
        }

        function renderClasses(classes) {
            const list = document.getElementById('assetClassList');
            list.innerHTML = classes.map(c => `
                <div class="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <span>${c.name}</span>
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
                        <p class="text-sm text-gray-500">${l.address}</p>
                        <span class="inline-block bg-emerald-100 text-emerald-800 text-xs px-2 py-1 rounded mt-1">${classMap[l.asset_class_id] || 'Unknown'}</span>
                    </div>
                    <button onclick="deleteLocation(${l.id})" class="bg-red-100 text-red-600 px-3 py-1 rounded hover:bg-red-200 text-sm">Delete</button>
                </div>
            `).join('') || '<p class="text-gray-400 italic">No locations found</p>';
        }

        function updateAssetClassDropdown(classes) {
            const select = document.getElementById('locAssetClass');
            select.innerHTML = classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
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
            const asset_class_id = document.getElementById('locAssetClass').value;
            if (!name || !asset_class_id) return;
            await fetch('/api/locations', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, address, asset_class_id: parseInt(asset_class_id)})
            });
            document.getElementById('locName').value = '';
            document.getElementById('locAddress').value = '';
            fetchAll();
        }

        async function deleteLocation(id) {
            await fetch(`/api/locations/${id}`, {method: 'DELETE'});
            fetchAll();
        }

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
    return jsonify([{'id': l.id, 'name': l.name, 'address': l.address, 'asset_class_id': l.asset_class_id} for l in locs])

@app.route('/api/locations', methods=['POST'])
def add_location():
    data = request.json
    new_loc = Location(name=data['name'], address=data.get('address'), asset_class_id=data['asset_class_id'])
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
    app.run(host='0.0.0.0', port=8080)
