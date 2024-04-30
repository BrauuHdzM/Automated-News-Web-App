const express = require('express');
const bcrypt = require('bcryptjs');
const mysql = require('mysql2/promise');
const bodyParser = require('body-parser');
const session = require('express-session');
const nodemailer = require('nodemailer'); 
const { spawn } = require('child_process');
require('dotenv').config();
const app = express();
const saltRounds = 10;

// Configuración de conexión a la base de datos
const dbConfig = {
  host: process.env.DB_HOST, 
  port: process.env.DB_PORT,        
  user: process.env.DB_USER,      
  password: process.env.DB_PASSWORD,  
  database: process.env.DB_DATABASE     
};

// Middleware para parsear el cuerpo de las solicitudes POST
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Directorio público para archivos estáticos (CSS, JS, imágenes, etc.)
app.use(express.static('assets'));

// Manejo de sesión
app.use(session({
  secret: 'tu_secreto_secreto', 
  resave: false,
  saveUninitialized: false,
  cookie: { secure: false } // Cambiar a 'true' si se usa HTTPS
}));

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: 'tt2024a013@gmail.com',
    pass: 'mkzh jjlx hgzc xuzv'
  },
  tls: {
    rejectUnauthorized: false // Ignora la verificación de SSL
  }
});

// Obtener una conexión a la base de datos
async function getDbConnection() {
  return await mysql.createConnection(dbConfig);
}

// Middleware de autenticación de sesión
function isAuthenticated(req, res, next) {
  if (req.session && req.session.userId) {
    return next(); 
  } else {
    return res.redirect('/login'); 
  }
}

// Actualizar datos del usuario
async function updateUserField(field, newValue, userId, connection) {
  let updateQuery = '';
  switch (field) {
      case 'nombre':
          updateQuery = 'UPDATE Usuario SET nombre = ? WHERE idUsuario = ?';
          break;
      case 'usuario':
          updateQuery = 'UPDATE Usuario SET usuario = ? WHERE idUsuario = ?';
          break;
      case 'contrasena':
          const hashedPassword = await bcrypt.hash(newValue, saltRounds);
          updateQuery = 'UPDATE Usuario SET contraseña = ? WHERE idUsuario = ?';
          newValue = hashedPassword;
          break;
      default:
          throw new Error('Campo para actualizar no reconocido');
  }
  
  const [result] = await connection.execute(updateQuery, [newValue, userId]);
  return result.affectedRows > 0;
}

// POST para registrar un nuevo usuario
app.post('/register', async (req, res) => {
    try {
      const { nombre, email, usuario, password } = req.body;
  
      // Verificar si el usuario o correo ya existen
      const connection = await getDbConnection();
      const [users] = await connection.execute('SELECT * FROM Usuario WHERE usuario = ? OR correo = ?', [usuario, email]);
      if (users.length > 0) {
        return res.status(400).json({ success: false, message: 'El usuario o correo ya existen.' });
      }
  
      // Verificar requisitos de la contraseña
      if (!password.match(/^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$/)) {
        return res.status(400).json({ success: false, message: 'La contraseña no cumple con los requisitos.' });
      }
      
      // Hashear la contraseña
      const hashedPassword = await bcrypt.hash(password, saltRounds);
  
      // Generar código de verificación
      const verificationCode = Math.floor(100000 + Math.random() * 900000); // Código de 6 dígitos
  
      // Guardar usuario en la base de datos con estado "no verificado" y el código de verificación
      await connection.execute(
        'INSERT INTO Usuario (nombre, usuario, correo, contraseña, codigoVerificacion, verificado, esAdmin) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [nombre, usuario, email, hashedPassword, verificationCode, 0, 0]
      );
  
      // Enviar correo con código de verificación
      const mailOptions = {
        from: 'tt2024a013@gmail.com',
        to: email,
        subject: 'Verificación de tu cuenta',
        text: `Tu nombre de usuario es: ${usuario}, y tu código de verificación es: ${verificationCode}`
      };
      
      transporter.sendMail(mailOptions, function(error, info){
        if (error) {
          console.log(error);
          res.status(500).json({ success: false, message: 'Error al enviar correo electrónico.' });
        } else {
          console.log('Correo enviado: ' + info.response);
          res.status(201).json({ success: true, message: 'Usuario registrado. Por favor, verifica tu correo electrónico.' });
        }
      });
  
    } catch (error) {
      console.error('Error al registrar el usuario: ', error);
      res.status(500).json({ success: false, message: 'Error al registrar el usuario' });
    }
  });

  // POST para verificar el usuario
  app.post('/verify', async (req, res) => {
    try {
      const { usuario, verificationCode } = req.body;
      const connection = await getDbConnection();
  
      // Verificar el código en la base de datos
      const [user] = await connection.execute('SELECT * FROM Usuario WHERE usuario = ? AND codigoVerificacion = ?', [usuario, verificationCode]);
  
      if (user.length === 0) {
        return res.status(400).json({ success: false, message: 'Código de verificación incorrecto o usuario no encontrado.' });
      }
  
      // Si el código es correcto, actualizar el estado del usuario a "verificado"
      await connection.execute('UPDATE Usuario SET verificado = 1 WHERE usuario = ?', [usuario]);
  
      res.status(200).json({ success: true, message: 'Cuenta verificada con éxito.' });
    } catch (error) {
      console.error('Error al verificar la cuenta: ', error);
      res.status(500).json({ success: false, message: 'Error al verificar la cuenta' });
    }
  });

