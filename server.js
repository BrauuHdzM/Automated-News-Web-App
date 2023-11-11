const express = require('express');
const bcrypt = require('bcrypt');
const mysql = require('mysql2/promise');
const bodyParser = require('body-parser');
const app = express();
const saltRounds = 10;

// Configuración de conexión a la base de datos
const dbConfig = {
  host: '127.0.0.1', // Sin el puerto aquí
  port: 3306,        // Puerto como un número, no como una cadena
  user: 'root',      // tu nombre de usuario de MySQL
  password: 'root',  // tu contraseña de MySQL
  database: 'tt'     // el nombre de tu base de datos
};

// Middleware para parsear el cuerpo de las solicitudes POST
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Directorio público para archivos estáticos (CSS, JS, imágenes, etc.)
// Asegúrate de que la carpeta 'assets' exista en la raíz de tu proyecto
app.use(express.static('assets'));

// Función para obtener una conexión a la base de datos
async function getDbConnection() {
  return await mysql.createConnection(dbConfig);
}

// Ruta de registro de usuarios
app.post('/register', async (req, res) => {
    try {
        const { nombre, email, usuario, password } = req.body;
        console.log({ nombre, email, usuario, password });
        
        if (!password || password.trim() === '') {
          // Envía un JSON con el error si la contraseña no se proporciona
          return res.status(400).json({ success: false, message: 'La contraseña es requerida.' });
        }
    
        const hashedPassword = await bcrypt.hash(password, saltRounds);
    

    const connection = await getDbConnection();
    const [result] = await connection.execute(
      'INSERT INTO Usuario (nombre, usuario, correo, contraseña) VALUES (?, ?, ?, ?)',
      [nombre, usuario, email, hashedPassword]
    );

    await connection.end();
    // Envía una respuesta de éxito con código de estado 201
    res.status(201).json({ success: true, message: 'Usuario registrado con éxito' });
  } catch (error) {
    console.error('Error al registrar el usuario: ', error);
    // Envía una respuesta de error con código de estado 500
    res.status(500).json({ success: false, message: 'Error al registrar el usuario' });
  }
});

// Ruta GET para servir la página de registro
app.get('/registrarse', (req, res) => {
  // Asegúrate de que el archivo 'registrarse.html' exista en la carpeta 'assets'
  res.sendFile(__dirname + '/registrarse.html');
});

// Ruta principal (opcional)
app.get('/', (req, res) => {
  res.sendFile(__dirname + '/main.html');
});

// Iniciar el servidor
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor corriendo en el puerto ${PORT}`);
});
