const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();

// Configuración de Middlewares
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Middleware para servir archivos estáticos (HTML e Imágenes)
app.use(express.static(__dirname));

// --- BASE DE DATOS EN MEMORIA ---
const menuProductos = {
  "Hamburguesas": [
    { nombre: "Clásica", precio: 60, imagen: "clasica.jpg", disponible: true },
    { nombre: "Doble", precio: 80, imagen: "doble.jpeg", disponible: true }
  ],
  "Hot Dogs": [
    { nombre: "Hot Dog", precio: 30, imagen: "hot.jpg", disponible: true },
    { nombre: "Orden de Hot Dogs", precio: 75, imagen: "Ordenhot.jpg", disponible: true }
  ]
};

let pedidosActivos = [];

// --- RUTAS DE LA API ---

// Obtener el menú completo
app.get('/api/menu', (req, res) => {
  res.json(menuProductos);
});

// Obtener todos los pedidos
app.get('/api/pedidos', (req, res) => {
  res.json(pedidosActivos);
});

// Crear un nuevo pedido (Ejemplo de lógica para el comandero)
app.post('/api/pedidos', (req, res) => {
  const nuevoPedido = {
    id: Date.now(),
    items: req.body.items || [],
    total: req.body.total || 0,
    estado: 'pendiente',
    fecha: new Date().toISOString()
  };
  pedidosActivos.push(nuevoPedido);
  res.status(201).json({ mensaje: 'Pedido registrado con éxito', pedido: nuevoPedido });
});

// Actualizar estado del pedido (Ejemplo para administración)
app.put('/api/pedidos/:id', (req, res) => {
  const idPedido = parseInt(req.params.id);
  const index = pedidosActivos.findIndex(p => p.id === idPedido);
  
  if (index !== -1) {
    pedidosActivos[index].estado = req.body.estado;
    res.json({ mensaje: 'Pedido actualizado', pedido: pedidosActivos[index] });
  } else {
    res.status(404).json({ error: 'Pedido no encontrado' });
  }
});

// --- EXPORTACIÓN PARA VERCEL ---
// Es vital exportar la app en lugar de solo dejarla escuchando, para evitar el error 404 en rutas dinámicas.
module.exports = app;

// Solo inicia el servidor localmente si lo corres desde tu terminal (ej: node app.js)
if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`Servidor del proyecto #hamburguesas activo en http://localhost:${PORT}`);
  });
}
