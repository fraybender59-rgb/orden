const express = require('express'); //[cite: 11]
const cors = require('cors'); //[cite: 11]
const app = express(); //[cite: 11]

// Middlewares necesarios para recibir datos JSON[cite: 11]
app.use(cors()); //[cite: 11]
// Aumentamos el límite a 50mb para permitir recibir imágenes en Base64 sin error
app.use(express.json({ limit: '50mb' })); 

// --- BASE DE DATOS EN MEMORIA ---[cite: 11]
// Menú base proporcionado para el proyecto #hamburguesas[cite: 11]
const menuProductos = {
  "Hamburguesas": [
    { nombre: "Clásica", precio: 60, imagen: "clasica.jpg", disponible: true }, //[cite: 11]
    { nombre: "Doble", precio: 80, imagen: "doble.jpeg", disponible: true } //[cite: 11]
  ],
  "Hot Dogs": [
    { nombre: "Hot Dog", precio: 30, imagen: "hot.jpg", disponible: true }, //[cite: 11]
    { nombre: "Orden de Hot Dogs", precio: 75, imagen: "Ordenhot.jpg", disponible: true } //[cite: 11]
  ],
  "Especialidades": [
    { nombre: "Enchiladas", precio: 75, imagen: "enchiladas.jpeg", disponible: true }, //[cite: 11]
    { nombre: "Chilaquiles", precio: 65, imagen: "chilaquiles.jpg", disponible: true }, //[cite: 11]
    { nombre: "Club Sandwich", precio: 85, imagen: "club.jpg", disponible: true }, //[cite: 11]
    { nombre: "Sincronizadas Mexa", precio: 85, imagen: "sincromexa.jpeg", disponible: true }, //[cite: 11]
    { nombre: "Crepa Pizza", precio: 90, imagen: "sincrop.webp", disponible: true } //[cite: 11]
  ],
  "Bebidas": [
    { nombre: "Refrescos Varios", precio: 25, imagen: "refrescosvarios.jpeg", disponible: true }, //[cite: 11]
    { nombre: "Coca Cola", precio: 25, imagen: "coca cola.jpeg", disponible: true } //[cite: 11]
  ]
}; //[cite: 11]

// Aquí se guardarán todos los pedidos que envíe el comandero/meseros[cite: 11]
let pedidosGlobales = []; //[cite: 11]

// Aquí se guardarán los comprobantes de pago enviados en Base64
let comprobantes = [];

// --- RUTAS DE LA API ---[cite: 11]

// 1. Obtener el menú (Lo usa Punto Staff 77 para cargar los botones)[cite: 11]
app.get('/api/menu', (req, res) => { //[cite: 11]
    res.json(menuProductos); //[cite: 11]
}); //[cite: 11]

// 2. Recibir un pedido nuevo desde Punto Staff 77 o Comandero[cite: 11]
app.post('/api/pedidos', (req, res) => { //[cite: 11]
    const nuevoPedido = req.body; //[cite: 11]
    
    // Le asignamos un ID único y la hora exacta del servidor[cite: 11]
    nuevoPedido.id = Date.now().toString(); //[cite: 11]
    if(!nuevoPedido.fecha) { //[cite: 11]
        nuevoPedido.fecha = new Date().toLocaleTimeString(); //[cite: 11]
    }
    
    // Lo guardamos en nuestra "base de datos" temporal[cite: 11]
    pedidosGlobales.push(nuevoPedido); //[cite: 11]
    
    console.log(`Nuevo pedido recibido de: ${nuevoPedido.mesero} para la ${nuevoPedido.cliente}`); //[cite: 11]
    res.status(201).json({ mensaje: "Pedido registrado con éxito", pedido: nuevoPedido }); //[cite: 11]
}); //[cite: 11]

// 3. Consultar todos los pedidos (Lo usa Control Jefe 99 y Administración)[cite: 11]
app.get('/api/pedidos', (req, res) => { //[cite: 11]
    // Enviamos la lista completa de pedidos[cite: 11]
    res.json(pedidosGlobales); //[cite: 11]
}); //[cite: 11]

// 4. Actualizar el estado de un pedido (Ej. De "Pendiente" a "Pagado" o "Entregado")[cite: 11]
app.put('/api/pedidos/:id', (req, res) => { //[cite: 11]
    const idPedido = req.params.id; //[cite: 11]
    const nuevoEstado = req.body.estado; //[cite: 11]
    
    let pedidoEncontrado = pedidosGlobales.find(p => p.id === idPedido); //[cite: 11]
    if (pedidoEncontrado) { //[cite: 11]
        pedidoEncontrado.estado = nuevoEstado; //[cite: 11]
        res.json({ mensaje: "Estado actualizado", pedido: pedidoEncontrado }); //[cite: 11]
    } else { //[cite: 11]
        res.status(404).json({ mensaje: "Pedido no encontrado" }); //[cite: 11]
    }
}); //[cite: 11]

// 5. Endpoint simulado de inventario (Para que Punto Staff no marque error 404)[cite: 11]
app.post('/api/inventario/restar', (req, res) => { //[cite: 11]
    // En el futuro aquí podemos conectar la lógica real del almacén[cite: 11]
    res.status(200).json({ mensaje: "Inventario notificado" }); //[cite: 11]
}); //[cite: 11]

// --- RUTAS PARA COMPROBANTES DE PAGO (NUEVO) ---
// Ruta para enviar los comprobantes al Control Maestro
app.get('/api/comprobantes', (req, res) => {
    res.json(comprobantes);
});

// Ruta para recibir la imagen desde el Comandero
app.post('/api/comprobantes', (req, res) => {
    const nuevoComprobante = req.body; 
    nuevoComprobante.id = Date.now();
    nuevoComprobante.fecha = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    comprobantes.push(nuevoComprobante);
    res.json({ mensaje: "Comprobante guardado con éxito", id: nuevoComprobante.id });
});

// Ruta para borrar foto (para el botón de "Borrar Foto" en el Control Maestro)
app.delete('/api/comprobantes/:id', (req, res) => {
    const id = req.params.id;
    comprobantes = comprobantes.filter(c => String(c.id) !== String(id));
    res.json({ mensaje: "Borrado" });
});

// --- CONFIGURACIÓN DEL SERVIDOR ---[cite: 11]
const PORT = process.env.PORT || 3000; //[cite: 11]
app.listen(PORT, () => { //[cite: 11]
    console.log(`Servidor del proyecto #hamburguesas corriendo en el puerto ${PORT}`); //[cite: 11]
}); //[cite: 11]

// EXPORTACIÓN OBLIGATORIA PARA VERCEL[cite: 11]
module.exports = app; //[cite: 11]
