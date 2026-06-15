#!/usr/bin/env python3
import time
import subprocess
import RPi.GPIO as GPIO

GPIO_PIN = 17
PULSE_TIME_S = 1

CMD_SWITCH_ON = "cansend can0 100##1300301"
CMD_OUTPUT_ON = "cansend can0 100##10103190000008813"
CMD_OUTPUT_OFF = "cansend can0 100##10103190000000000"


def run_cmd(cmd, check=True):
    print(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"Falló el comando: {cmd}")


def can0_is_up():
    result = subprocess.run(
        "ip link show can0",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return False
    return "state UP" in result.stdout or ("<" in result.stdout and "UP" in result.stdout.split(">", 1)[0])


def setup_can0_if_needed():
    if can0_is_up():
        print("can0 ya está levantado. No se baja ni se reinicia.")
        return
    print("can0 está apagado. Levantando can0 sin ejecutar candump...")
    run_cmd("ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on")


def ensure_gpio17_on():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.output(GPIO_PIN, GPIO.HIGH)
    print("GPIO17 encendido.")


def main():
    print("========================================")
    print("Activando S3 / pin STM32 PA8")
    print("Tiempo activo: 1 segundo")
    print("========================================")

    setup_can0_if_needed()
    ensure_gpio17_on()

    print("Esperando 1 segundo antes de mandar comandos CAN...")
    time.sleep(1)

    print("Activando switch por CAN...")
    run_cmd(CMD_SWITCH_ON)

    time.sleep(0.2)

    print("Encendiendo S3...")
    run_cmd(CMD_OUTPUT_ON)

    print("Esperando 1 segundo...")
    time.sleep(PULSE_TIME_S)

    print("Apagando S3...")
    run_cmd(CMD_OUTPUT_OFF)

    print("Proceso terminado correctamente.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # No hacemos GPIO.cleanup() para no apagar GPIO17 al terminar.
        pass
