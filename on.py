import RPi.GPIO as GPIO
import time

# Usar numeración BCM
GPIO.setmode(GPIO.BCM)
# Configurar pin 8 como salida
LED_PIN = 8
GPIO.setup(LED_PIN, GPIO.OUT)

# Encender el pin
GPIO.output(LED_PIN, GPIO.HIGH)
print("Pin encendido")

# Mantener encendido por 5 segundos
time.sleep(5)

# Limpiar configuraciones
GPIO.cleanup()
