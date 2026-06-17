import network
import time
from machine import Pin, ADC, PWM
import dht
from umqtt.simple import MQTTClient

try:
    import ujson as json
except:
    import json

ssid = "REDWIFI_uXyf"
password = "GP3UFNDUZ5x9uUQ5"

mqtt_server = "broker.hivemq.com"
client_id = "pico_sergio_proyecto"
topic_pub = b"idc/proyecto/sergio/datos"

dht_sensor = dht.DHT11(Pin(15))
ldr_sensor = ADC(Pin(26))
co2_sensor = ADC(Pin(27))

buzzer = Pin(16, Pin.OUT)
servo = PWM(Pin(14))
servo.freq(50)

led_luz = Pin(17, Pin.OUT)

UMBRAL_HUMEDAD = 70
UMBRAL_LUZ_BAJA = 20000
UMBRAL_CO2 = 12000

def mover_servo(angulo):
    min_duty = 1638
    max_duty = 8192
    duty = int(min_duty + (angulo / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        print("Conectando WiFi...")
        time.sleep(1)

    print("WiFi conectado")
    print(wlan.ifconfig())

def conectar_mqtt():
    client = MQTTClient(client_id, mqtt_server)
    client.connect()
    print("Conectado al broker MQTT")
    return client

def pitar_buzzer_3s():
    buzzer.value(1)
    time.sleep(3)
    buzzer.value(0)

buzzer.value(0)
led_luz.value(0)
mover_servo(0)

conectar_wifi()
client = conectar_mqtt()

alarma_humedad_ya_sonada = False

try:
    while True:
        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            hum = dht_sensor.humidity()

            luz = ldr_sensor.read_u16()
            co2 = co2_sensor.read_u16()

            print("Temperatura:", temp, "ºC")
            print("Humedad:", hum, "%")
            print("Luz:", luz)
            print("CO2/MQ135:", co2)

            alerta_humedad = hum > UMBRAL_HUMEDAD
            alerta_luz_baja = luz < UMBRAL_LUZ_BAJA
            alerta_co2 = co2 > UMBRAL_CO2

            if alerta_humedad and not alarma_humedad_ya_sonada:
                print("ALERTA: humedad alta - buzzer 3 segundos")
                pitar_buzzer_3s()
                alarma_humedad_ya_sonada = True

            elif not alerta_humedad:
                buzzer.value(0)
                alarma_humedad_ya_sonada = False

            if alerta_co2:
                print("ALERTA: aire cargado / CO2 alto")
                mover_servo(90)
            else:
                mover_servo(0)

            if alerta_luz_baja:
                print("Aviso: poca luz")
                led_luz.value(1)
            else:
                led_luz.value(0)

            if alerta_humedad or alerta_luz_baja or alerta_co2:
                estado = "ALERTA"
            else:
                estado = "NORMAL"

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

            mensaje = json.dumps(datos)
            client.publish(topic_pub, mensaje)

            print("Publicado MQTT:", mensaje)
            print("----------------------")

        except Exception as e:
            print("Error leyendo sensores o publicando:", e)
            buzzer.value(0)
            led_luz.value(0)
            mover_servo(0)

        time.sleep(5)

except KeyboardInterrupt:
    buzzer.value(0)
    led_luz.value(0)
    mover_servo(0)
    print("Programa parado")