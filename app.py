from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json

app = Flask(__name__)

# Almacenamiento de datos
temperaturas_historicas = []
ultima_temperatura = None

# Template HTML moderno con gráficos
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌡️ Monitor de Temperatura</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            align-items: start;
        }

        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
        }

        .temp-display {
            text-align: center;
            margin-bottom: 30px;
        }

        .temp-value {
            font-size: 4rem;
            font-weight: bold;
            margin: 20px 0;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
            transition: all 0.3s ease;
        }

        .temp-cold { color: #74b9ff; }
        .temp-normal { color: #00b894; }
        .temp-warm { color: #fdcb6e; }
        .temp-hot { color: #e84393; }

        .status-indicator {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }

        .status-online { background: #00b894; }
        .status-offline { background: #636e72; }

        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }

        .chart-container {
            position: relative;
            height: 400px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .stat-item {
            background: rgba(255, 255, 255, 0.08);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #74b9ff;
        }

        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 5px;
        }

        .last-update {
            font-size: 0.9rem;
            opacity: 0.7;
            text-align: center;
            margin-top: 15px;
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5rem;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
        }

        h2 {
            margin-bottom: 20px;
            font-size: 1.5rem;
            text-align: center;
        }

        .loading {
            text-align: center;
            font-size: 1.2rem;
            opacity: 0.8;
        }

        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .temp-value {
                font-size: 3rem;
            }
            
            h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <h1>🌡️ Monitor de Temperatura IoT</h1>
    
    <div class="container">
        <!-- Panel de temperatura actual -->
        <div class="card">
            <div class="temp-display">
                <div id="status">
                    <span class="status-indicator" id="statusIndicator"></span>
                    <span id="statusText">Conectando...</span>
                </div>
                <div class="temp-value" id="tempValue">--°C</div>
                <div class="last-update" id="lastUpdate">Esperando datos...</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="maxTemp">--°C</div>
                    <div class="stat-label">Máxima</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="minTemp">--°C</div>
                    <div class="stat-label">Mínima</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="avgTemp">--°C</div>
                    <div class="stat-label">Promedio</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="totalReadings">0</div>
                    <div class="stat-label">Lecturas</div>
                </div>
            </div>
        </div>

        <!-- Gráfico de temperatura -->
        <div class="card">
            <h2>📊 Historial de Temperatura</h2>
            <div class="chart-container">
                <canvas id="temperatureChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // Configuración del gráfico
        const ctx = document.getElementById('temperatureChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Temperatura (°C)',
                    data: [],
                    borderColor: '#74b9ff',
                    backgroundColor: 'rgba(116, 185, 255, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#74b9ff',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'white',
                            callback: function(value) {
                                return value + '°C';
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'white',
                            maxTicksLimit: 8
                        }
                    }
                },
                elements: {
                    point: {
                        hoverBackgroundColor: '#ffffff'
                    }
                }
            }
        });

        // Datos del servidor
        const historicalData = {{ datos_historicos|tojsonfilter }};
        const currentTemp = {{ temperatura_actual|tojsonfilter }};

        // Función para obtener color según temperatura
        function getTempColor(temp) {
            if (temp < 10) return 'temp-cold';
            if (temp < 25) return 'temp-normal';
            if (temp < 35) return 'temp-warm';
            return 'temp-hot';
        }

        // Función para formatear fecha
        function formatTime(dateString) {
            const date = new Date(dateString);
            return date.toLocaleTimeString('es-ES', { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
            });
        }

        // Actualizar interfaz
        function updateInterface() {
            const tempValue = document.getElementById('tempValue');
            const statusIndicator = document.getElementById('statusIndicator');
            const statusText = document.getElementById('statusText');
            const lastUpdate = document.getElementById('lastUpdate');

            if (currentTemp !== null) {
                tempValue.textContent = currentTemp + '°C';
                tempValue.className = 'temp-value ' + getTempColor(currentTemp);
                
                statusIndicator.className = 'status-indicator status-online';
                statusText.textContent = 'Conectado';
                
                if (historicalData.length > 0) {
                    const lastReading = historicalData[historicalData.length - 1];
                    lastUpdate.textContent = 'Última actualización: ' + formatTime(lastReading.timestamp);
                }
            } else {
                statusIndicator.className = 'status-indicator status-offline';
                statusText.textContent = 'Sin datos';
            }

            // Actualizar estadísticas
            if (historicalData.length > 0) {
                const temps = historicalData.map(d => d.temperatura);
                const maxTemp = Math.max(...temps);
                const minTemp = Math.min(...temps);
                const avgTemp = (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1);

                document.getElementById('maxTemp').textContent = maxTemp + '°C';
                document.getElementById('minTemp').textContent = minTemp + '°C';
                document.getElementById('avgTemp').textContent = avgTemp + '°C';
                document.getElementById('totalReadings').textContent = historicalData.length;
            }
        }

        // Actualizar gráfico
        function updateChart() {
            if (historicalData.length > 0) {
                const last20 = historicalData.slice(-20); // Mostrar últimas 20 lecturas
                
                chart.data.labels = last20.map(d => formatTime(d.timestamp));
                chart.data.datasets[0].data = last20.map(d => d.temperatura);
                
                chart.update('none');
            }
        }

        // Inicializar
        updateInterface();
        updateChart();

        // Auto-refresh cada 5 segundos
        setInterval(() => {
            location.reload();
        }, 5000);
    </script>
</body>
</html>
"""

@app.route("/update", methods=["POST"])
def recibir_temperatura():
    global ultima_temperatura, temperaturas_historicas
    data = request.json
    print("📩 Temperatura recibida:", data)
    
    if data and "temperatura" in data:
        temperatura = data["temperatura"]
        timestamp = datetime.now().isoformat()
        
        # Actualizar última temperatura
        ultima_temperatura = temperatura
        
        # Agregar al historial
        temperaturas_historicas.append({
            "temperatura": temperatura,
            "timestamp": timestamp
        })
        
        # Mantener solo las últimas 100 lecturas
        if len(temperaturas_historicas) > 100:
            temperaturas_historicas = temperaturas_historicas[-100:]
        
        return jsonify({
            "status": "ok", 
            "mensaje": "Temperatura recibida",
            "temperatura": temperatura,
            "timestamp": timestamp
        }), 200
    else:
        return jsonify({"status": "error", "mensaje": "JSON inválido"}), 400

@app.route("/")
def home():
    return render_template_string(
        HTML_TEMPLATE,
        datos_historicos=temperaturas_historicas,
        temperatura_actual=ultima_temperatura
    )

@app.route("/api/datos")
def obtener_datos():
    """Endpoint para obtener datos en formato JSON"""
    return jsonify({
        "temperatura_actual": ultima_temperatura,
        "historial": temperaturas_historicas,
        "estadisticas": {
            "total_lecturas": len(temperaturas_historicas),
            "temperatura_maxima": max([t["temperatura"] for t in temperaturas_historicas]) if temperaturas_historicas else None,
            "temperatura_minima": min([t["temperatura"] for t in temperaturas_historicas]) if temperaturas_historicas else None,
            "temperatura_promedio": sum([t["temperatura"] for t in temperaturas_historicas]) / len(temperaturas_historicas) if temperaturas_historicas else None
        }
    })

@app.route("/api/limpiar", methods=["POST"])
def limpiar_historial():
    """Endpoint para limpiar el historial de temperaturas"""
    global temperaturas_historicas
    temperaturas_historicas = []
    return jsonify({"status": "ok", "mensaje": "Historial limpiado"})

if __name__ == "__main__":
    print("🌡️ Monitor de Temperatura IoT iniciado")
    print("📱 Abre tu navegador en: http://localhost:5000")
    print("📡 Endpoint para datos: POST /update")
    print("🔄 Auto-refresh cada 5 segundos")
    app.run(debug=True, host='0.0.0.0', port=5000)
