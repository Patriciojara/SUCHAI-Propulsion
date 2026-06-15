#!/usr/bin/env python3
import time
import subprocess
import RPi.GPIO as GPIO

GPIO_PIN = 17

CMD_CAN_DOWN = "ip link set can0 down"
CMD_CAN_UP = "ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on"

CMD_SWITCH_ON = "cansend can0 100##1300301"

CMD_SALIDA8_ON = "cansend can0 100##10108190000008813"
CMD_SALIDA8_OFF = "cansend can0 100##10108190000000000"


def run_cmd(cmd, check=True):
    print(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, text=True)

    if check and result.returncode != 0:
        raise RuntimeError(f"Falló el comando: {cmd}")


try:
    print("Configurando CAN0...")

    run_cmd(CMD_CAN_DOWN, check=False)
    time.sleep(0.2)

    run_cmd(CMD_CAN_UP)
    time.sleep(0.5)

    print("Iniciando candump en segundo plano...")
    candump_process = subprocess.Popen(
        "candump -tz can0",
        shell=True
    )

    time.sleep(0.5)

    print("Configurando GPIO17...")

    GPIO.setmode(GPIO.BCM)

    # Leer el estado actual del GPIO17
    GPIO.setup(GPIO_PIN, GPIO.IN)
    estado = GPIO.input(GPIO_PIN)

    if estado == GPIO.LOW:
        print("GPIO17 está apagado. Encendiendo GPIO17...")
    else:
        print("GPIO17 ya estaba encendido.")

    GPIO.setup(GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH)

    print("Esperando 1 segundo...")
    time.sleep(1)

    print("Activando switch por CAN...")
    run_cmd(CMD_SWITCH_ON)

    time.sleep(0.3)

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
    print("Cerrando candump...")

    try:
        candump_process.terminate()
    except:
        pass

    # No se hace GPIO.cleanup() para no apagar GPIO17 al finalizar
    print("Fin del programa.")