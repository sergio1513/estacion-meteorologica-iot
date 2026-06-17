# MANUAL DE USUARIO
## Estación Meteorológica IoT para Confort Ambiental

¡Bienvenido! Este manual le guiará para utilizar su Estación Meteorológica IoT, comprender las alertas y consultar los datos desde su teléfono móvil.

---

## 1. Instalación y Ubicación

Para garantizar lecturas precisas, coloque la estación siguiendo estas recomendaciones:

- **Lugar representativo**: Zona neutra de la habitación, a una altura de entre 1.2 y 1.5 metros del suelo.
- **Evite fuentes de calor/frío**: No la coloque sobre radiadores, bajo rejillas de aire acondicionado ni en contacto directo con la luz del sol.
- **Zonas con riesgo de humedad**: Si quiere vigilar aparición de moho, ubíquela cerca de paredes exteriores o esquinas propensas a condensación.
- **Alimentación**: Conecte el cable USB a cualquier cargador de móvil estándar (5V).

---

## 2. Indicadores Visuales y Sonoros (Hardware)

El dispositivo trabaja de forma autónoma. Estos son los indicadores que le avisarán de condiciones adversas:

| Indicador | Qué significa |
|-----------|---------------|
| **LED Rojo encendido** | La luminosidad de la estancia está por debajo del nivel recomendado. Encienda una luz o abra las cortinas. |
| **Alarma sonora (Buzzer)** | La humedad ha superado el 70%. Suena una vez durante 3 segundos como aviso. No vuelve a sonar hasta que la humedad baje y vuelva a subir. |
| **Servo se mueve** | La calidad del aire es deficiente (CO₂ alto). Simula la apertura de una rejilla de ventilación. Vuelve a su posición cuando el aire se normaliza. |

---

## 3. Uso del Bot de Telegram

La forma más sencilla de consultar su estación es mediante Telegram. Busque el nombre del bot y pulse **INICIAR**.

### Comandos Disponibles

| Comando | Qué le muestra |
|---------|----------------|
| `/start` | Mensaje de bienvenida y lista de todos los comandos |
| `/temperatura` | La temperatura actual en °C |
| `/humedad` | La humedad relativa actual en % |
| `/luz` | Nivel de luz y si es normal o baja |
| `/co2` | Nivel de CO₂ y si el aire es normal o está cargado |
| `/estado` | Estado general del ambiente: NORMAL o ALERTA |
| `/todo` | Resumen completo de todos los sensores y alertas |

### Ejemplo de uso

Envíe `/todo` y recibirá algo como:

```
Temperatura: 23 ºC
Humedad: 58 %
Luz: 42310
CO2/MQ135: 8750
Alerta luz baja: False
Alerta CO2: False
Estado: NORMAL
```

---

## 4. Acceso al Panel Visual (Grafana)

Si desea ver gráficos detallados e historiales, acceda al Panel Web:

1. Abra el navegador en su ordenador o tableta.
2. Introduzca la dirección proporcionada por el instalador (ej: `http://192.168.1.100:3000`).
3. Inicie sesión con las credenciales facilitadas.
4. Seleccione el dashboard para ver gráficos de evolución temporal de temperatura, humedad, luz y CO₂.

---

## 5. Consejos para Mejorar el Ambiente

| Situación | Recomendación |
|-----------|---------------|
| Humedad < 30% (Muy seco) | Use humidificadores o coloque recipientes con agua |
| Humedad > 70% (Riesgo) | Abra ventanas para ventilar, active extractores |
| CO₂ alto | Ventile la estancia al menos 10 minutos |
| Luz baja prolongada | Encienda luces artificiales |

---

## 6. Preguntas Frecuentes

**¿Qué hago si el bot no responde?**
Compruebe que el servidor donde se ejecuta el bot está encendido y conectado a Internet.

**¿Los datos se guardan?**
Sí, InfluxDB almacena todo el histórico. Puede consultarlo en Grafana.

**¿Necesito Internet para las alertas locales?**
No. El LED, el buzzer y el servo funcionan de forma autónoma sin conexión a Internet. Solo Telegram y Grafana requieren conexión.

**¿El buzzer suena constantemente si la humedad es alta?**
No. Suena una sola vez durante 3 segundos. No vuelve a sonar hasta que la humedad baje del 70% y vuelva a superarlo.
