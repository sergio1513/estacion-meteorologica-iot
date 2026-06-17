# ESTACIÓN METEOROLÓGICA IOT PARA CONFORT AMBIENTAL Y ALERTA DE RIESGO DE HUMEDAD

## MEMORIA TÉCNICA DE PROYECTO - IOT

**Alumnos**: Diego Torres Martín, Sergio Gadea Hierro

**Tecnologías**: Raspberry Pi Pico W, MicroPython, MQTT, TIG Stack (Telegraf, InfluxDB, Grafana), Telegram Bot, Docker

---

## 1. CONTEXTO Y OBJETIVOS DEL PROYECTO

### 1.1 Contexto e Introducción

En la actualidad, pasamos más del 80% de nuestro tiempo en espacios interiores (viviendas, oficinas, aulas), donde las condiciones ambientales influyen de manera directa sobre la salud, la productividad y el confort térmico. Un control deficiente de la climatización y la ventilación puede desencadenar patologías biológicas, entre las cuales destaca la proliferación de hongos y moho. La aparición de esporas de moho ocurre habitualmente en rincones con humedad relativa persistentemente elevada (>70%) y temperaturas templadas, afectando negativamente a personas con afecciones respiratorias, alergias o asma.

Este proyecto surge como una solución tecnológica enmarcada en el Internet de las Cosas (IoT). Utilizando hardware de bajo coste y alta eficiencia energética, se propone el diseño e implementación de un sistema sensorizado capaz de monitorizar las variables críticas del entorno doméstico y alertar al usuario ante escenarios de riesgo.

### 1.2 Objetivos del Proyecto

- **Monitorización Ambiental**: Adquirir periódicamente lecturas de temperatura, humedad relativa, nivel de luminosidad y calidad del aire en entornos de interior.
- **Alertas Locales Automáticas**: Activar actuadores físicos (buzzer, LED, servo) cuando los valores superen umbrales predefinidos.
- **Comunicación MQTT**: Implementar un protocolo de mensajería ligero sobre Wi-Fi para el envío periódico de los datos hacia un bróker centralizado.
- **Interfaz de Consulta (Telegram Bot)**: Proporcionar a los usuarios una vía de consulta remota que permita conocer el estado actual de los sensores desde el móvil.
- **Persistencia y Visualización (TIG Stack)**: Desplegar una infraestructura basada en contenedores Docker para almacenar el histórico de datos en InfluxDB y visualizar tendencias en Grafana.

---

## 2. METODOLOGÍA Y ARQUITECTURA DEL SISTEMA

Se ha seguido una metodología de desarrollo por bloques independientes: firmware del nodo sensor, despliegue de comunicaciones MQTT, programación del bot de Telegram, e integración del pipeline de datos con TIG Stack.

### 2.1 Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                     USUARIO FINAL                           │
│           Telegram (móvil)  │  Grafana (navegador)          │
└──────────────┬──────────────┼─────────────┬─────────────────┘
               │              │             │
     ┌─────────▼────────┐    │    ┌────────▼──────────────┐
     │  Bot Telegram     │    │    │  Grafana (Docker)     │
     │  (Python)         │    │    │  Dashboards           │
     └─────────┬────────┘    │    └────────▲──────────────┘
               │              │             │
               │ MQTT Sub     │        Consulta
               │              │             │
     ┌─────────▼──────────────▼─────────────┴──────────────┐
     │           Broker MQTT (HiveMQ público)               │
     └─────────▲────────────────────────────▲──────────────┘
               │ MQTT Pub                   │ MQTT Sub
               │                            │
     ┌─────────┴────────┐        ┌─────────┴──────────────┐
     │  Raspberry Pi     │        │  Telegraf (Docker)     │
     │  Pico W           │        │  Parsea JSON→InfluxDB  │
     │  (MicroPython)    │        └─────────┬──────────────┘
     │                   │                  │
     │ DHT11 LDR MQ135  │        ┌─────────▼──────────────┐
     │ Buzzer LED Servo  │        │  InfluxDB (Docker)     │
     └───────────────────┘        └────────────────────────┘
