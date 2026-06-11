#!/usr/bin/env python3
import subprocess
import time
import signal
import sys

import RPi.GPIO as GPIO


CAN_IFACE = "can0"
GPIO_PIN = 17  # BCM GPIO17

SLEEP_GPIO_ACTIVO = 2
SLEEP_SALIDA_3 = 3

# Si quieres que GPIO17 quede apagado al final, cambia esto a False
DEJAR_GPIO17_ACTIVO_AL_FINAL = True


def run_cmd(cmd, check=True):
    print(f"> Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, check=check)


def start_candump():
    print("> Iniciando candump para monitoreo CAN...")
    return subprocess.Popen(["candump", "-tz", CAN_IFACE])


def send_can(frame):
    cmd = ["cansend", CAN_IFACE, frame]
    run_cmd(cmd)


def cleanup(candump_proc=None):
    print("\n> Cerrando script...")

    if candump_proc is not None:
        print("> Deteniendo candump...")
        candump_proc.terminate()
        try:
            candump_proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            candump_proc.kill()

    if not DEJAR_GPIO17_ACTIVO_AL_FINAL:
        print("> Apagando GPIO17...")
        GPIO.output(GPIO_PIN, GPIO.LOW)

    GPIO.cleanup()
    print("> Limpieza terminada.")


def main():
    candump_proc = None

    try:
        print("=== Inicio de secuencia CAN + GPIO ===")

        print("\n[1] Configurando CAN-FD")
        run_cmd(["sudo", "ip", "link", "set", CAN_IFACE, "down"], check=False)

        run_cmd([
            "sudo", "ip", "link", "set", CAN_IFACE, "up",
            "type", "can",
            "bitrate", "500000",
            "dbitrate", "2000000",
            "fd", "on"
        ])

        time.sleep(0.5)

        candump_proc = start_candump()
        time.sleep(1)

        print("\n[2] Activando GPIO17 de la Raspberry Pi")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_PIN, GPIO.OUT)

        GPIO.output(GPIO_PIN, GPIO.HIGH)
        print(f"> GPIO{GPIO_PIN} activado en HIGH")
        print(f"> Esperando {SLEEP_GPIO_ACTIVO} segundos con GPIO17 activo...")
        time.sleep(SLEEP_GPIO_ACTIVO)

        print("\n[3] Encendiendo switch 8V4 por CAN")
        send_can("100##1300301")
        time.sleep(0.5)

        print("\n[4] Activando salida 3")
        send_can("100##10103190000008813")

        print(f"> Salida 3 activa por {SLEEP_SALIDA_3} segundos...")
        time.sleep(SLEEP_SALIDA_3)

        print("\n[5] Desactivando salida 3")
        send_can("100##10103190000000000")

        print("\n=== Secuencia terminada correctamente ===")

    except KeyboardInterrupt:
        print("\n> Interrumpido por usuario.")

    except subprocess.CalledProcessError as e:
        print(f"\nERROR ejecutando comando: {e.cmd}")
        print(f"Código de salida: {e.returncode}")

    finally:
        cleanup(candump_proc)


if __name__ == "__main__":
    main()