// POST para solicitar recuperación de contraseña
app.post('/request-password-reset', async (req, res) => {
  const { email } = req.body;
  const connection = await getDbConnection();

  try {
    // Verifica si el usuario existe
    const [users] = await connection.execute('SELECT * FROM Usuario WHERE correo = ?', [email]);
    if (users.length === 0) {
      res.status(400).json({ success: false, message: 'Correo no encontrado.' });
      return;
    }

    // Generar token de restablecimiento de contraseña
    const resetToken = Math.floor(100000 + Math.random() * 900000);

    // Actualiza el token
    await connection.execute('UPDATE Usuario SET codigoVerificacion = ? WHERE correo = ?', [resetToken, email]);

    // Enviar correo con instrucciones y token
    const mailOptions = {
      from: 'tt2024a013@gmail.com',
      to: email,
      subject: 'Recuperación de contraseña',
      text: `Tu código de recuperación de contraseña es: ${resetToken}`
    };

    transporter.sendMail(mailOptions, function(error, info){
      if (error) {
        console.log(error);
        res.status(500).json({ success: false, message: 'Error al enviar correo electrónico.' });
      } else {
        console.log('Correo enviado: ' + info.response);
        res.status(201).json({ success: true, message: 'Usuario registrado. Por favor, verifica tu correo electrónico.' });
      }
    });

    res.json({ success: true, message: 'Correo de recuperación enviado.' });
  } catch (error) {
    console.error('Error al solicitar recuperación de contraseña: ', error);
    res.status(500).json({ success: false, message: 'Error del servidor.' });
  }
});
  
// POST para actualizar la contraseña
app.post('/reset-password', async (req, res) => {
  const { email, verificationCode, newPassword } = req.body;
  const connection = await getDbConnection();

  try {
    // Verificar código de verificación
    const [user] = await connection.execute(
      'SELECT * FROM Usuario WHERE correo = ? AND codigoVerificacion = ?',
      [email, verificationCode]
    );

    if (user.length === 0) {
      return res.status(400).json({ success: false, message: 'Datos inválidos.' });
    }

    // Verificar la fortaleza de la contraseña
    if (!newPassword.match(/^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$/)) {
      return res.status(400).json({ success: false, message: 'La contraseña no cumple con los requisitos.' });
    }

    // Actualizar contraseña
    const hashedPassword = await bcrypt.hash(newPassword, saltRounds);
    await connection.execute(
      'UPDATE Usuario SET contraseña = ? WHERE correo = ?',
      [hashedPassword, email]
    );

    res.json({ success: true, message: 'Contraseña actualizada con éxito.' });
  } catch (error) {
    console.error('Error al actualizar contraseña: ', error);
    res.status(500).json({ success: false, message: 'Error del servidor.' });
  }
});

