# MANUAL DEL PROGRAMADOR
## Estación Meteorológica IoT para Confort Ambiental

---

## 1. Requisitos Previos

### 1.1 Software necesario

| Software | Versión | Uso |
|----------|---------|-----|
| Python 3.10+ | 3.10 o superior | Ejecutar el bot de Telegram |
| MicroPython | v1.22+ (RP2-W) | Firmware de la Raspberry Pi Pico W |
| Thonny IDE | 4.x | Programación y flasheo de la Pico W |
| Docker + Docker Compose | 24.x / 2.x | Despliegue del TIG Stack |

### 1.2 Dependencias Python (PC/Servidor del bot)

```bash
pip install paho-mqtt python-telegram-bot
```

### 1.3 Librerías MicroPython (Pico W)

Las librerías `dht`, `machine`, `network`, `time` y `json` vienen incluidas en el firmware estándar de MicroPython. Solo es necesario instalar `umqtt.simple`:

```
Thonny → Herramientas → Administrar paquetes → Buscar "micropython-umqtt.simple" → Instalar
```

---

## 2. Estructura del Proyecto

```
proyecto/
├── codigoFinal_EstaMet.py       # Firmware MicroPython para la Pico W
├── bot_Telegram.py              # Bot de Telegram (se ejecuta en PC/servidor)
├── docker-compose.yml           # Definición del TIG Stack
└── telegraf/
    └── telegraf.conf            # Configuración del agente Telegraf
```

---

## 3. Esquema de Conexiones Hardware

### 3.1 Tabla de pines GPIO

| Pin Pico W | Componente | Tipo | Función |
|------------|-----------|------|---------|
| GP15 | DHT11 | Sensor digital (1-Wire) | Temperatura (°C) y Humedad (%) |
| GP26 (ADC0) | LDR + R 10kΩ | Sensor analógico | Luminosidad ambiental (0–65535) |
| GP27 (ADC1) | MQ135 | Sensor analógico | Calidad del aire / CO₂ (0–65535) |
| GP16 | Buzzer piezoeléctrico | Actuador digital | Alerta sonora por humedad alta |
| GP17 | LED rojo + R 220Ω | Actuador digital | Indicador de luz baja |
| GP14 | Servo SG90 | Actuador PWM (50Hz) | Simulación apertura ventilación |

### 3.2 Circuito del divisor de tensión (LDR)

```
3.3V ──── LDR ────┬──── GP26 (ADC0)
                   │
              R 10kΩ
                   │
                  GND
```

### 3.3 Conexión del MQ135

```
5V ──── VCC (MQ135)
GND ─── GND (MQ135)
GP27 ── AOUT (MQ135)
```

---

## 4. Firmware de la Pico W (`codigoFinal_EstaMet.py`)

### 4.1 Parámetros configurables

Estos valores están al inicio del archivo y deben editarse según el entorno:

```python
ssid = "NOMBRE_DE_TU_RED"          # SSID Wi-Fi
password = "CONTRASEÑA"             # Contraseña Wi-Fi
mqtt_server = "broker.hivemq.com"   # Broker MQTT
client_id = "pico_sergio_proyecto"  # ID del cliente MQTT
topic_pub = b"idc/proyecto/sergio/datos"  # Tópico de publicación
```

### 4.2 Umbrales de alerta

```python
UMBRAL_HUMEDAD = 70       # % — Activa buzzer si se supera
UMBRAL_LUZ_BAJA = 20000   # ADC raw — Enciende LED si cae por debajo
UMBRAL_CO2 = 12000         # ADC raw — Mueve servo si se supera
```

### 4.3 Flujo de ejecución

1. Inicializa sensores y actuadores (estado seguro: todo apagado)
2. Conecta a Wi-Fi
3. Conecta al broker MQTT
4. Entra en bucle infinito (cada 5 segundos):
   - Lee DHT11, LDR y MQ135
   - Evalúa los 3 umbrales
   - Activa/desactiva actuadores según corresponda
   - Publica JSON por MQTT
5. En caso de error de lectura: apaga actuadores y continúa
6. `Ctrl+C` detiene el programa limpiamente

### 4.4 Lógica del buzzer

El buzzer suena 3 segundos la primera vez que la humedad supera el 70%. Un flag (`alarma_humedad_ya_sonada`) evita que vuelva a sonar mientras la humedad siga alta. Solo se resetea cuando la humedad baja del umbral, permitiendo una nueva alarma si vuelve a subir.

### 4.5 Formato del payload MQTT

