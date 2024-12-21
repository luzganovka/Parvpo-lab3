const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const port = 8080;

// Middleware для парсинга данных формы
app.use(express.urlencoded({ extended: true }));

// Обслуживание статических файлов из папки public
app.use(express.static(path.join(__dirname, 'public')));

// Обработка GET-запроса на корень
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Обработка POST-запроса на вход
app.post('/login', (req, res) => {
  const { login, password } = req.body;
  
  // Проксирование запроса к Nginx
  const options = {
    target: 'http://nginx:80', // Укажите имя вашего контейнера Nginx
    changeOrigin: true,
    pathRewrite: {
      '^/login': '/login', // Измените путь, если необходимо
    },
  };
  
  createProxyMiddleware(options)(req, res);
});

// Запуск сервера
app.listen(port, () => {
  console.log("Server running at http://localhost:${port}/");
});
