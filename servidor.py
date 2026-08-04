from flask import Flask, request, jsonify, send_from_directory
import json
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- ARCHIVOS DE BASE DE DATOS LOCAL ---
ARCHIVO_PEDIDOS = 'pedidos.json'
ARCHIVO_MESEROS = 'meseros.json'
ARCHIVO_INVENTARIO = 'inventario.json'
ARCHIVO_VENTAS = 'ventas_cerradas.json'
ARCHIVO_MESAS = 'mesas_abiertas.json'

# --- INVENTARIO BASE POR DEFECTO ---
inventario_base = [
    {"id": "hamb_sencilla", "nombre": "Hamburguesa Sencilla", "stock": 100, "precio": 70},
    {"id": "hamb_doble", "nombre": "Hamburguesa Doble", "stock": 100, "precio": 100},
    {"id": "hd_sencillo", "nombre": "Hotdog Sencillo", "stock": 100, "precio": 50},
    {"id": "hd_orden", "nombre": "Orden Hotdogs", "stock": 100, "precio": 90},
    {"id": "hd_toluqueno", "nombre": "Hotdog Toluqueño", "stock": 100, "precio": 70},
    {"id": "papas", "nombre": "Papas Fritas", "stock": 100, "precio": 40},
    {"id": "refresco", "nombre": "Refresco", "stock": 100, "precio": 25}
]

