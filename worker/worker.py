from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/', methods=['GET'])
def handle_post():
    print("DWORKER:\tGot get request", flush=True)

    login = request.args.get('login')
    password = request.args.get('password')
    print(f"WORKER:\tGot login = '{login}'", flush=True)

    url = f'http://database:8080/?login={login}'
    # curl "http://172.18.0.2:8080?login=Hilda&password=123"
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

if __name__=='__main__':

    print("WORKER:\tStarting server...")
    app.run(debug=False, host="0.0.0.0", port=8080)

    # found = get_user_by_login("Hilda")
    # for user in found:
    #     print(f"MAIN:\t{user}")
    