// POST para iniciar sesión
app.post('/login', async (req, res) => {
  const { usuario, contrasena } = req.body;
  const connection = await getDbConnection();
  try {
      const [rows] = await connection.execute('SELECT idUsuario, contraseña, verificado, esAdmin FROM Usuario WHERE usuario = ?', [usuario]);
      if (rows.length > 0) {
          // Comprobar si la cuenta está verificada
          const validPassword = await bcrypt.compare(contrasena, rows[0].contraseña);
          if (validPassword) {
            if (rows[0].verificado == '1') {
              if (rows[0].esAdmin == '0') {
                req.session.userId = rows[0].idUsuario;
                res.json({ success: true, message: `Bienvenid@ ${usuario}`, isAdmin: false});
              }
              else {
                req.session.userId = rows[0].idUsuario;
                res.json({ success: true, message: `Bienvenid@ ${usuario}`, isAdmin: true});
              } 
            }
            else {
              res.json({ success: false, message: 'Cuenta no verificada. Por favor, verifica tu correo electrónico.' });
            }
          }
      } else {
          res.json({ success: false, message: 'Usuario y/o contraseña incorrecta.' });
      }
  } catch (error) {
      console.error('Error al intentar iniciar sesión: ', error);
      res.status(500).json({ success: false, message: 'Error del servidor al intentar iniciar sesión.' });
  } finally {
      if (connection) {
          await connection.end();
      }
  }
});

// Endpoint para cerrar sesión
app.get('/logout', (req, res) => {
  // Destruye la sesión y redirige al usuario a la página de inicio
  req.session.destroy(err => {
    if (err) {
      console.error('Error al cerrar sesión: ', err);
      res.status(500).send('No se pudo cerrar la sesión correctamente');
    } else {
      res.redirect('/'); // Redirige al usuario a la página de inicio
    }
  });
});

// POST para modificar los datos del usuario
app.post('/update-user', async (req, res) => {
  const { campoModificar, datoReemplazo, contrasena } = req.body;
  const userId = req.session.userId; // Obtener el ID del usuario desde la sesión
  const connection = await getDbConnection();
  try {
      // Verificar la contraseña actual antes de actualizar los datos
      const [rows] = await connection.execute('SELECT contraseña FROM Usuario WHERE idUsuario = ?', [userId]);
      if (rows.length > 0) {
          const validPassword = await bcrypt.compare(contrasena, rows[0].contraseña);
          if (!validPassword) {
              return res.json({ success: false, message: 'Contraseña actual incorrecta.' });
          }
          const updated = await updateUserField(campoModificar, datoReemplazo, userId, connection);
          if (updated) {
              res.json({ success: true, message: 'Se han actualizado los datos con éxito.' });
          } else {
              res.json({ success: false, message: 'No se pudo actualizar los datos.' });
          }
      } else {
          res.json({ success: false, message: 'Usuario no encontrado.' });
      }
  } catch (error) {
      console.error('Error al actualizar los datos del usuario: ', error);
      res.status(500).json({ success: false, message: 'Error del servidor al intentar actualizar.' });
  } finally {
      if (connection) {
          await connection.end();
      }
  }
});

