#!/usr/bin/env python3
import argparse
import time
import subprocess
import RPi.GPIO as GPIO

GPIO_PIN = 17
CMD_SWITCH_ON = "cansend can0 100##1300301"
SALIDAS = {'s1': {'pin': 'PA10', 'on': 'cansend can0 100##10101190000008813', 'off': 'cansend can0 100##10101190000000000'}, 's2': {'pin': 'PA9', 'on': 'cansend can0 100##10102190000008813', 'off': 'cansend can0 100##10102190000000000'}, 's3': {'pin': 'PA8', 'on': 'cansend can0 100##10103190000008813', 'off': 'cansend can0 100##10103190000000000'}, 's4': {'pin': 'PC9', 'on': 'cansend can0 100##10104190000008813', 'off': 'cansend can0 100##10104190000000000'}, 's5': {'pin': 'PA0', 'on': 'cansend can0 100##10105190000008813', 'off': 'cansend can0 100##10105190000000000'}, 's6': {'pin': 'PA1', 'on': 'cansend can0 100##10106190000008813', 'off': 'cansend can0 100##10106190000000000'}, 's7': {'pin': 'PA2', 'on': 'cansend can0 100##10107190000008813', 'off': 'cansend can0 100##10107190000000000'}, 's8': {'pin': 'PA3', 'on': 'cansend can0 100##10108190000008813', 'off': 'cansend can0 100##10108190000000000'}, 's9': {'pin': 'PB1', 'on': 'cansend can0 100##10109190000008813', 'off': 'cansend can0 100##10109190000000000'}, 's12': {'pin': 'PB3', 'on': 'cansend can0 100##1010C190000008813', 'off': 'cansend can0 100##1010C190000000000'}, 's13': {'pin': 'PC6', 'on': 'cansend can0 100##1010D190000008813', 'off': 'cansend can0 100##1010D190000000000'}, 's14': {'pin': 'PD15', 'on': 'cansend can0 100##1010E190000008813', 'off': 'cansend can0 100##1010E190000000000'}, 's15': {'pin': 'PD14', 'on': 'cansend can0 100##1010F190000008813', 'off': 'cansend can0 100##1010F190000000000'}, 's16': {'pin': 'PB11', 'on': 'cansend can0 100##10110190000008813', 'off': 'cansend can0 100##10110190000000000'}, 's17': {'pin': 'PE14', 'on': 'cansend can0 100##10111190000008813', 'off': 'cansend can0 100##10111190000000000'}}


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
    parser = argparse.ArgumentParser(description="Control de salidas por CAN sin candump.")
    parser.add_argument("salida", choices=SALIDAS.keys(), help="Ejemplo: s1, s8, s17")
    parser.add_argument("accion", choices=["on", "off", "pulso"], help="Acción: on, off o pulso")
    parser.add_argument("--tiempo", type=float, default=1.0, help="Tiempo del pulso en segundos. Default: 1")
    args = parser.parse_args()

    salida = SALIDAS[args.salida]

    setup_can0_if_needed()
    ensure_gpio17_on()

    print("Esperando 1 segundo antes de mandar comandos CAN...")
    time.sleep(1)

    print("Activando switch por CAN...")
    run_cmd(CMD_SWITCH_ON)
    time.sleep(0.2)

    if args.accion == "on":
        print(f"Encendiendo {args.salida.upper()} / pin {salida['pin']}...")
        run_cmd(salida["on"])
    elif args.accion == "off":
        print(f"Apagando {args.salida.upper()} / pin {salida['pin']}...")
        run_cmd(salida["off"])
    elif args.accion == "pulso":
        print(f"Encendiendo {args.salida.upper()} / pin {salida['pin']}...")
        run_cmd(salida["on"])
        print(f"Esperando {args.tiempo} segundo(s)...")
        time.sleep(args.tiempo)
        print(f"Apagando {args.salida.upper()} / pin {salida['pin']}...")
        run_cmd(salida["off"])

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
