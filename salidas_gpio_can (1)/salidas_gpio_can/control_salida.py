#!/usr/bin/env python3
"""
control_salida.py

Control de salidas por CAN-FD desde Raspberry Pi Zero 2W.

- NO ejecuta "ip link set can0 down".
- Si can0 ya está arriba, lo deja tal cual para no cortar procesos paralelos
  como lectura de sensores.
- Si can0 está abajo, intenta levantarlo con:
  ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
- Activa GPIO17 en HIGH para alimentar/habilitar la placa.
- Puede encender, apagar o hacer pulso de 5 segundos por salida.

Uso:
  sudo python3 control_salida.py s8 pulso
  sudo python3 control_salida.py s8 on
  sudo python3 control_salida.py s8 off
  sudo python3 control_salida.py s8 pulso --tiempo 10
  sudo python3 control_salida.py s8 pulso --candump
"""

import argparse
import shlex
import subprocess
import sys
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None


GPIO_PIN = 17
SWITCH_ON_CMD = "cansend can0 100##1300301"

SALIDAS = {
    "s1": {
        "pin": "PA10",
        "on_info": "PA10 / TIM1_CH3",
        "on_cmd": "cansend can0 100##10101190000008813",
        "off_cmd": "cansend can0 100##10101190000000000"
    },
    "s2": {
        "pin": "PA9",
        "on_info": "PA9 / TIM1_CH2",
        "on_cmd": "cansend can0 100##10102190000008813",
        "off_cmd": "cansend can0 100##10102190000000000"
    },
    "s3": {
        "pin": "PA8",
        "on_info": "PA8 / TIM1_CH1",
        "on_cmd": "cansend can0 100##10103190000008813",
        "off_cmd": "cansend can0 100##10103190000000000"
    },
    "s4": {
        "pin": "PC9",
        "on_info": "PC9 / TIM8_CH4",
        "on_cmd": "cansend can0 100##10104190000008813",
        "off_cmd": "cansend can0 100##10104190000000000"
    },
    "s5": {
        "pin": "PA0",
        "on_info": "PA0 / TIM2_CH1",
        "on_cmd": "cansend can0 100##10105190000008813",
        "off_cmd": "cansend can0 100##10105190000000000"
    },
    "s6": {
        "pin": "PA1",
        "on_info": "PA1 / TIM5_CH2",
        "on_cmd": "cansend can0 100##10106190000008813",
        "off_cmd": "cansend can0 100##10106190000000000"
    },
    "s7": {
        "pin": "PA2",
        "on_info": "PA2 / TIM15_CH1",
        "on_cmd": "cansend can0 100##10107190000008813",
        "off_cmd": "cansend can0 100##10107190000000000"
    },
    "s8": {
        "pin": "PA3",
        "on_info": "PA3 / TIM15_CH2",
        "on_cmd": "cansend can0 100##10108190000008813",
        "off_cmd": "cansend can0 100##10108190000000000"
    },
    "s9": {
        "pin": "PB1",
        "on_info": "PB1 / TIM3_CH4",
        "on_cmd": "cansend can0 100##10109190000008813",
        "off_cmd": "cansend can0 100##10109190000000000"
    },
    "s12": {
        "pin": "PB3",
        "on_info": "PB3 / TIM2_CH2",
        "on_cmd": "cansend can0 100##1010C190000008813",
        "off_cmd": "cansend can0 100##1010C190000000000"
    },
    "s13": {
        "pin": "PC6",
        "on_info": "PC6 / TIM3_CH1",
        "on_cmd": "cansend can0 100##1010D190000008813",
        "off_cmd": "cansend can0 100##1010D190000000000"
    },
    "s14": {
        "pin": "PD15",
        "on_info": "PD15 / TIM4_CH4",
        "on_cmd": "cansend can0 100##1010E190000008813",
        "off_cmd": "cansend can0 100##1010E190000000000"
    },
    "s15": {
        "pin": "PD14",
        "on_info": "PD14 / TIM4_CH3",
        "on_cmd": "cansend can0 100##1010F190000008813",
        "off_cmd": "cansend can0 100##1010F190000000000"
    },
    "s16": {
        "pin": "PB11",
        "on_info": "PB11 / TIM2_CH4",
        "on_cmd": "cansend can0 100##10110190000008813",
        "off_cmd": "cansend can0 100##10110190000000000"
    },
    "s17": {
        "pin": "PE14",
        "on_info": "PE14 / TIM1_CH4",
        "on_cmd": "cansend can0 100##10111190000008813",
        "off_cmd": "cansend can0 100##10111190000000000"
    }
}