// POST para eliminar la cuenta del usuario
app.post('/delete-account', async (req, res) => {
  const userId = req.session.userId; // Asume que el ID del usuario está en la sesión
  const { contrasena } = req.body;

  // Verifica que la contraseña se haya proporcionado
  if (!contrasena) {
      return res.status(400).json({ success: false, message: 'La contraseña es requerida.' });
  }

  const connection = await getDbConnection();

  try {
      // Busca al usuario en la base de datos y obtiene su contraseña hash
      const [user] = await connection.execute('SELECT contraseña FROM Usuario WHERE idUsuario = ?', [userId]);
      
      // Si no se encuentra un usuario o la contraseña hash está undefined, lanza un error
      if (user.length === 0 || !user[0].contraseña) {
          throw new Error('No se encontró el usuario o falta la contraseña hash.');
      }

      // Compara la contraseña ingresada con el hash almacenado
      const validPassword = await bcrypt.compare(contrasena, user[0].contraseña);
      if (!validPassword) {
          throw new Error('Contraseña incorrecta.');
      }

      // Elimina los registros relacionados con el usuario
      await connection.execute('DELETE FROM CalificacionNoticia WHERE idUsuario = ?', [userId])
      await connection.execute('DELETE FROM ArticuloNoticia WHERE idUsuario = ?', [userId]);

      // Elimina la cuenta del usuario
      await connection.execute('DELETE FROM Usuario WHERE idUsuario = ?', [userId]);
      
      // Cierra la sesión después de eliminar la cuenta
      if (req.session) {
          req.session.destroy();
      }

      res.json({ success: true, message: 'Se ha eliminado al usuario del sistema con éxito.' });
  } catch (error) {
      console.error('Error al eliminar la cuenta: ', error);
      res.status(500).json({ success: false, message: 'Contraseña incorrecta' });
  } finally {
      if (connection) {
          await connection.end();
      }
  }
});

// Ruta para obtener los artículos de un usuario específico
app.get('/mis-articulos', async (req, res) => {
  try {
    const idUsuario = req.session.userId;
    const connection = await getDbConnection();
    
    const [articulos] = await connection.query('SELECT * FROM ArticuloNoticia WHERE idUsuario = ?', [idUsuario]);

    // Devuelve los artículos en formato JSON
    res.json(articulos);

  } catch (error) {
    console.error('Error al obtener artículos:', error);
    res.status(500).send('Ocurrió un error al obtener los artículos');
  }
});

// API para recuperar el nombre de un usuario, utilizado en la barra de navegación
app.get('/api/recuperarNombre', async (req, res) => {
  const connection = await getDbConnection();
  const idUsuario = req.session.userId;
  const [rows] = await connection.execute('SELECT nombre FROM Usuario WHERE idUsuario = ?', [idUsuario]);
  if (rows.length > 0) {
      res.json({ nombre: rows[0].nombre });
  } else {
      res.status(404).json({ error: 'Usuario no encontrado' });
  }
});

// POST para solicitar la búsqueda de noticias
app.post('/encontrar-noticias', async (req, res) => {
  const { lugar, palabrasClave, fecha } = req.body;
  const consulta =`${lugar}, ${palabrasClave}`;

  try {
      const resultados = await buscarNoticias(consulta);
      req.session.resultadosNoticias = resultados;
      res.redirect('/articulos-encontrados');

  } catch (error) {
      console.error('Error al ejecutar script de Python: ', error);
      res.status(500).send('Error al procesar la solicitud');
  }
});

// POST para generar un artículo a partir de las noticias seleccionadas
app.post('/generar-noticias', async (req, res) => {
  const { noticiasSeleccionadas } = req.body;
  try {
      //console.log('Consultas recibidas: ', noticiasSeleccionadas);
      const articulo = await generarArticulo(JSON.stringify(noticiasSeleccionadas));
      req.session.articuloGenerado = articulo; 
      res.json({success: true, redirectUrl: '/articulo-generado'});
  } catch (error) {
      console.error('Error al ejecutar script de Python: ', error);
      res.status(500).json({success: false, message: 'Error al procesar la solicitud'});
  }
});

// Función para enviar consulta de buscar noticias a recuperaciónNoticias.py
function buscarNoticias(consulta) {
    return new Promise((resolve, reject) => {
        //console.log('Enviando consulta a Python:', consulta);
        const procesoPython = spawn('python', ['recuperacionNoticias.py', consulta]);
        let resultados = '';

        procesoPython.stdout.on('data', (data) => {
            resultados += data.toString();
        });

        procesoPython.on('close', (code) => {
            if (code !== 0) {
                return reject(`El script de Python finalizó con el código ${code}`);
            }
            try {
                const parsedData = JSON.parse(resultados);
                resolve(parsedData);
            } catch (error) {
                reject('Error al parsear la salida del script de Python: ' + error);
            }
        });
    });
}

