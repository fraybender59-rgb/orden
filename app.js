const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();

// Middlewares
app.use(express.json({ limit: '10mb' })); // Límite ampliado para permitir imágenes en Base64
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(express.static(path.join(__dirname, 'public'))); // Asegúrate de tener tus HTML en una carpeta 'public'

const ARCHIVO_PEDIDOS = path.join(__dirname, 'pedidos.json');

// Función para leer pedidos
const leerPedidos = () => {
    try {
        if (!fs.existsSync(ARCHIVO_PEDIDOS)) return [];
        const data = fs.readFileSync(ARCHIVO_PEDIDOS, 'utf-8');
        return JSON.parse(data);
    } catch (error) {
        console.error('Error al leer pedidos:', error);
        return [];
    }
};

// Función para guardar pedidos
const guardarPedidos = (pedidos) => {
    try {
        fs.writeFileSync(ARCHIVO_PEDIDOS, JSON.stringify(pedidos, null, 2));
    } catch (error) {
        console.error('Error al guardar pedidos:', error);
    }
};

// --- RUTAS DE LA API ---

// Obtener todos los pedidos
app.get('/api/pedidos', (req, res) => {
    const pedidos = leerPedidos();
    res.json(pedidos);
});

// Crear un nuevo pedido
app.post('/api/pedidos', (req, res) => {
    const pedidos = leerPedidos();
    const nuevoPedido = {
        id: Date.now().toString(), // Genera un ID único basado en la fecha
        cliente: req.body.cliente || 'Sin Nombre',
        productos: req.body.productos || [],
        total: req.body.total || 0,
        estado: 'Pendiente',
        fecha: new Date().toISOString()
    };
    
    pedidos.push(nuevoPedido);
    guardarPedidos(pedidos);
    res.status(201).json({ status: 'success', pedido: nuevoPedido });
});

// Actualizar un pedido (Cobro, Estado, Comprobante y Origen)
app.patch('/api/pedidos/:id', (req, res) => {
    const pedidos = leerPedidos();
    const pedidoId = req.params.id;
    const index = pedidos.findIndex(p => String(p.id) === String(pedidoId));

    if (index !== -1) {
        // Actualiza los campos si vienen en la petición
        if (req.body.estado) pedidos[index].estado = req.body.estado;
        if (req.body.metodo) pedidos[index].metodo = req.body.metodo;
        if (req.body.origen) pedidos[index].origen = req.body.origen;
        if (req.body.comprobante_base64) pedidos[index].comprobante_base64 = req.body.comprobante_base64;

        guardarPedidos(pedidos);
        res.json({ status: 'success', pedido: pedidos[index] });
    } else {
        res.status(404).json({ status: 'error', message: 'Pedido no encontrado' });
    }
});

// Iniciar Servidor
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Servidor de #hamburguesas corriendo en el puerto ${PORT}`);
});

module.exports = app;
