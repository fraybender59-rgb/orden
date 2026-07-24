from flask import Flask, request, jsonify, send_from_directory
import json
import os

app = Flask(__name__, static_folder='.')

ARCHIVO_PEDIDOS = 'pedidos.json'

def leer_pedidos():
    if not os.path.exists(ARCHIVO_PEDIDOS):
        return []
    with open(ARCHIVO_PEDIDOS, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def guardar_pedidos(pedidos):
    with open(ARCHIVO_PEDIDOS, 'w') as f:
        json.dump(pedidos, f)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

@app.route('/api/pedidos', methods=['GET'])
def get_pedidos():
    return jsonify(leer_pedidos())

@app.route('/api/pedidos', methods=['POST'])
def create_pedido():
    pedido = request.json
    pedido['estado'] = 'Activo'
    pedidos = leer_pedidos()
    pedidos.append(pedido)
    guardar_pedidos(pedidos)
    return jsonify({"status": "success"}), 201

# Actualizado para recibir cambios de total por descuento
@app.route('/api/pedidos/<pedido_id>', methods=['PATCH'])
def update_pedido(pedido_id):
    datos = request.json
    pedidos = leer_pedidos()
    for p in pedidos:
        if str(p.get('id')) == str(pedido_id):
            p['estado'] = datos.get('estado', p.get('estado'))
            if 'motivo' in datos:
                p['motivo'] = datos['motivo']
            if 'total' in datos:
                p['total'] = datos['total']
            break
    guardar_pedidos(pedidos)
    return jsonify({"status": "success"})

@app.route('/api/pedidos/<pedido_id>', methods=['DELETE'])
def delete_pedido(pedido_id):
    pedidos = leer_pedidos()
    pedidos = [p for p in pedidos if p.get('id') != str(pedido_id)]
    guardar_pedidos(pedidos)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
