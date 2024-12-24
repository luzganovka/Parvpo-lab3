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
            pika.ConnectionParameters(host=RABBITMQ_HOST))

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


# # Соединение с RabbitMQ
# def send_to_rabbitmq(message):
#     try:
#         connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
#         channel = connection.channel()
#         channel.queue_declare(queue=QUEUE_NAME, durable=True)  # Очередь устойчивая
#         channel.basic_publish(
#             exchange='',
#             routing_key=QUEUE_NAME,
#             body=json.dumps(message),
#             properties=pika.BasicProperties(delivery_mode=2)  # Устойчивое сообщение
#         )
#         connection.close()
#     except Exception as e:
#         print(f"WEB |\tError sending message to RabbitMQ: {e}")
#         raise e


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
    redirect(url_for('/login'))

    # try:
    #     result = rpc_client.call(username, password)  # Отправляем запрос
    #     return f"Login result: {result}"
    # except:
    #     return "WEB |\tError in rpc call!", 500

    # message = {'login': login, 'password': password}

    # try:
    #     send_to_rabbitmq(message)
    #     return "WEB |\tYour request has been queued successfully!", 200
    # except Exception:
    #     return "WEB |\tFailed to queue your request. Please try again later.", 500


if __name__ == '__main__':
    rpc_client = RpcClient()
    # Запускаем Quart-сервер
    print("WEB:\tStarting server...", flush=True)
    app.run(host='0.0.0.0', port=5000)
