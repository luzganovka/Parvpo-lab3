from quart import Quart, render_template, request
import aiohttp
import asyncio
import pika
import json

app = Quart(__name__)

# URL сервера-обработчика "worker"
WORKER_URL = "http://worker:8080/"

# Настройки RabbitMQ
# RABBITMQ_HOST = 'rabbitmq-container'  # Имя RabbitMQ-контейнера из docker-compose.yml
RABBITMQ_HOST = 'rabbitmq'  # Имя RabbitMQ-контейнера из docker-compose.yml
QUEUE_NAME = 'login_queue'


# Соединение с RabbitMQ
def send_to_rabbitmq(message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)  # Очередь устойчивая
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)  # Устойчивое сообщение
        )
        connection.close()
    except Exception as e:
        print(f"WEB |\tError sending message to RabbitMQ: {e}")
        raise e


@app.route('/')
async def index():
    return await render_template('login.html')  # Асинхронный рендеринг страницы

@app.route('/login', methods=['POST'])
async def login():
    form_data = await request.form
    login = form_data['login']
    password = form_data['password']
    
    message = {'login': login, 'password': password}

    try:
        send_to_rabbitmq(message)
        return "WEB |\tYour request has been queued successfully!", 200
    except Exception:
        return "WEB |\tFailed to queue your request. Please try again later.", 500


if __name__ == '__main__':
    # Запускаем Quart-сервер
    print("WEB:\tStarting server...", flush=True)
    app.run(host='0.0.0.0', port=5000)