```json
{
    "temperatura": 23,
    "humedad": 58,
    "luz": 42310,
    "co2_mq135": 8750,
    "alerta_humedad": false,
    "alerta_luz_baja": false,
    "alerta_co2": false,
    "estado": "NORMAL"
}
```

El campo `estado` vale `"ALERTA"` si algún umbral se supera, `"NORMAL"` si todos están dentro de rango.

---

## 5. Bot de Telegram (`bot_Telegram.py`)

### 5.1 Crear el bot con BotFather

1. Abrir Telegram y buscar `@BotFather`
2. Enviar `/newbot`
3. Elegir nombre y username
4. Copiar el token generado
5. Pegar el token en la variable `TELEGRAM_TOKEN` del archivo

### 5.2 Configuración

Editar las siguientes variables al inicio del archivo:

```python
TELEGRAM_TOKEN = "tu_token_aquí"
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "idc/proyecto/sergio/datos"
```

### 5.3 Comandos implementados

| Comando | Qué hace |
|---------|----------|
| `/start` | Muestra mensaje de bienvenida y lista de comandos |
| `/temperatura` | Devuelve la temperatura actual (°C) |
| `/humedad` | Devuelve la humedad actual (%) |
| `/luz` | Devuelve el nivel de luz y si es normal o baja |
| `/co2` | Devuelve el nivel de CO₂ y si es normal o alto |
| `/estado` | Devuelve el estado general: NORMAL o ALERTA |
| `/todo` | Devuelve un resumen completo de todos los sensores |

### 5.4 Ejecución

```bash
python bot_Telegram.py
```

El bot se conecta al broker MQTT, se suscribe al tópico y queda a la espera de comandos de Telegram. Cada vez que llega un mensaje MQTT, actualiza la variable `ultimo_dato`. Cuando el usuario envía un comando, responde con el último valor recibido.

---

## 6. TIG Stack (Docker)

### 6.1 `docker-compose.yml`

```yaml
version: '3.8'

services:
  mosquitto:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
    volumes:
      - mosquitto_data:/mosquitto/data
    networks:
      - iot_network

  telegraf:
    image: telegraf:latest
    volumes:
      - ./telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro
    depends_on:
      - mosquitto
      - influxdb
    networks:
      - iot_network

  influxdb:
    image: influxdb:1.8
    ports:
      - "8086:8086"
    environment:
      - INFLUXDB_DB=estacion_iot
      - INFLUXDB_ADMIN_USER=admin
      - INFLUXDB_ADMIN_PASSWORD=admin123
    volumes:
      - influxdb_data:/var/lib/influxdb
    networks:
      - iot_network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - influxdb
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - iot_network

volumes:
  mosquitto_data:
  influxdb_data:
  grafana_data:

networks:
  iot_network:
    driver: bridge
```

### 6.2 `telegraf/telegraf.conf`

```toml
[agent]
  interval = "5s"
  flush_interval = "5s"

[[inputs.mqtt_consumer]]
  servers = ["tcp://mosquitto:1883"]
  topics = ["idc/proyecto/sergio/datos"]
  data_format = "json"

[[outputs.influxdb]]
  urls = ["http://influxdb:8086"]
  database = "estacion_iot"
  username = "admin"
  password = "admin123"
```

### 6.3 Comandos de despliegue

```bash
docker-compose up -d         # Levantar todo
docker-compose ps            # Verificar estado
docker-compose logs -f telegraf  # Ver logs de Telegraf
docker-compose down          # Parar todo
```

### 6.4 Configurar Grafana

1. Acceder a `http://localhost:3000` (admin / admin)
2. Configuration → Data Sources → Add → InfluxDB
3. URL: `http://influxdb:8086`, Database: `estacion_iot`
4. Crear Dashboard con paneles de Time series y Gauge

---

## 7. Cómo Modificar el Sistema

### Añadir un nuevo sensor
1. Conectar al pin GPIO/ADC correspondiente
2. Declarar el pin en el firmware
3. Añadir la lectura en el bucle y al diccionario `datos`
4. Añadir un comando en el bot que lea el nuevo campo

### Cambiar umbrales
Editar las constantes `UMBRAL_HUMEDAD`, `UMBRAL_LUZ_BAJA` y `UMBRAL_CO2` al inicio del firmware.

### Cambiar la frecuencia de lectura
Modificar `time.sleep(5)` en el bucle principal del firmware (línea 139).

### Cambiar el broker MQTT
Editar `mqtt_server` en el firmware y `MQTT_BROKER` en el bot.
