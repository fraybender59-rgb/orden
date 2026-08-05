const express = require('express');
const cors = require('cors');
const app = express();

// Middlewares necesarios para recibir datos JSON
app.use(cors());
app.use(express.json());

// --- BASE DE DATOS EN MEMORIA ---
// Menú base proporcionado para el proyecto #hamburguesas
const menuProductos = {
  "Hamburguesas": [
    { nombre: "Clásica", precio: 60, imagen: "clasica.jpg", disponible: true },
    { nombre: "Doble", precio: 80, imagen: "doble.jpeg", disponible: true }
  ],
  "Hot Dogs": [
    { nombre: "Hot Dog", precio: 30, imagen: "hot.jpg", disponible: true },
    { nombre: "Orden de Hot Dogs", precio: 75, imagen: "Ordenhot.jpg", disponible: true }
  ],
  "Especialidades": [
    { nombre: "Enchiladas", precio: 75, imagen: "enchiladas.jpeg", disponible: true },
    { nombre: "Chilaquiles", precio: 65, imagen: "chilaquiles.jpg", disponible: true },
    { nombre: "Club Sandwich", precio: 85, imagen: "club.jpg", disponible: true },
    { nombre: "Sincronizadas Mexa", precio: 85, imagen: "sincromexa.jpeg", disponible: true },
    { nombre: "Crepa Pizza", precio: 90, imagen: "sincrop.webp", disponible: true }
  ],
  "Bebidas": [
    { nombre: "Refrescos Varios", precio: 25, imagen: "refrescosvarios.jpeg", disponible: true },
    { nombre: "Coca Cola", precio: 25, imagen: "coca cola.jpeg", disponible: true }
  ]
}; //[cite: 14]

// Aquí se guardarán todos los pedidos que envíe el comandero/meseros
let pedidosGlobales = []; 

// --- RUTAS DE LA API ---

// 1. Obtener el menú (Lo usa Punto Staff 77 para cargar los botones)
app.get('/api/menu', (req, res) => {
    res.json(menuProductos);
});

// 2. Recibir un pedido nuevo desde Punto Staff 77 o Comandero
app.post('/api/pedidos', (req, res) => {
    const nuevoPedido = req.body;
    
    // Le asignamos un ID único y la hora exacta del servidor
    nuevoPedido.id = Date.now().toString(); 
    if(!nuevoPedido.fecha) {
        nuevoPedido.fecha = new Date().toLocaleTimeString();
    }
    
    // Lo guardamos en nuestra "base de datos" temporal
    pedidosGlobales.push(nuevoPedido);
    
    console.log(`Nuevo pedido recibido de: ${nuevoPedido.mesero} para la ${nuevoPedido.cliente}`);
    res.status(201).json({ mensaje: "Pedido registrado con éxito", pedido: nuevoPedido });
});

// 3. Consultar todos los pedidos (Lo usa Control Jefe 99 y Administración)
app.get('/api/pedidos', (req, res) => {
    // Enviamos la lista completa de pedidos
    res.json(pedidosGlobales);
});

// 4. Actualizar el estado de un pedido (Ej. De "Pendiente" a "Pagado" o "Entregado")
app.put('/api/pedidos/:id', (req, res) => {
    const idPedido = req.params.id;
    const nuevoEstado = req.body.estado;
    
    let pedidoEncontrado = pedidosGlobales.find(p => p.id === idPedido);
    if (pedidoEncontrado) {
        pedidoEncontrado.estado = nuevoEstado;
        res.json({ mensaje: "Estado actualizado", pedido: pedidoEncontrado });
    } else {
        res.status(404).json({ mensaje: "Pedido no encontrado" });
    }
});

// 5. Endpoint simulado de inventario (Para que Punto Staff no marque error 404)
app.post('/api/inventario/restar', (req, res) => {
    // En el futuro aquí podemos conectar la lógica real del almacén
    res.status(200).json({ mensaje: "Inventario notificado" });
});

// --- CONFIGURACIÓN DEL SERVIDOR ---
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Servidor del proyecto #hamburguesas corriendo en el puerto ${PORT}`);
});

// EXPORTACIÓN OBLIGATORIA PARA VERCEL
module.exports = app;
