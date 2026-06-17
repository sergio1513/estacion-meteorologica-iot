import json
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# -------------------------
# Telegram
# -------------------------
TELEGRAM_TOKEN = "8826538937:AAGrzu82ijULKZ4v7UX7mTc9nWP2_8wK81M"

# -------------------------
# MQTT
# -------------------------
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "idc/proyecto/sergio/datos"

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
# MQTT callbacks
# -------------------------
def on_connect(client, userdata, flags, rc):
    print("Conectado a MQTT con código:", rc)
    client.subscribe(MQTT_TOPIC)
    print("Suscrito a:", MQTT_TOPIC)

def on_message(client, userdata, msg):
    global ultimo_dato
    try:
        payload = msg.payload.decode()
        ultimo_dato = json.loads(payload)
        print("Dato recibido:", ultimo_dato)
    except Exception as e:
        print("Error leyendo MQTT:", e)

# -------------------------
# Telegram commands
# -------------------------
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

async def temperatura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Temperatura: {ultimo_dato.get('temperatura')} ºC"
    )

async def humedad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Humedad: {ultimo_dato.get('humedad')} %"
    )

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

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Estado general: {ultimo_dato.get('estado')}"
    )

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
# Main
# -------------------------
def main():
    # MQTT
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.loop_start()

    # Telegram
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

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