// Función para enviar consulta de generación de artículo a generacionArticulo.py
function generarArticulo(consulta) {
  return new Promise((resolve, reject) => {
      console.log('Enviando consulta a Python:', consulta);
      const procesoPython = spawn('python', ['generacionArticulo.py']);

      procesoPython.stdin.write(consulta);
      procesoPython.stdin.end();

      let resultados = '';

      procesoPython.stdout.on('data', (data) => {
          resultados += data.toString();
      });

      procesoPython.on('close', (code) => {
          if (code !== 0) {
              console.error(`Error al ejecutar el script de Python: ${resultados}`);
              return reject(`El script de Python finalizó con el código ${code}`);
          } else {
              resolve(resultados);

          }
      });

      procesoPython.stderr.on('data', (data) => {
          console.error(`stderr: ${data}`);
      });
  });
}

// API para guardar un artículo en la base de datos
app.post('/api/guardarArticulo', async (req, res) => {
  const connection = await getDbConnection();
    try {
      const userId = req.session.userId;
      const { dataContenido, dataTitulo, dataFecha } = req.body; 
      const sql = `INSERT INTO ArticuloNoticia (idUsuario, titulo, contenido, fecha) VALUES (?, ?, ?, ?)`;
      const valores = [userId, dataTitulo, dataContenido, dataFecha];

      // Ejecutar consulta y recuperar el ID insertado
      const [result] = await connection.execute(sql, valores);
      const idArticulo = result.insertId; // Recuperar el ID del artículo insertado

      // Insertar calificaciones iniciales para el artículo
      const sql2 = `INSERT INTO CalificacionNoticia (idArticulo, idUsuario, calificacionTitulo, calificacionContenido, calificacionRedaccion) VALUES (?, ?, ?, ?, ?)`;
      const valores2 = [idArticulo, userId, 0, 0, 0];
      await connection.execute(sql2, valores2);
      res.json({ success: true, message: 'Artículo guardado correctamente', idarticulo: idArticulo});

} catch (error) {
      console.error('Error al guardar el artículo en la base de datos: ', error);
      res.status(500).json({ success: false, message: "Error al guardar el artículo en la base de datos", error: error.message });
}
});

// API para obtener un artículo generado
app.get('/api/articulo-generado', (req, res) => {
  if (req.session.articuloGenerado) {
    res.json({ articulo: req.session.articuloGenerado });
  } else {
    res.status(404).json({ error: 'No se encontró el artículo generado' });
  }
});

// Ruta para manejar las solicitudes de artículos individuales
app.get('/articulo/:idArticulo', async (req, res) => {
  const connection = await getDbConnection();
  const idArticulo = req.params.idArticulo;
  const userId = req.session.userId;

  try {
    const [rows, fields] = await connection.query('SELECT * FROM ArticuloNoticia WHERE idArticulo = ? AND idUsuario = ?', [idArticulo, userId]);
    const articulo = rows[0];
    
    if (!articulo) {
      res.status(404).send('Artículo no encontrado');
    } else {
      res.json(articulo);
    }
  } catch (error) {
    console.error('Error al obtener el artículo:', error);
    res.status(500).send('Error al obtener el artículo');
  }
});

// Ruta para eliminar un artículo específico
app.delete('/eliminarArticulo/:idArticulo', async (req, res) => {
  const connection = await getDbConnection();
  const { idArticulo } = req.params;

  try {
    const [result1] = await connection.query('DELETE FROM CalificacionNoticia WHERE idArticulo = ?', [idArticulo]);
    const [result2] = await connection.query('DELETE FROM ArticuloNoticia WHERE idArticulo = ?', [idArticulo]);
    
    if (result1.affectedRows === 0) {
      return res.status(404).json({ message: 'Calificaciones no encontradas o ya fueron eliminadas' });
    }

    if (result2.affectedRows === 0) {
      return res.status(404).json({ message: 'Artículo no encontrado o ya fue eliminado' });
    }

    res.json({ message: 'Artículo eliminado con éxito' });
  } catch (error) {
    console.error('Error al eliminar el artículo:', error);
    res.status(500).json({ message: 'Error al eliminar el artículo' });
  }
});

