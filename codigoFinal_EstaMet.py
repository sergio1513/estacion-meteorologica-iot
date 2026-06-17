import network
import time
from machine import Pin, ADC, PWM
import dht
from umqtt.simple import MQTTClient

# Intentar importar la librería ujson optimizada para MicroPython
try:
    import ujson as json
except:
    import json

# Configuración de la red Wi-Fi
ssid = "REDWIFI_uXyf"
password = "GP3UFNDUZ5x9uUQ5"

# Configuración del servidor MQTT
mqtt_server = "broker.hivemq.com"
client_id = "pico_sergio_proyecto"
topic_pub = b"idc/proyecto/sergio/datos"

# Inicialización de sensores
dht_sensor = dht.DHT11(Pin(15)) # Sensor de temperatura y humedad DHT11 en GP15
ldr_sensor = ADC(Pin(26))      # LDR (Sensor de luz) en GP26 (ADC0)
co2_sensor = ADC(Pin(27))      # MQ135 (Sensor de calidad de aire/CO2) en GP27 (ADC1)

# Inicialización de actuadores
buzzer = Pin(16, Pin.OUT)      # Zumbador piezoeléctrico en GP16
servo = PWM(Pin(14))           # Servomotor SG90 en GP14
servo.freq(50)                 # Frecuencia del servo a 50Hz para control PWM

led_luz = Pin(17, Pin.OUT)     # LED indicador de luz baja en GP17

# Umbrales de alerta predefinidos
UMBRAL_HUMEDAD = 70
UMBRAL_LUZ_BAJA = 20000
UMBRAL_CO2 = 12000

# Función para controlar el ángulo del servomotor
def mover_servo(angulo):
    min_duty = 1638 # Duty cycle para 0 grados
    max_duty = 8192 # Duty cycle para 180 grados
    duty = int(min_duty + (angulo / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

# Función para realizar la conexión a la red Wi-Fi
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        print("Conectando WiFi...")
        time.sleep(1)

    print("WiFi conectado")
    print(wlan.ifconfig())

# Función para conectar con el broker MQTT
def conectar_mqtt():
    client = MQTTClient(client_id, mqtt_server)
    client.connect()
    print("Conectado al broker MQTT")
    return client

# Función para hacer sonar el zumbador durante 3 segundos
def pitar_buzzer_3s():
    buzzer.value(1)
    time.sleep(3)
    buzzer.value(0)

# Inicialización del estado de los actuadores
buzzer.value(0)
led_luz.value(0)
mover_servo(0)

# Conexión inicial
conectar_wifi()
client = conectar_mqtt()

# Bandera para evitar que el buzzer pite continuamente si se mantiene la humedad alta
alarma_humedad_ya_sonada = False

# Bucle principal de lectura y control
try:
    while True:
        try:
            # Medir temperatura y humedad
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            hum = dht_sensor.humidity()

            # Leer sensores analógicos (luz y calidad del aire)
            luz = ldr_sensor.read_u16()
            co2 = co2_sensor.read_u16()

            # Mostrar lecturas en consola local
            print("Temperatura:", temp, "ºC")
            print("Humedad:", hum, "%")
            print("Luz:", luz)
            print("CO2/MQ135:", co2)

            # Comprobar si se superan los umbrales de alerta
            alerta_humedad = hum > UMBRAL_HUMEDAD
            alerta_luz_baja = luz < UMBRAL_LUZ_BAJA
            alerta_co2 = co2 > UMBRAL_CO2

            # Control de la alerta de humedad (Buzzer)
            if alerta_humedad and not alarma_humedad_ya_sonada:
                print("ALERTA: humedad alta - buzzer 3 segundos")
                pitar_buzzer_3s()
                alarma_humedad_ya_sonada = True
            elif not alerta_humedad:
                buzzer.value(0)
                alarma_humedad_ya_sonada = False

            # Control de la alerta de calidad del aire (Servo)
            if alerta_co2:
                print("ALERTA: aire cargado / CO2 alto")
                mover_servo(90)
            else:
                mover_servo(0)

            # Control del LED de luz baja
            if alerta_luz_baja:
                print("Aviso: poca luz")
                led_luz.value(1)
            else:
                led_luz.value(0)

            # Determinar el estado general
            if alerta_humedad or alerta_luz_baja or alerta_co2:
                estado = "ALERTA"
            else:
                estado = "NORMAL"

            # Construir el objeto de datos en JSON
            datos = {
                "temperatura": temp,
                "humedad": hum,
                "luz": luz,
                "co2_mq135": co2,
                "alerta_humedad": alerta_humedad,
                "alerta_luz_baja": alerta_luz_baja,
                "alerta_co2": alerta_co2,
                "estado": estado
            }

            # Publicar el mensaje vía MQTT
            mensaje = json.dumps(datos)
            client.publish(topic_pub, mensaje)

            print("Publicado MQTT:", mensaje)
            print("----------------------")

        except Exception as e:
            print("Error leyendo sensores o publicando:", e)
            buzzer.value(0)
            led_luz.value(0)
            mover_servo(0)

        # Intervalo entre lecturas (5 segundos)
        time.sleep(5)

except KeyboardInterrupt:
    # Apagar y limpiar actuadores al interrumpir la ejecución
    buzzer.value(0)
    led_luz.value(0)
    mover_servo(0)
    print("Programa parado")