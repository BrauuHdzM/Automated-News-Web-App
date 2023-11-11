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
app.use(express.static('assets'));

// Función para obtener una conexión a la base de datos
async function getDbConnection() {
  return await mysql.createConnection(dbConfig);
}

// POST de registro de usuarios
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

// POST de inicio de sesión
app.post('/login', async (req, res) => {
  try {
      const { usuario, contrasena } = req.body;
      //const hashedPassword = await bcrypt.hash(contrasena, saltRounds);
      const connection = await getDbConnection();
      const [rows] = await connection.execute('SELECT contraseña FROM Usuario WHERE usuario = ?', [usuario]);

      if (rows.length > 0) {
          const validPassword = await bcrypt.compare(contrasena, rows[0].contraseña);
          if (validPassword) {
              res.json({ success: true, message: 'Ingreso exitoso.' });
          } else {
              res.json({ success: false, message: 'Usuario y/o contraseña incorrecta.' });
          }
      } else {
          res.json({ success: false, message: 'Usuario y/o contraseña incorrecta.' });
      }

      await connection.end();
  } catch (error) {
      console.error('Error al intentar iniciar sesión: ', error);
      res.status(500).json({ success: false, message: 'Error del servidor al intentar iniciar sesión.' });
  }
});


// Ruta de inicio de sesión
app.get('/login', async (req, res) => {
    res.sendFile(__dirname + '/login.html');
});

// Ruta de pagina principal de articulos
app.get('/articulos', async (req, res) => {
    res.sendFile(__dirname + '/articulos.html');
});

// Ruta para nuevo articulo
app.get('/nuevo-articulo', async (req, res) => {
    res.sendFile(__dirname + '/nuevo-articulo.html');
});

// Ruta para articulo-generado
app.get('/articulo-generado', async (req, res) => {
    res.sendFile(__dirname + '/articulo-generado.html');
});

// Ruta para articulos-encontrados
app.get('/articulos-encontrados', async (req, res) => {
    res.sendFile(__dirname + '/articulos-encontrados.html');
});

// Ruta para como-funciona
app.get('/como-funciona', async (req, res) => {
    res.sendFile(__dirname + '/como-funciona.html');
});

// Ruta para contacto
app.get('/contacto', async (req, res) => {
    res.sendFile(__dirname + '/contacto.html');
});

// Ruta para contrasena-olvidada
app.get('/contrasena-olvidada', async (req, res) => {
    res.sendFile(__dirname + '/contrasena-olvidada.html');
});

// Ruta para dato a modificar
app.get('/dato-modificar', async (req, res) => {
    res.sendFile(__dirname + '/dato-modificar.html');
});

// Ruta para eliminar-cuenta
app.get('/eliminar-cuenta', async (req, res) => {
    res.sendFile(__dirname + '/eliminar-cuenta.html');
});

// Ruta para calificacion
app.get('/calificacion', async (req, res) => {
    res.sendFile(__dirname + '/calificacion.html');
});

// Ruta GET para servir la página de registro
app.get('/registrarse', (req, res) => {
  // Asegúrate de que el archivo 'registrarse.html' exista en la carpeta 'assets'
  res.sendFile(__dirname + '/registrarse.html');
});

// Ruta principal 
app.get('/', (req, res) => {
  res.sendFile(__dirname + '/main.html');
});

// Iniciar el servidor
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor corriendo en el puerto ${PORT}`);
});
