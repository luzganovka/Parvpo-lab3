from quart import Quart, render_template, request
import aiohttp
import asyncio

app = Quart(__name__)

# URL сервера-обработчика "worker"
WORKER_URL = "http://worker:8080/"

@app.route('/')
async def index():
    return await render_template('login.html')  # Асинхронный рендеринг страницы

@app.route('/login', methods=['POST'])
async def login():
    login = (await request.form)['login']
    password = (await request.form)['password']
    
    async with aiohttp.ClientSession() as session:
        try:
            # Асинхронно отправляем POST-запрос на сервер "worker"
            async with session.post(WORKER_URL, json={'login': login, 'password': password}) as response:
                if response.status == 200:
                    result = await response.text()  # Получаем ответ от "worker"
                    return f"Login successful! Worker responded: {result}"
                else:
                    return f"Failed to process login on worker server. Status: {response.status}", 500
        except aiohttp.ClientError as e:
            return f"Error communicating with worker: {e}", 500

if __name__ == '__main__':
    # Запускаем Quart-сервер
    app.run(host='0.0.0.0', port=5000)
