from quart import Quart, render_template, request
import pika
import json

app = Quart(__name__)

# Настройки RabbitMQ
RABBITMQ_HOST = 'rabbitmq-container'  # Имя контейнера RabbitMQ в вашей сети Docker
QUEUE_NAME = 'login_queue'

# Соединение с RabbitMQ
def send_to_rabbitmq(message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)  # Создаём очередь (если её нет)
        
        # Публикуем сообщение
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)  # Устанавливаем сообщение как "устойчивое"
        )
        connection.close()
        return True
    except Exception as e:
        print(f"Failed to send message to RabbitMQ: {e}")
        return False

@app.route('/')
async def index():
    return await render_template('login.html')  # Загружаем HTML-форму

@app.route('/login', methods=['POST'])
async def login():
    print("WEB |\tgot some /login request", flush = True)
    form_data = await request.form
    login = form_data['login']
    password = form_data['password']
    print(f"WEB |\tgot login = {login}", flush = True)
    print(f"WEB |\tgot password = {password}", flush = True)
    
    # Формируем сообщение
    message = {
        'login': login,
        'password': password
    }

    # Отправляем сообщение в RabbitMQ
    if send_to_rabbitmq(message):
        return "Your login request has been queued successfully!"
    else:
        return "Failed to queue your request. Please try again later.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
