from quart import Quart, render_template, request, redirect, url_for
import aiohttp
import asyncio
import pika
import json
import uuid
import time
time.sleep(10)

app = Quart(__name__)

# URL сервера-обработчика "worker"
WORKER_URL = "http://worker:8080/"

# Настройки RabbitMQ
RABBITMQ_HOST = 'rabbitmq'  # Имя RabbitMQ-контейнера из docker-compose.yml
QUEUE_NAME = 'task_queue'


class RpcClient(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                heartbeat=1800
            ))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, username, password):
        self.response = None
        self.corr_id = str(uuid.uuid4())  # Уникальный идентификатор запроса
        self.channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,  # Очередь запросов
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,  # Указываем очередь для ответа
                correlation_id=self.corr_id,
            ),
            body=f"{username},{password}"
        )
        while self.response is None:
            self.connection.process_data_events(time_limit=None)  # Ожидаем ответа
        print("WEB |\tGot response:\t", str(self.response.decode()), flush=True)
        return self.response.decode()

@app.route('/')
async def index():
    return await render_template('login.html')  # Асинхронный рендеринг страницы

@app.route('/login', methods=['POST'])
async def login():
    form_data = await request.form
    login = form_data['login']
    password = form_data['password']
    
    response = rpc_client.call(login, password)  # Отправляем запрос
    try:
        code, user_id = response.split(",")
    except:
        code = "Unknown_code"
        User_id = None

    if code == "yes":
        # Перенаправляем на домашнюю страницу пользователя
        print(f"WEB:\tuser id = {user_id}")
        return redirect(url_for('home', username=login))
    else:
        # Возвращаем страницу входа с сообщением об ошибке
        return await render_template('login.html', error="Invalid username or password")


@app.route('/home/<username>')
async def home(username):
    # Рендерим персонализированную домашнюю страницу
    return await render_template('home.html', username=username)

@app.route('/logout')
async def logout():
    return redirect(url_for('/'))

if __name__ == '__main__':
    rpc_client = RpcClient()
    # Запускаем Quart-сервер
    print("WEB:\tStarting server...", flush=True)
    app.run(host='0.0.0.0', port=5000)
