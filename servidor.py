from flask import Flask, request, jsonify, send_from_directory
import json
import os
import uuid
from datetime import datetime

# Configuración de Flask para servir tus archivos HTML, JS e imágenes
app = Flask(__name__, static_folder='.', static_url_path='')

# ==========================================
# BASES DE DATOS EN MEMORIA Y ARCHIVOS
# ==========================================
ARCHIVO_PEDIDOS = 'pedidos.json'

# Historial de cobranzas del día y control de mesas de los meseros
ventas_cerradas = []
mesas_abiertas = {}

# Almacén centralizado iniciando en 100pz
inventario = [
    {"id": "hamb_sencilla", "nombre": "Hamburguesa Sencilla", "stock": 100, "precio": 70},
    {"id": "hamb_doble", "nombre": "Hamburguesa Doble", "stock": 100, "precio": 100},
    {"id": "papas", "nombre": "Papas Fritas", "stock": 100, "precio": 40},
    {"id": "refresco", "nombre": "Refresco", "stock": 100, "precio": 25}
]

# Función para cargar pedidos activos desde tu JSON
def leer_pedidos():
    if not os.path.exists(ARCHIVO_PEDIDOS):
        return []
    with open(ARCHIVO_PEDIDOS, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# Función para guardar pedidos activos
def guardar_pedidos(pedidos):
    with open(ARCHIVO_PEDIDOS, 'w') as f:
        json.dump(pedidos, f, indent=4)

# ==========================================
# RUTAS DE INTERFAZ WEB (Frontend)
# ==========================================
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def servir_html(path):
    return app.send_static_file(path)

# ==========================================
# RUTAS DEL ALMACÉN (INVENTARIO)
# ==========================================
@app.route('/api/inventario', methods=['GET'])
def obtener_inventario():
    return jsonify(inventario)

@app.route('/api/inventario/reiniciar', methods=['POST'])
def reiniciar_inventario():
    for item in inventario:
        item['stock'] = 100
    return jsonify({"status": "ok", "mensaje": "Stock reiniciado a 100pz"})

# ==========================================
# RUTAS DE ADMINISTRACIÓN (COBROS)
# ==========================================
@app.route('/api/pedidos', methods=['GET'])
def listar_pedidos():
    pedidos = leer_pedidos()
    return jsonify(pedidos)

# AQUÍ ESTÁ EL ARREGLO DEL POST PARA TARJETA/EFECTIVO
@app.route('/api/pedidos/cobrar', methods=['POST'])
def cobrar_pedido():
    data = request.get_json()
    id_pedido = data.get('id')
    metodo = data.get('metodo') # Recibe "efectivo" o "tarjeta" limpio
    
    pedidos = leer_pedidos()
    pedido_a_cobrar = None
    
    # Buscar el pedido y sacarlo de la lista de activos
    pedidos_restantes = []
    for p in pedidos:
        if str(p.get('id')) == str(id_pedido):
            pedido_a_cobrar = p
        else:
            pedidos_restantes.append(p)
            
    if pedido_a_cobrar:
        # Registrar método de pago y guardar en ventas cerradas
        pedido_a_cobrar['metodo_pago'] = metodo
        pedido_a_cobrar['hora_cobro'] = datetime.now().strftime("%H:%M:%S")
        ventas_cerradas.append(pedido_a_cobrar)
        
        # Actualizar el JSON de pedidos activos
        guardar_pedidos(pedidos_restantes)
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Pedido no encontrado"}), 404

@app.route('/api/ventas_cerradas', methods=['GET'])
def obtener_ventas_cerradas():
    return jsonify(ventas_cerradas)

@app.route('/api/cierre_caja', methods=['POST'])
def cierre_caja():
    global ventas_cerradas
    # Aquí en un futuro puedes guardar 'ventas_cerradas' en una base de datos histórica.
    # Por ahora, al hacer el corte, vaciamos la lista del día.
    ventas_cerradas = []
    return jsonify({"status": "ok", "mensaje": "Cierre de caja exitoso"})

# ==========================================
# RUTAS DEL COMANDERO STAFF (MESAS)
# ==========================================
@app.route('/api/mesas_activas', methods=['GET'])
def mesas_activas():
    # Devuelve solo los nombres de las mesas que tienen algo cargado
    activas = [mesa for mesa, datos in mesas_abiertas.items() if len(datos.get('items', [])) > 0]
    return jsonify(activas)

@app.route('/api/mesa_consumo', methods=['GET'])
def mesa_consumo():
    nombre_mesa = request.args.get('mesa')
    datos_mesa = mesas_abiertas.get(nombre_mesa, {"items": [], "total": 0})
    return jsonify(datos_mesa)

@app.route('/api/pedir_cuenta', methods=['POST'])
def pedir_cuenta():
    data = request.get_json()
    nombre_mesa = data.get('mesa')
    
    if nombre_mesa in mesas_abiertas and len(mesas_abiertas[nombre_mesa]['items']) > 0:
        datos_mesa = mesas_abiertas[nombre_mesa]
        
        # Crear un nuevo ticket para Administración
        nuevo_pedido = {
            "id": str(uuid.uuid4())[:8],
            "cliente": nombre_mesa,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": datos_mesa['items'],
            "total": datos_mesa['total']
        }
        
        # Guardarlo en pedidos.json (Bandeja de Administración)
        pedidos = leer_pedidos()
        pedidos.append(nuevo_pedido)
        guardar_pedidos(pedidos)
        
        # Liberar la mesa limpiando sus datos
        mesas_abiertas[nombre_mesa] = {"items": [], "total": 0}
        return jsonify({"status": "ok"})
    
    return jsonify({"error": "Mesa vacía o no existe"}), 400

# ==========================================
# CREAR UN NUEVO PEDIDO Y DESCONTAR INVENTARIO
# ==========================================
@app.route('/api/pedidos', methods=['POST'])
def crear_pedido():
    data = request.get_json()
    items_solicitados = data.get('items', [])
    mesa_destino = data.get('mesa', None) # Si viene de un mesero
    
    # 1. VERIFICACIÓN DE INVENTARIO
    for item_pedido in items_solicitados:
        # Buscamos el producto en el inventario por su nombre (o ID)
        for prod_inv in inventario:
            if prod_inv['nombre'] == item_pedido['nombre']:
                if prod_inv['stock'] - item_pedido['cantidad'] < 0:
                    return jsonify({"error": f"¡Stock agotado para {prod_inv['nombre']}!"}), 400

    # 2. DESCONTAR DEL INVENTARIO (Si pasó la verificación)
    for item_pedido in items_solicitados:
        for prod_inv in inventario:
            if prod_inv['nombre'] == item_pedido['nombre']:
                prod_inv['stock'] -= item_pedido['cantidad']
    
    # 3. GUARDAR EL PEDIDO
    total_pedido = sum(item['subtotal'] for item in items_solicitados)
    
    if mesa_destino:
        # Si lo pidió el staff para una mesa, lo guardamos en la mesa y NO en administración todavía
        if mesa_destino not in mesas_abiertas:
            mesas_abiertas[mesa_destino] = {"items": [], "total": 0}
            
        mesas_abiertas[mesa_destino]['items'].extend(items_solicitados)
        mesas_abiertas[mesa_destino]['total'] += total_pedido
        return jsonify({"status": "ok", "mensaje": "Añadido a la mesa"})
    else:
        # Si es pedido normal online, va directo a Administración
        nuevo_pedido = {
            "id": str(uuid.uuid4())[:8],
            "cliente": data.get('cliente', 'Cliente Online'),
            "telefono": data.get('telefono', ''),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": items_solicitados,
            "total": total_pedido
        }
        pedidos = leer_pedidos()
        pedidos.append(nuevo_pedido)
        guardar_pedidos(pedidos)
        return jsonify({"status": "ok", "id": nuevo_pedido['id']})

# ==========================================
# INICIO DEL SERVIDOR
# ==========================================
if __name__ == '__main__':
    # Flask correrá en el puerto 5000 por defecto (http://localhost:5000)
    app.run(host='0.0.0.0', port=5000, debug=True)
