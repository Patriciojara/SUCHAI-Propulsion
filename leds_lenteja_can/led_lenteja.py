#!/usr/bin/env python3
import argparse
import subprocess
import time
import RPi.GPIO as GPIO

GPIO_PIN = 17

CMD_3V3_ON = "cansend can0 100##1300201"

LEDS = {
    "rojo": {
        "pin": "PB13",
        "grupo": "G4",
        "on": "cansend can0 100##1300401",
        "off": "cansend can0 100##1300400",
        "toggle": "cansend can0 100##13104",
        "get": "cansend can0 100##13204",
    },
    "blanco": {
        "pin": "PE8",
        "grupo": "G5",
        "on": "cansend can0 100##1300501",
        "off": "cansend can0 100##1300500",
        "toggle": "cansend can0 100##13105",
        "get": "cansend can0 100##13205",
    },
    "azul": {
        "pin": "PE4",
        "grupo": "G6",
        "on": "cansend can0 100##1300601",
        "off": "cansend can0 100##1300600",
        "toggle": "cansend can0 100##13106",
        "get": "cansend can0 100##13206",
    },
}


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

    txt = result.stdout

    # Ejemplos típicos:
    # 2: can0: <NOARP,UP,LOWER_UP,ECHO> ...
    # state UP ...
    return ("state UP" in txt) or ("<" in txt and ">" in txt and "UP" in txt.split(">")[0])


def setup_can0_if_needed():
    if can0_is_up():
        print("can0 ya está levantado. No se baja ni se reinicia.")
        return

    print("can0 está apagado. Levantando can0 sin ejecutar candump y sin hacer can0 down...")
    run_cmd("ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on")


def ensure_gpio17_on():
    GPIO.setmode(GPIO.BCM)

    # Dejamos GPIO17 como salida en HIGH.
    # No usamos cleanup al final para no apagar la placa al terminar.
    GPIO.setup(GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.output(GPIO_PIN, GPIO.HIGH)

    print("GPIO17 encendido.")


def preparar_sistema():
    """
    Secuencia base:
    1. Encender GPIO17.
    2. Levantar can0 si está apagado.
    3. Activar 3V3 en la placa por CAN.
    """
    print("Preparando sistema...")

    ensure_gpio17_on()
    time.sleep(0.5)

    setup_can0_if_needed()
    time.sleep(0.2)

    print("Activando 3V3 desde la placa...")
    run_cmd(CMD_3V3_ON)
    time.sleep(0.2)


def led_on(nombre_led):
    preparar_sistema()
    led = LEDS[nombre_led]
    print(f"Encendiendo LED {nombre_led.upper()} / {led['pin']} / {led['grupo']}...")
    run_cmd(led["on"])


def led_off(nombre_led):
    preparar_sistema()
    led = LEDS[nombre_led]
    print(f"Apagando LED {nombre_led.upper()} / {led['pin']} / {led['grupo']}...")
    run_cmd(led["off"])


def led_toggle(nombre_led):
    preparar_sistema()
    led = LEDS[nombre_led]
    print(f"Toggle LED {nombre_led.upper()} / {led['pin']} / {led['grupo']}...")
    run_cmd(led["toggle"])


def led_get(nombre_led):
    preparar_sistema()
    led = LEDS[nombre_led]
    print(f"Consultando estado LED {nombre_led.upper()} / {led['pin']} / {led['grupo']}...")
    run_cmd(led["get"])


def main():
    parser = argparse.ArgumentParser(
        description="Control de LEDs de lenteja por CAN: rojo, blanco y azul."
    )

    parser.add_argument(
        "led",
        choices=LEDS.keys(),
        help="LED a controlar: rojo, blanco o azul"
    )

    parser.add_argument(
        "accion",
        choices=["on", "off", "toggle", "get"],
        help="Acción: on, off, toggle o get"
    )

    args = parser.parse_args()

    if args.accion == "on":
        led_on(args.led)
    elif args.accion == "off":
        led_off(args.led)
    elif args.accion == "toggle":
        led_toggle(args.led)
    elif args.accion == "get":
        led_get(args.led)

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