```

### 2.2 Especificación de Componentes

| Componente | Tipo | Función |
|-----------|------|---------|
| Raspberry Pi Pico W | Microcontrolador | Ejecuta el firmware MicroPython, lee sensores y publica datos vía MQTT sobre Wi-Fi. |
| Sensor DHT11 (GP15) | Sensor digital | Captura temperatura ambiente (°C) y humedad relativa (%). |
| LDR + Resistencia 10kΩ (GP26/ADC0) | Sensor analógico | Mide luminosidad ambiental mediante divisor de tensión (0–65535). |
| Sensor MQ135 (GP27/ADC1) | Sensor analógico | Detecta calidad del aire / concentración de CO₂ (0–65535). |
| LED rojo + Resistencia 220Ω (GP17) | Actuador | Se enciende cuando la luminosidad cae por debajo del umbral. |
| Buzzer piezoeléctrico (GP16) | Actuador | Suena 3 segundos cuando la humedad supera el 70%. Solo una vez por episodio. |
| Servo SG90 (GP14) | Actuador | Se posiciona a 90° cuando el CO₂ supera el umbral, simulando apertura de ventilación. Vuelve a 0° cuando baja. |

---

## 3. TRABAJO REALIZADO E IMPLEMENTACIÓN TÉCNICA

### 3.1 Firmware de la Pico W (`codigoFinal_EstaMet.py`)

El firmware sigue un bucle principal que cada 5 segundos:

1. Lee los tres sensores (DHT11, LDR, MQ135).
2. Evalúa tres umbrales de alerta:
   - **Humedad > 70%** → activa buzzer durante 3 segundos (solo la primera vez que se supera; no repite hasta que baje y vuelva a subir).
   - **Luz < 20000 (ADC)** → enciende LED indicador.
   - **CO₂ > 12000 (ADC)** → mueve servo a 90° (ventilación).
3. Clasifica el estado general como `"ALERTA"` si algún umbral se supera, o `"NORMAL"` si todos están dentro de rango.
4. Empaqueta todos los datos en un JSON y lo publica al tópico MQTT `idc/proyecto/sergio/datos`.

**Formato del payload JSON publicado:**

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

El bloque de lectura está envuelto en un `try-except` que, en caso de error, apaga todos los actuadores como medida de seguridad. El programa completo se puede detener con `Ctrl+C` (KeyboardInterrupt), lo cual también deja los actuadores en estado seguro.

### 3.2 Bot de Telegram (`bot_Telegram.py`)

El bot se ejecuta en un PC o servidor con Python. Se suscribe al mismo tópico MQTT que publica la Pico W y almacena siempre el último dato recibido. El usuario puede consultarlo mediante comandos de Telegram:

| Comando | Respuesta |
|---------|-----------|
| `/start` | Mensaje de bienvenida con la lista de comandos disponibles |
| `/temperatura` | Temperatura actual en °C |
| `/humedad` | Humedad relativa en % |
| `/luz` | Nivel de luz y estado (normal/baja) |
| `/co2` | Nivel de CO₂ y estado (normal/alto) |
| `/estado` | Estado general: NORMAL o ALERTA |
| `/todo` | Resumen completo de todos los sensores y alertas |

### 3.3 TIG Stack (Docker)

La infraestructura de visualización se despliega con Docker Compose y consta de tres servicios en una red bridge dedicada:

- **Telegraf**: Se suscribe al tópico MQTT `idc/proyecto/sergio/datos`, parsea el JSON y escribe los campos en InfluxDB.
- **InfluxDB**: Base de datos de series temporales que almacena el histórico de lecturas.
- **Grafana**: Consulta InfluxDB y presenta dashboards interactivos con gráficos de líneas temporales, medidores gauge y tablas de estado.

---

## 4. RESULTADOS OBTENIDOS

### 4.1 Monitorización en tiempo real

La estación publica correctamente cada 5 segundos los datos de los tres sensores al broker MQTT público (broker.hivemq.com). Los actuadores responden inmediatamente a las condiciones del entorno:

- El buzzer alerta una vez al superar la humedad del 70%, evitando repeticiones molestas gracias a un flag de control (`alarma_humedad_ya_sonada`).
- El LED se enciende/apaga dinámicamente según la luminosidad.
- El servo simula la apertura de ventilación cuando el CO₂ es alto y vuelve a su posición de reposo cuando se normaliza.

### 4.2 Consulta remota vía Telegram

El bot responde a los 7 comandos implementados, proporcionando al usuario las lecturas actuales sin necesidad de estar físicamente cerca de la estación.

### 4.3 Visualización histórica con Grafana

Los datos almacenados en InfluxDB permiten consultar gráficos de evolución temporal de temperatura, humedad, luminosidad y CO₂, así como identificar patrones a lo largo de horas y días.

---

## 5. PROBLEMAS ENCONTRADOS Y SOLUCIONES

| Problema | Solución |
|----------|----------|
| Lecturas erráticas del sensor DHT11 (errores ETIMEDOUT por sensibilidad del protocolo 1-Wire). | Se envolvió la lectura en un bloque `try-except` que, en caso de fallo, apaga los actuadores y continúa el bucle sin detener el sistema. |
| El buzzer sonaba repetidamente en cada iteración mientras la humedad estaba alta, resultando molesto. | Se implementó un flag booleano (`alarma_humedad_ya_sonada`) que limita la alarma a una sola activación por episodio. Solo se resetea cuando la humedad vuelve a bajar del umbral. |
| Conflictos de red entre contenedores Docker del TIG Stack. | Se definió una red Docker interna de tipo bridge dedicada en el `docker-compose.yml`, permitiendo la resolución de nombres DNS entre Telegraf, InfluxDB y Grafana. |
| El buzzer bloquea el bucle principal durante 3 segundos con `time.sleep(3)`. | Se asumió como limitación aceptable dado que el ciclo de lectura es de 5 segundos. En futuras versiones podría implementarse un buzzer no bloqueante basado en timestamps. |

---

## 6. CONCLUSIONES

La estación meteorológica IoT cumple con los objetivos planteados: monitoriza temperatura, humedad, luminosidad y calidad del aire, activa alertas locales automáticas, permite consulta remota por Telegram y almacena el histórico para visualización en Grafana.

El sistema demuestra que la Raspberry Pi Pico W es una plataforma adecuada para aplicaciones IoT de monitorización ambiental de bajo coste, y que la integración MQTT + TIG Stack + Telegram proporciona un flujo de datos completo desde el sensor hasta el usuario final.

### Posibles ampliaciones futuras

- Reconexión automática Wi-Fi y MQTT ante caídas de red.
- Filtrado digital de la señal del LDR (media móvil) para suavizar lecturas ruidosas.
- Cálculo de un índice de confort térmico basado en temperatura y humedad combinadas.
- Algoritmo de riesgo de moho que evalúe condiciones sostenidas en el tiempo.
- Buzzer no bloqueante para no interrumpir el ciclo de lectura.
- Comandos adicionales en el bot: historial de alertas, configuración remota de umbrales.
- Sustitución del DHT11 por BME280 (mayor precisión + presión atmosférica).
