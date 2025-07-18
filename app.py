import time
import threading
from flask import Flask, render_template_string
from datetime import datetime
import json

app = Flask(__name__)

# Variables globales
temperatura_actual = None
historial_temperaturas = []

def leer_temperatura_cpu():
    """Lee la temperatura del CPU"""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as archivo:
            temp_miligrados = int(archivo.read())
            temp_celsius = temp_miligrados / 1000.0
            return temp_celsius
    except:
        return None

def monitor_temperatura():
    """Función que corre en segundo plano monitoreando la temperatura"""
    global temperatura_actual, historial_temperaturas
    
    while True:
        try:
            temp = leer_temperatura_cpu()
            if temp is not None:
                temperatura_actual = temp
                hora = datetime.now().strftime("%H:%M:%S")
                
                # Agregar al historial
                historial_temperaturas.append({
                    'temp': round(temp, 2),
                    'hora': hora,
                    'timestamp': datetime.now()
                })
                
                # Mantener solo las últimas 50 lecturas
                if len(historial_temperaturas) > 50:
                    historial_temperaturas = historial_temperaturas[-50:]
                
                print(f"🌡️ Temperatura: {temp:.2f}°C")
            
            time.sleep(5)  # Leer cada 5 segundos
            
        except Exception as e:
            print(f"Error en monitor: {e}")
            time.sleep(10)

@app.route("/")
def index():
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌡️ Monitor Raspberry Pi</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="5">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                min-height: 100vh;
            }
            .container { 
                max-width: 900px; 
                margin: 0 auto; 
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 20px;
                backdrop-filter: blur(15px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            h1 { 
                text-align: center;
                font-size: 2.5em;
                margin-bottom: 30px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }
            .temp-display { 
                text-align: center;
                font-size: 4em;
                font-weight: bold;
                margin: 30px 0;
                padding: 20px;
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .status { 
                text-align: center; 
                margin: 20px 0;
                font-size: 1.3em;
            }
            .historial { 
                background: rgba(255,255,255,0.1); 
                padding: 20px; 
                border-radius: 15px;
                margin: 30px 0;
            }
            .historial h3 {
                margin-top: 0;
                color: #fff;
            }
            .temp-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid rgba(255,255,255,0.2);
            }
            .temp-item:last-child {
                border-bottom: none;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                font-size: 0.9em;
                opacity: 0.7;
            }
            .temp-color {
                {% if temperatura_actual %}
                    {% if temperatura_actual < 45 %}
                        color: #4CAF50;
                    {% elif temperatura_actual < 60 %}
                        color: #FFC107;
                    {% else %}
                        color: #F44336;
                    {% endif %}
                {% endif %}
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌡️ Monitor de Temperatura CPU</h1>
            
            <div class="temp-display temp-color">
                {% if temperatura_actual %}
                    {{ "%.2f"|format(temperatura_actual) }}°C
                {% else %}
                    --°C
                {% endif %}
            </div>
            
            <div class="status">
                {% if temperatura_actual %}
                    <span style="color: #4CAF50;">✅ Sistema funcionando</span>
                    <br>
                    <small>Actualizado: {{ datetime.now().strftime("%H:%M:%S") }}</small>
                {% else %}
                    <span style="color: #f44336;">❌ Sin datos</span>
                {% endif %}
            </div>
            
            <div class="historial">
                <h3>📊 Historial de Temperatura</h3>
                {% if historial_temperaturas %}
                    {% for temp in historial_temperaturas[-10:] %}
                        <div class="temp-item">
                            <span>{{ temp.hora }}</span>
                            <span>{{ temp.temp }}°C</span>
                        </div>
                    {% endfor %}
                {% else %}
                    <p>No hay datos disponibles</p>
                {% endif %}
            </div>
            
            <div class="footer">
                <p>🔄 Actualización automática cada 5 segundos</p>
                <p>📡 Servidor local Raspberry Pi</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, 
                                temperatura_actual=temperatura_actual,
                                historial_temperaturas=historial_temperaturas,
                                datetime=datetime)

@app.route("/api/temperatura")
def api_temperatura():
    """API simple para obtener la temperatura actual"""
    return {
        "temperatura": temperatura_actual,
        "timestamp": datetime.now().isoformat(),
        "status": "ok" if temperatura_actual else "sin_datos"
    }

if __name__ == "__main__":
    print("🚀 Iniciando servidor en Raspberry Pi...")
    print("🌐 Accede desde tu PC a: http://IP_DE_TU_RASPBERRY:5000")
    print("💡 Para encontrar tu IP: hostname -I")
    print("=" * 50)
    
    # Iniciar el monitor de temperatura en segundo plano
    monitor_thread = threading.Thread(target=monitor_temperatura, daemon=True)
    monitor_thread.start()
    
    # Iniciar el servidor web
    app.run(host="0.0.0.0", port=5000, debug=False)
