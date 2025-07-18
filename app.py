from flask import Flask, request, jsonify

app = Flask(__name__)

ultima_temperatura = None

@app.route("/update", methods=["POST"])
def recibir_temperatura():
    global ultima_temperatura
    data = request.json
    print("📩 Temperatura recibida:", data)

    if data and "temperatura" in data:
        ultima_temperatura = data["temperatura"]
        return jsonify({"status": "ok", "mensaje": "Temperatura recibida"}), 200
    else:
        return jsonify({"status": "error", "mensaje": "JSON inválido"}), 400

@app.route("/")
def home():
    if ultima_temperatura:
        return f"<h1>🌡️ Última temperatura: {ultima_temperatura}°C</h1>"
    return "<h1>Esperando datos...</h1>"

if __name__ == "__main__":
    app.run()
