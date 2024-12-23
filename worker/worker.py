from flask import Flask, request, jsonify
# import requests
import pika
import json

app = Flask(__name__)

# Настройки RabbitMQ
RABBITMQ_HOST = 'rabbitmq'  # Имя RabbitMQ-контейнера из docker-compose.yml
QUEUE_NAME = 'login_queue'

def ask_DB(login, password):
    url = f'http://database:8080/?login={login}'
    # curl "http://172.18.0.2:8080?login=Hilda&password=123"
    # curl --data "login=Hilda&password=123" http://172.18.0.2:8080
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        user_id = data.get("id")
        if password == data.get("password"):
            print(f"WORKER:\tWelcome!", flush=True)
            return jsonify({"message": "Welcome"}), 200
        else:
            print(f"WORKER:\tWrong login or password", flush=True)
            return jsonify({"message": "Wrong login or password"}), 200
    else:
        return jsonify({"message": "Error on connection between WORKER and DB"}), 500
    

# @app.route('/', methods=['POST'])
# def handle_post():
#     print("DWORKER:\tGot post request", flush=True)

#     data = request.get_json()
#     print("ADDER: Received data:", data['login'], flush=True)

#     login    = request.form.get('login')
#     password = request.form.get('password')
#     print(f"WORKER:\tGot login = '{login}'", flush=True)

#     return ask_DB(data['login'], data['password'])
    

# @app.route('/', methods=['GET'])
# def handle_get():
#     print("DWORKER:\tGot get request", flush=True)

#     login = request.args.get('login')
#     password = request.args.get('password')
#     print(f"WORKER:\tGot login = '{login}'", flush=True)

#     url = f'http://database:8080/?login={login}'
    
#     return ask_DB(login, password)


def process_message(ch, method, properties, body):
    message = json.loads(body)
    login = message['login']
    password = message['password']

    # Обработка запроса
    print(f"WORKER |\tProcessing login request: login={login}, password={password}", flush=True)

    # Подтверждение обработки сообщения
    ch.basic_ack(delivery_tag=method.delivery_tag)

    return ask_DB(login, password)


def main():
    credentials = pika.PlainCredentials('guest', 'guest')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=5672, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    print("WORKER:\tWorker is waiting for messages...", flush=True)
    channel.basic_consume(queue=QUEUE_NAME, auto_ack=True, on_message_callback=process_message)
    channel.start_consuming()


if __name__=='__main__':

    print("WORKER:\tStarting server...", flush=True)
    main()
    # app.run(debug=False, host="0.0.0.0", port=8080)

    # found = get_user_by_login("Hilda")
    # for user in found:
    #     print(f"MAIN:\t{user}")
    