def run_cmd(cmd, check=True):
    print(f"> {cmd}")
    result = subprocess.run(shlex.split(cmd), text=True, capture_output=True)

    if result.stdout.strip():
        print(result.stdout.strip())

    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip())

        if check:
            raise RuntimeError(f"Falló el comando: {cmd}")

    return result


def can0_is_up():
    result = subprocess.run(
        ["ip", "-details", "link", "show", "can0"],
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        print("No pude leer can0. Revisa que exista la interfaz can0.")
        if result.stderr.strip():
            print(result.stderr.strip())
        return False

    output = result.stdout
    return "state UP" in output or "<NOARP,UP" in output or ",UP," in output


def ensure_can0_up():
    print("Revisando estado de can0...")

    if can0_is_up():
        print("can0 ya está UP. No ejecuto 'ip link set can0 down'.")
        return

    print("can0 está abajo. Lo levantaré sin bajarlo primero...")
    run_cmd("ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on")
    time.sleep(0.3)


def start_candump_if_requested(enabled):
    if not enabled:
        return None

    print("Iniciando candump en segundo plano...")
    return subprocess.Popen(["candump", "-tz", "can0"])


def ensure_gpio17_high():
    if GPIO is None:
        raise RuntimeError(
            "No está instalada la librería RPi.GPIO. Instala con: sudo apt install python3-rpi.gpio"
        )

    print("Revisando GPIO17...")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    estado = None
    try:
        GPIO.setup(GPIO_PIN, GPIO.IN)
        estado = GPIO.input(GPIO_PIN)
    except Exception:
        estado = None

    if estado == GPIO.HIGH:
        print("GPIO17 ya parece estar encendido.")
    elif estado == GPIO.LOW:
        print("GPIO17 parece apagado. Encendiendo...")
    else:
        print("No pude leer GPIO17, pero lo dejaré en HIGH.")

    GPIO.setup(GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.output(GPIO_PIN, GPIO.HIGH)
    print("GPIO17 en HIGH.")
    time.sleep(1)


def controlar_salida(salida, accion, tiempo=5, candump=False):
    salida = salida.lower().strip()

    if salida not in SALIDAS:
        disponibles = ", ".join(SALIDAS.keys())
        raise ValueError(f"Salida no válida: {salida}. Disponibles: {disponibles}")

    data = SALIDAS[salida]

    candump_process = None

    try:
        ensure_can0_up()
        candump_process = start_candump_if_requested(candump)
        ensure_gpio17_high()

        if accion in ("on", "encender", "activar", "pulso"):
            print("Activando switch por CAN...")
            run_cmd(SWITCH_ON_CMD)
            time.sleep(0.2)

        if accion in ("on", "encender", "activar"):
            print(f"Encendiendo {salida.upper()} -> {data['on_info']}")
            run_cmd(data["on_cmd"])

        elif accion in ("off", "apagar", "desactivar"):
            print(f"Apagando {salida.upper()} -> {data['pin']}")
            run_cmd(data["off_cmd"])

        elif accion == "pulso":
            print(f"Encendiendo {salida.upper()} -> {data['on_info']}")
            run_cmd(data["on_cmd"])

            print(f"{salida.upper()} activa por {tiempo} segundos...")
            time.sleep(tiempo)

            print(f"Apagando {salida.upper()}...")
            run_cmd(data["off_cmd"])

        else:
            raise ValueError("Acción no válida. Usa: on, off o pulso.")

        print("Proceso terminado correctamente.")

    finally:
        if candump_process is not None:
            print("Cerrando candump...")
            candump_process.terminate()

        # Importante: no hacemos GPIO.cleanup() para no apagar GPIO17 al terminar.


def main():
    parser = argparse.ArgumentParser(description="Control de salidas por CAN-FD")
    parser.add_argument("salida", help="Salida a controlar. Ejemplo: s1, s2, s8, s17")
    parser.add_argument(
        "accion",
        choices=["on", "off", "pulso", "encender", "apagar", "activar", "desactivar"],
        help="Acción: on, off o pulso"
    )
    parser.add_argument(
        "--tiempo",
        type=float,
        default=5,
        help="Tiempo en segundos para la acción pulso. Por defecto: 5"
    )
    parser.add_argument(
        "--candump",
        action="store_true",
        help="Inicia candump -tz can0 en segundo plano mientras corre el script"
    )

    args = parser.parse_args()
    controlar_salida(args.salida, args.accion, args.tiempo, args.candump)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
