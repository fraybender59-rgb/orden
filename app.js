const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();

// Aumentamos el límite para que acepte las fotos de las transferencias sin problema
app.use(express.json({ limit: '50mb' }));
app.use(express.static(__dirname));

// Bases de datos locales
const dbPedidos = path.join(__dirname, 'pedidos.json');
const dbHistorial = path.join(__dirname, 'historial.json');

// Funciones para leer y guardar datos
function leerDB(archivo) {
    if (!fs.existsSync(archivo)) return [];
    return JSON.parse(fs.readFileSync(archivo, 'utf8'));
}

function guardarDB(archivo, datos) {
    fs.writeFileSync(archivo, JSON.stringify(datos, null, 2));
}

// 1. Obtener pedidos ACTIVOS (Para cocina y control jefe)
app.get('/api/pedidos', (req, res) => {
    res.json(leerDB(dbPedidos));
});

// 2. Obtener HISTORIAL DE VENTAS (Para control jefe)
app.get('/api/historial', (req, res) => {
    res.json(leerDB(dbHistorial));
});

// 3. Crear un nuevo pedido
app.post('/api/pedidos', (req, res) => {
    let pedidos = leerDB(dbPedidos);
    pedidos.push(req.body);
    guardarDB(dbPedidos, pedidos);
    res.json({ success: true });
});

// 4. Actualizar un pedido (Para cancelar platillos individuales, aplicar cortesías, etc.)
app.patch('/api/pedidos/:id', (req, res) => {
    let pedidos = leerDB(dbPedidos);
    let index = pedidos.findIndex(p => String(p.id) === String(req.params.id));
    
    if (index !== -1) {
        // Actualizamos los datos del pedido con lo que nos mande el frontend (items nuevos, nuevo total, estado)
        pedidos[index] = { ...pedidos[index], ...req.body };
        guardarDB(dbPedidos, pedidos);
        res.json({ success: true });
    } else {
        res.status(404).json({ error: "Pedido no encontrado" });
    }
});

// 5. ARCHIVAR pedido (Cobrar y Cerrar Mesa)
app.post('/api/pedidos/:id/archivar', (req, res) => {
    let pedidos = leerDB(dbPedidos);
    let index = pedidos.findIndex(p => String(p.id) === String(req.params.id));
    
    if (index !== -1) {
        // Sacamos el pedido de la lista activa
        let pedidoCerrado = pedidos.splice(index, 1)[0];
        
        // Le agregamos datos de cierre
        pedidoCerrado.estadoFinal = req.body.estado || 'Pagado';
        pedidoCerrado.fechaCierre = new Date().toLocaleString();
        
        // Lo guardamos en la bóveda del historial
        let historial = leerDB(dbHistorial);
        historial.push(pedidoCerrado);
        guardarDB(dbHistorial, historial);
        
        // Guardamos la lista activa ya sin esa mesa
        guardarDB(dbPedidos, pedidos);
        res.json({ success: true });
    } else {
        res.status(404).json({ error: "Pedido no encontrado" });
    }
});

// 6. Eliminar pedido (Borrado definitivo por error extremo)
app.delete('/api/pedidos/:id', (req, res) => {
    let pedidos = leerDB(dbPedidos);
    let filtrados = pedidos.filter(p => String(p.id) !== String(req.params.id));
    guardarDB(dbPedidos, filtrados);
    res.json({ success: true });
});

const PORT = 3000; // Puedes cambiar el puerto si usas otro
app.listen(PORT, () => {
    console.log(`Servidor de comandas corriendo y listo en el puerto ${PORT}`);
});
