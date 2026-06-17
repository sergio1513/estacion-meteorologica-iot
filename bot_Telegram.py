import json
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# -------------------------
# Configuración del Bot de Telegram
# -------------------------
# Token único del bot obtenido del BotFather
TELEGRAM_TOKEN = "8826538937:AAGrzu82ijULKZ4v7UX7mTc9nWP2_8wK81M"

# -------------------------
# Configuración del Broker MQTT
# -------------------------
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "idc/proyecto/sergio/datos"

# Estructura global para almacenar la última lectura recibida de los sensores
ultimo_dato = {
    "temperatura": None,
    "humedad": None,
    "luz": None,
    "co2_mq135": None,
    "alerta_luz_baja": None,
    "alerta_co2": None,
    "estado": "SIN DATOS"
}

# -------------------------
# Retrollamadas (Callbacks) de MQTT
# -------------------------
# Se ejecuta cuando el cliente se conecta exitosamente al broker MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado a MQTT con código:", rc)
    client.subscribe(MQTT_TOPIC)
    print("Suscrito a:", MQTT_TOPIC)

# Se ejecuta cuando se recibe un nuevo mensaje en el tópico suscrito
def on_message(client, userdata, msg):
    global ultimo_dato
    try:
        payload = msg.payload.decode()
        ultimo_dato = json.loads(payload)
        print("Dato recibido:", ultimo_dato)
    except Exception as e:
        print("Error leyendo MQTT:", e)

# -------------------------
# Comandos del Bot de Telegram
# -------------------------

# Comando /start: Da la bienvenida al usuario y lista los comandos disponibles
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "Hola, soy el bot de la estación meteorológica IoT.\n\n"
        "Comandos disponibles:\n"
        "/temperatura\n"
        "/humedad\n"
        "/luz\n"
        "/co2\n"
        "/estado\n"
        "/todo"
    )
    await update.message.reply_text(texto)

# Comando /temperatura: Muestra la lectura actual de temperatura
async def temperatura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Temperatura: {ultimo_dato.get('temperatura')} ºC"
    )

# Comando /humedad: Muestra la lectura actual de humedad relativa
async def humedad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Humedad: {ultimo_dato.get('humedad')} %"
    )

# Comando /luz: Muestra el valor de luminosidad y su estado (normal/bajo)
async def luz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = ultimo_dato.get("luz")
    alerta = ultimo_dato.get("alerta_luz_baja")

    if alerta:
        texto_alerta = "Luz baja detectada"
    else:
        texto_alerta = "Luz normal"

    await update.message.reply_text(
        f"Luz: {valor}\nEstado: {texto_alerta}"
    )

# Comando /co2: Muestra el nivel de CO2 y si el aire está limpio o cargado
async def co2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = ultimo_dato.get("co2_mq135")
    alerta = ultimo_dato.get("alerta_co2")

    if alerta:
        texto_alerta = "Aire cargado / CO2 alto"
    else:
        texto_alerta = "Aire normal"

    await update.message.reply_text(
        f"CO2/MQ135: {valor}\nEstado: {texto_alerta}"
    )

# Comando /estado: Muestra si el ambiente general está en estado NORMAL o ALERTA
async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Estado general: {ultimo_dato.get('estado')}"
    )

# Comando /todo: Envía un resumen completo con el valor de todos los sensores y alertas
async def todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        f"Temperatura: {ultimo_dato.get('temperatura')} ºC\n"
        f"Humedad: {ultimo_dato.get('humedad')} %\n"
        f"Luz: {ultimo_dato.get('luz')}\n"
        f"CO2/MQ135: {ultimo_dato.get('co2_mq135')}\n"
        f"Alerta luz baja: {ultimo_dato.get('alerta_luz_baja')}\n"
        f"Alerta CO2: {ultimo_dato.get('alerta_co2')}\n"
        f"Estado: {ultimo_dato.get('estado')}"
    )
    await update.message.reply_text(texto)

# -------------------------
# Función Principal y Ejecución
# -------------------------
def main():
    # Inicializar y conectar el cliente MQTT
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.loop_start()

    # Construir la aplicación del bot de Telegram
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Registrar los manejadores para cada comando
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("temperatura", temperatura))
    app.add_handler(CommandHandler("humedad", humedad))
    app.add_handler(CommandHandler("luz", luz))
    app.add_handler(CommandHandler("co2", co2))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("todo", todo))

    print("Bot iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()

