#!/usr/bin/env python3
import time
import subprocess
import RPi.GPIO as GPIO

GPIO_PIN = 17

CMD_SWITCH_ON = "cansend can0 100##1300301"
CMD_SALIDA8_ON = "cansend can0 100##10108190000008813"
CMD_SALIDA8_OFF = "cansend can0 100##10108190000000000"


def run_cmd(cmd):
    print(f"Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error ejecutando comando:")
        print(result.stderr)
        raise RuntimeError(f"Falló comando: {cmd}")

    if result.stdout.strip():
        print(result.stdout.strip())


try:
    GPIO.setmode(GPIO.BCM)

    # Lee primero el estado del GPIO17
    GPIO.setup(GPIO_PIN, GPIO.IN)
    estado = GPIO.input(GPIO_PIN)

    if estado == GPIO.LOW:
        print("GPIO17 está apagado. Activando...")
        GPIO.setup(GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH)
    else:
        print("GPIO17 ya estaba encendido.")
        GPIO.setup(GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH)

    print("Esperando 1 segundo...")
    time.sleep(1)

    print("Activando switch por CAN...")
    run_cmd(CMD_SWITCH_ON)

    time.sleep(0.2)

    print("Activando salida 8...")
    run_cmd(CMD_SALIDA8_ON)

    print("Salida 8 activa por 5 segundos...")
    time.sleep(5)

    print("Apagando salida 8...")
    run_cmd(CMD_SALIDA8_OFF)

    print("Proceso terminado correctamente.")

except KeyboardInterrupt:
    print("\nPrograma interrumpido por el usuario.")

except Exception as e:
    print(f"Error: {e}")

finally:
    # No uso GPIO.cleanup() para no apagar GPIO17 al terminar
    pass