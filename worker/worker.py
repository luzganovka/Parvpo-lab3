import requests
from requests.exceptions import HTTPError
import pika
import json
import time
time.sleep(15)

# Настройки RabbitMQ
RABBITMQ_HOST = 'rabbitmq'  # Имя RabbitMQ-контейнера из docker-compose.yml
QUEUE_NAME = 'task_queue'

def ask_DB(login, password):
        url = f'http://database:8080/?login={login}'
        try:
            response = requests.get(url)

            # если ответ успешен, исключения задействованы не будут
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'DB-query: HTTP error occurred: {http_err}')
        except Exception as err:
            print(f'DB-query: Other error occurred: {err}')
        else:
            print('DB-query: Success!')

        if response.status_code == 200:
            data = response.json()
            user_id = int(data.get("id"))
            if password == data.get("password"):
                print(f"WORKER:\tWelcome!", flush=True)
                return f"yes,{user_id}"
            else:
                print(f"WORKER:\tWrong login or password", flush=True)
                return f"no,{user_id}"


def on_request(ch, method, props, body):
    login, password = body.decode().split(',')
    print(f"WORKER |\tProcessing login request: login={login}, password={password}", flush=True)

    response = ask_DB(login, password)

    ch.basic_publish(exchange='',
                    routing_key=props.reply_to,  # Очередь, указанная веб-сервером
                    properties=pika.BasicProperties(
                        correlation_id = props.correlation_id   # Передаём обратно correlation_id
                    ),
                    body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)  # Подтверждаем обработку

def main():
    credentials = pika.PlainCredentials('guest', 'guest')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672, \
        credentials=credentials,
        heartbeat=1800
    ))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_request)

    print("WORKER:\tWorker is waiting for messages...", flush=True)
    channel.start_consuming()


if __name__=='__main__':

    print("WORKER:\tStarting server...", flush=True)
    main()