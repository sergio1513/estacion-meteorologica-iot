# Estación Meteorológica IoT

Proyecto de Internet de las Cosas (IoT) para monitorización de confort ambiental y alerta de riesgo de humedad.

**Asignatura**: Ingeniería de Computadores (IDC)  
**Alumnos**: Diego Torres Martín, Sergio Gadea Hierro

## Descripción

Sistema IoT completo que monitoriza temperatura, humedad, luminosidad y calidad del aire en espacios interiores. Utiliza una Raspberry Pi Pico W con MicroPython como nodo sensor, MQTT para la comunicación, un bot de Telegram para consulta remota y el TIG Stack (Telegraf, InfluxDB, Grafana) para persistencia y visualización de datos.

## Arquitectura

```
Sensores (DHT11, LDR, MQ135)
        │
  Raspberry Pi Pico W (MicroPython)
        │
     Wi-Fi / MQTT
        │
   Broker MQTT (HiveMQ)
     ┌──┴──┐
     │     │
Bot Telegram   Telegraf → InfluxDB → Grafana
```

## Estructura del repositorio

| Archivo | Descripción |
|---------|-------------|
| `codigoFinal_EstaMet.py` | Firmware MicroPython para la Pico W |
| `bot_Telegram.py` | Bot de Telegram (Python) |
| `docker-compose.yml` | Despliegue del TIG Stack |
| `telegraf/telegraf.conf` | Configuración de Telegraf |

## Hardware utilizado

- Raspberry Pi Pico W
- Sensor DHT11 (temperatura y humedad)
- LDR + resistencia 10kΩ (luminosidad)
- Sensor MQ135 (calidad del aire)
- Buzzer piezoeléctrico
- LED rojo + resistencia 220Ω
- Servo SG90

## Tecnologías

MicroPython · MQTT · Docker · InfluxDB · Grafana · Telegraf · Python · Telegram Bot API