// Ruta para obtener las calificaciones de un artículo
app.get('/calificaciones/:idArticulo', async (req, res) => {
  const connection = await getDbConnection();
  const idArticulo = req.params.idArticulo;

  try {
    const rows = await connection.query('SELECT calificacionTitulo, calificacionContenido, calificacionRedaccion FROM CalificacionNoticia WHERE idArticulo = ?', [idArticulo]);
    res.json(rows);
  } catch (error) {
    console.error('Error al obtener las calificaciones:', error);
    res.status(500).send('Error al obtener las calificaciones');
  }
  });

// Ruta para actualizar las calificaciones de un artículo
app.put('/calificaciones/:idArticulo', async (req, res) => {
  const connection = await getDbConnection();
  const idArticulo = req.params.idArticulo;
  const { calificacionTitulo, calificacionContenido, calificacionRedaccion } = req.body;

  try {
    const [result] = await connection.query('UPDATE CalificacionNoticia SET calificacionTitulo = ?, calificacionContenido = ?, calificacionRedaccion = ? WHERE idArticulo = ?', [calificacionTitulo, calificacionContenido, calificacionRedaccion, idArticulo]);
    res.json({ message: 'Calificaciones actualizadas correctamente' });
  }
  catch (error) {
    console.error('Error al actualizar las calificaciones:', error);
    res.status(500).send('Error al actualizar las calificaciones');
  };
});

// API para obtener los resultados de la búsqueda de noticias
app.get('/api/resultados-noticias', (req, res) => {
  res.json(req.session.resultadosNoticias || []);
});

// Ruta para formulario de recuperar contraseña
app.get('/reset-password-form', async (req, res) => {
  res.sendFile(__dirname + '/nueva-contrasena.html');
});

// Ruta de inicio de sesión
app.get('/login', async (req, res) => {
    res.sendFile(__dirname + '/login.html');
});

// Ruta de pagina principal de articulos
app.get('/articulos', isAuthenticated, async (req, res) => {
    res.sendFile(__dirname + '/articulos.html');
});

// Ruta para nuevo articulo
app.get('/nuevo-articulo', isAuthenticated, async (req, res) => {
    res.sendFile(__dirname + '/nuevo-articulo.html');
});

// Ruta para articulo-generado
app.get('/articulo-generado', isAuthenticated, async (req, res) => {
    res.sendFile(__dirname + '/articulo-generado.html');
});

// Ruta para articulos-encontrados
app.get('/articulos-encontrados', isAuthenticated, async (req, res) => {
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
app.get('/dato-modificar', isAuthenticated, async (req, res) => {
    res.sendFile(__dirname + '/dato-modificar.html');
});

// Ruta para eliminar-cuenta
app.get('/eliminar-cuenta', isAuthenticated, async (req, res) => {
    res.sendFile(__dirname + '/eliminar-cuenta.html');
});

// Ruta para calificacion
app.get('/calificacion', isAuthenticated, async (req, res) => {
    res.sendFile(__dirname + '/calificacion.html');
});

// Ruta para administrador
app.get('/admin', isAuthenticated, async (req, res) => {
    res.sendFile(__dirname + '/administrador.html');
});

// Ruta GET para servir la página de registro
app.get('/registrarse', (req, res) => {
  // Asegúrate de que el archivo 'registrarse.html' exista en la carpeta 'assets'
  res.sendFile(__dirname + '/registrarse.html');
});

app.get('/articulo', (req, res) => {
  res.sendFile(__dirname + '/articulo.html');
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