# --- FUNCIONES DE LECTURA Y ESCRITURA ---
def leer_json(archivo, default_data):
    if not os.path.exists(archivo):
        guardar_json(archivo, default_data)
        return default_data
    with open(archivo, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return default_data

def guardar_json(archivo, data):
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# Inicialización de datos persistentes
def inicializar_datos():
    global inventario, meseros, ventas_cerradas, mesas_abiertas
    inventario = leer_json(ARCHIVO_INVENTARIO, inventario_base)
    meseros = leer_json(ARCHIVO_MESEROS, [
        {"user": "mesero1", "pass": "mesero1", "nombre": "Mesero 1"},
        {"user": "mesero2", "pass": "mesero2", "nombre": "Mesero 2"}
    ])
    ventas_cerradas = leer_json(ARCHIVO_VENTAS, [])
    mesas_abiertas = leer_json(ARCHIVO_MESAS, {})

inicializar_datos()

@app.route('/')
def index(): return app.send_static_file('index.html')

@app.route('/<path:path>')
def servir_html(path): return app.send_static_file(path)

# --- INVENTARIO ---
@app.route('/api/inventario', methods=['GET'])
def obtener_inventario(): 
    return jsonify(leer_json(ARCHIVO_INVENTARIO, inventario_base))

@app.route('/api/inventario/reiniciar', methods=['POST'])
def reiniciar_inventario():
    inventario_actual = leer_json(ARCHIVO_INVENTARIO, inventario_base)
    for item in inventario_actual: item['stock'] = 100
    guardar_json(ARCHIVO_INVENTARIO, inventario_actual)
    return jsonify({"status": "ok", "mensaje": "Stock reiniciado a 100pz y guardado."})

# --- MESEROS ---
@app.route('/api/meseros', methods=['GET'])
def get_meseros(): 
    return jsonify(leer_json(ARCHIVO_MESEROS, []))

@app.route('/api/meseros/login', methods=['POST'])
def login_mesero():
    data = request.get_json()
    meseros_actuales = leer_json(ARCHIVO_MESEROS, [])
    for m in meseros_actuales:
        if m['user'] == data.get('user') and m['pass'] == data.get('pass'):
            return jsonify({"status": "ok", "nombre": m['nombre']})
    return jsonify({"error": "Credenciales incorrectas"}), 401

# --- IMÁGENES ---
@app.route('/api/subir_imagen', methods=['POST'])
def subir_imagen():
    if 'file' not in request.files: return jsonify({"error": "No hay archivo"}), 400
    file = request.files['file']
    id_pedido = request.form.get('id_pedido', 'desconocido')
    filename = secure_filename(f"{id_pedido}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({"status": "ok", "url": f"/uploads/{filename}"})

@app.route('/uploads/<path:path>')
def servir_imagen(path):
    return send_from_directory(app.config['UPLOAD_FOLDER'], path)

# --- PEDIDOS Y CUENTAS ---
@app.route('/api/pedidos', methods=['GET'])
def listar_pedidos(): 
    return jsonify(leer_json(ARCHIVO_PEDIDOS, []))

@app.route('/api/pedidos/cobrar', methods=['POST'])
def cobrar_pedido():
    data = request.get_json()
    id_pedido = data.get('id')
    metodo = data.get('metodo')
    
    pedidos = leer_json(ARCHIVO_PEDIDOS, [])
    ventas = leer_json(ARCHIVO_VENTAS, [])
    
    pedido_a_cobrar = None
    pedidos_restantes = []
    
    for p in pedidos:
        if str(p.get('id')) == str(id_pedido): 
            pedido_a_cobrar = p
        else: 
            pedidos_restantes.append(p)
            
    if pedido_a_cobrar:
        pedido_a_cobrar['metodo_pago'] = metodo
        pedido_a_cobrar['hora_cobro'] = datetime.now().strftime("%H:%M:%S")
        pedido_a_cobrar['estado'] = 'Cobrado' if metodo != 'Cancelado' else 'Cancelado'
        
        ventas.append(pedido_a_cobrar)
        guardar_json(ARCHIVO_VENTAS, ventas)
        guardar_json(ARCHIVO_PEDIDOS, pedidos_restantes)
        return jsonify({"status": "ok"})
        
    return jsonify({"error": "Pedido no encontrado"}), 404

@app.route('/api/ventas_cerradas', methods=['GET'])
def obtener_ventas_cerradas(): 
    return jsonify(leer_json(ARCHIVO_VENTAS, []))

@app.route('/api/cierre_caja', methods=['POST'])
def cierre_caja():
    # En un sistema real, un cierre de caja archiva el archivo actual por fecha
    # Por ahora, simplemente limpiamos el registro actual
    guardar_json(ARCHIVO_VENTAS, [])
    return jsonify({"status": "ok", "mensaje": "Cierre de caja exitoso"})

@app.route('/api/mesas_activas', methods=['GET'])
def mesas_activas():
    mesas_db = leer_json(ARCHIVO_MESAS, {})
    activas = [mesa for mesa, datos in mesas_db.items() if len(datos.get('items', [])) > 0]
    return jsonify(activas)

@app.route('/api/pedir_cuenta', methods=['POST'])
def pedir_cuenta():
    data = request.get_json()
    nombre_mesa = data.get('mesa')
    mesas_db = leer_json(ARCHIVO_MESAS, {})
    
    if nombre_mesa in mesas_db and len(mesas_db[nombre_mesa]['items']) > 0:
        datos_mesa = mesas_db[nombre_mesa]
        nuevo_pedido = {
            "id": str(uuid.uuid4())[:8],
            "cliente": nombre_mesa,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": datos_mesa['items'],
            "total": datos_mesa['total'],
            "origen": "punto_staf"
        }
        
        pedidos = leer_json(ARCHIVO_PEDIDOS, [])
        pedidos.append(nuevo_pedido)
        guardar_json(ARCHIVO_PEDIDOS, pedidos)
        
        # Limpiar mesa
        mesas_db[nombre_mesa] = {"items": [], "total": 0}
        guardar_json(ARCHIVO_MESAS, mesas_db)
        
        return jsonify({"status": "ok"})
    return jsonify({"error": "Mesa vacía o no existe"}), 400

@app.route('/api/pedidos', methods=['POST'])
def crear_pedido():
    data = request.get_json()
    items_solicitados = data.get('items', [])
    mesa_destino = data.get('mesa', None)
    cerrar_cuenta = data.get('cerrar_cuenta', False)
    
    inventario_actual = leer_json(ARCHIVO_INVENTARIO, inventario_base)
    
    # Validar y descontar stock
    for item_pedido in items_solicitados:
        for prod_inv in inventario_actual:
            if prod_inv['nombre'] == item_pedido['nombre']:
                if prod_inv['stock'] - item_pedido['cantidad'] < 0:
                    return jsonify({"error": f"¡Stock agotado para {prod_inv['nombre']}!"}), 400
                prod_inv['stock'] -= item_pedido['cantidad']
                
    guardar_json(ARCHIVO_INVENTARIO, inventario_actual)
    
    total_pedido = sum(item['subtotal'] for item in items_solicitados)
    nuevo_pedido = {
        "id": str(uuid.uuid4())[:8],
        "cliente": data.get('cliente', 'Cliente Online'),
        "telefono": data.get('telefono', ''),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": items_solicitados,
        "total": total_pedido,
        "origen": data.get('origen', 'comandero')
    }
    
    if mesa_destino and not cerrar_cuenta:
        mesas_db = leer_json(ARCHIVO_MESAS, {})
        if mesa_destino not in mesas_db:
            mesas_db[mesa_destino] = {"items": [], "total": 0}
        mesas_db[mesa_destino]['items'].extend(items_solicitados)
        mesas_db[mesa_destino]['total'] += total_pedido
        guardar_json(ARCHIVO_MESAS, mesas_db)
        return jsonify({"status": "ok", "mensaje": "Añadido a la mesa"})
    else:
        if cerrar_cuenta:
            nuevo_pedido['metodo_pago'] = 'WhatsApp'
            nuevo_pedido['hora_cobro'] = datetime.now().strftime("%H:%M:%S")
            ventas = leer_json(ARCHIVO_VENTAS, [])
            ventas.append(nuevo_pedido)
            guardar_json(ARCHIVO_VENTAS, ventas)
            return jsonify({"status": "ok", "id": nuevo_pedido['id'], "mensaje": "Cuenta cerrada"})
        else:
            pedidos = leer_json(ARCHIVO_PEDIDOS, [])
            pedidos.append(nuevo_pedido)
            guardar_json(ARCHIVO_PEDIDOS, pedidos)
            return jsonify({"status": "ok", "id": nuevo_pedido['id']})
# --- ACTUALIZACIÓN DE PEDIDOS (DESCUENTOS Y ESTADOS) ---
@app.route('/api/pedidos/<pedido_id>', methods=['PATCH'])
def update_pedido(pedido_id):
    datos = request.json
    pedidos = leer_json(ARCHIVO_PEDIDOS, [])
    
    for p in pedidos:
        if str(p.get('id')) == str(pedido_id):
            p['estado'] = datos.get('estado', p.get('estado'))
            if 'motivo' in datos:
                p['motivo'] = datos['motivo']
            if 'total' in datos:
                p['total'] = datos['total']
            break
            
    guardar_json(ARCHIVO_PEDIDOS, pedidos)
    return jsonify({"status": "success"})

# --- ELIMINACIÓN DE PEDIDOS ---
@app.route('/api/pedidos/<pedido_id>', methods=['DELETE'])
def delete_pedido(pedido_id):
    pedidos = leer_json(ARCHIVO_PEDIDOS, [])
    # Filtramos para conservar todos los que NO coincidan con el ID a eliminar
    pedidos_filtrados = [p for p in pedidos if str(p.get('id')) != str(pedido_id)]
    
    guardar_json(ARCHIVO_PEDIDOS, pedidos_filtrados)
    return jsonify({"status": "success"})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
