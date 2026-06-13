#!/usr/bin/env python3
import argparse
import math
import re
import signal
import sys
import time

import can


CAN_TX_ID = 0x100
CAN_ACK_ID = 0x101
CAN_STREAM_ID = 0x200

CMD_ICM_READ = 0x40
CMD_ICM_WHOAMI = 0x41
CMD_ICM_STREAM_SET = 0x42

# Según la configuración que dejamos en el STM32:
# ACCEL_CONFIG0 = 0x06 -> ±16 g
# GYRO_CONFIG0  = 0x06 -> ±2000 dps
ACCEL_LSB_PER_G = 2048.0
GYRO_LSB_PER_DPS = 16.4
GRAVITY = 9.80665


running = True


def stop_handler(signum, frame):
    global running
    running = False


def clean_ascii(data: bytes) -> str:
    return data.rstrip(b"\x00").decode("ascii", errors="ignore").strip()


def send_fd(bus, data):
    msg = can.Message(
        arbitration_id=CAN_TX_ID,
        data=bytearray(data),
        is_extended_id=False,
        is_fd=True,
        bitrate_switch=True,
    )
    bus.send(msg)


def enable_stream(bus):
    send_fd(bus, [CMD_ICM_STREAM_SET, 0x01])


def disable_stream(bus):
    send_fd(bus, [CMD_ICM_STREAM_SET, 0x00])


def request_whoami(bus):
    send_fd(bus, [CMD_ICM_WHOAMI])


def request_single_read(bus):
    send_fd(bus, [CMD_ICM_READ])


def parse_icm_text(text):
    """
    Espera texto tipo:
    ICM A=986,13,-1773 G=22,-4,-23 T=30.4C
    """

    pattern = (
        r"ICM\s+A=(-?\d+),(-?\d+),(-?\d+)\s+"
        r"G=(-?\d+),(-?\d+),(-?\d+)\s+"
        r"T=(-?\d+(?:\.\d+)?)C"
    )

    match = re.search(pattern, text)

    if not match:
        return None

    ax_raw = int(match.group(1))
    ay_raw = int(match.group(2))
    az_raw = int(match.group(3))

    gx_raw = int(match.group(4))
    gy_raw = int(match.group(5))
    gz_raw = int(match.group(6))

    temp_c = float(match.group(7))

    ax_g = ax_raw / ACCEL_LSB_PER_G
    ay_g = ay_raw / ACCEL_LSB_PER_G
    az_g = az_raw / ACCEL_LSB_PER_G

    gx_dps = gx_raw / GYRO_LSB_PER_DPS
    gy_dps = gy_raw / GYRO_LSB_PER_DPS
    gz_dps = gz_raw / GYRO_LSB_PER_DPS

    ax_ms2 = ax_g * GRAVITY
    ay_ms2 = ay_g * GRAVITY
    az_ms2 = az_g * GRAVITY

    accel_norm_g = math.sqrt(ax_g**2 + ay_g**2 + az_g**2)
    gyro_norm_dps = math.sqrt(gx_dps**2 + gy_dps**2 + gz_dps**2)

    return {
        "ax_raw": ax_raw,
        "ay_raw": ay_raw,
        "az_raw": az_raw,
        "gx_raw": gx_raw,
        "gy_raw": gy_raw,
        "gz_raw": gz_raw,
        "ax_g": ax_g,
        "ay_g": ay_g,
        "az_g": az_g,
        "ax_ms2": ax_ms2,
        "ay_ms2": ay_ms2,
        "az_ms2": az_ms2,
        "gx_dps": gx_dps,
        "gy_dps": gy_dps,
        "gz_dps": gz_dps,
        "accel_norm_g": accel_norm_g,
        "gyro_norm_dps": gyro_norm_dps,
        "temp_c": temp_c,
    }


def print_processed(d):
    print(
        f"ACC[g]  x={d['ax_g']:+.3f}  y={d['ay_g']:+.3f}  z={d['az_g']:+.3f}  "
        f"|A|={d['accel_norm_g']:.3f} g   "
        f"ACC[m/s2] x={d['ax_ms2']:+.2f} y={d['ay_ms2']:+.2f} z={d['az_ms2']:+.2f}   "
        f"GYRO[dps] x={d['gx_dps']:+.2f} y={d['gy_dps']:+.2f} z={d['gz_dps']:+.2f}  "
        f"|G|={d['gyro_norm_dps']:.2f} dps   "
        f"T={d['temp_c']:.1f} °C"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Activa telemetría CAN-FD del ICM-42688-V y muestra datos procesados."
    )

    parser.add_argument("--channel", default="can0", help="Interfaz CAN. Default: can0")
    parser.add_argument("--no-whoami", action="store_true", help="No consulta WHO_AM_I al inicio")
    parser.add_argument("--poll", action="store_true", help="No usa stream; pide una lectura con 0x40 repetidamente")
    parser.add_argument("--period", type=float, default=0.1, help="Periodo en modo poll. Default: 0.1 s")
    parser.add_argument("--show-raw", action="store_true", help="También muestra el texto raw recibido")
    parser.add_argument("--timeout", type=float, default=1.0, help="Timeout de recepción. Default: 1.0 s")

    args = parser.parse_args()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    bus = can.interface.Bus(channel=args.channel, interface="socketcan", fd=True)

    print("========================================")
    print(" ICM-42688-V CAN-FD Telemetría")
    print("========================================")
    print(f"CAN: {args.channel}")
    print("TX ID: 0x100")
    print("ACK ID: 0x101")
    print("STREAM ID: 0x200")
    print("Escala accel: ±16 g -> 2048 LSB/g")
    print("Escala gyro:  ±2000 dps -> 16.4 LSB/dps")
    print("Ctrl+C para salir")
    print("========================================")

    try:
        if not args.no_whoami:
            print("Consultando WHO_AM_I...")
            request_whoami(bus)
            start = time.time()

            while time.time() - start < 2.0:
                msg = bus.recv(timeout=0.2)
                if msg is None:
                    continue

                if msg.arbitration_id == CAN_ACK_ID:
                    text = clean_ascii(bytes(msg.data))
                    if text:
                        print(f"Respuesta: {text}")
                        break

        if args.poll:
            print("Modo poll: pidiendo lecturas con comando 0x40...")
        else:
            print("Activando telemetría periódica...")
            enable_stream(bus)

        while running:
            if args.poll:
                request_single_read(bus)

            msg = bus.recv(timeout=args.timeout)

            if msg is None:
                continue

            if msg.arbitration_id not in (CAN_ACK_ID, CAN_STREAM_ID):
                continue

            text = clean_ascii(bytes(msg.data))

            if not text:
                continue

            if args.show_raw:
                print(f"RAW CAN 0x{msg.arbitration_id:X}: {text}")

            parsed = parse_icm_text(text)

            if parsed is not None:
                print_processed(parsed)
            else:
                if "ICM WHO" in text or "sensor stream" in text or "error" in text:
                    print(text)

            if args.poll:
                time.sleep(args.period)

    finally:
        if not args.poll:
            print("\nDesactivando telemetría...")
            try:
                disable_stream(bus)
            except Exception:
                pass

        bus.shutdown()
        print("Listo.")


if __name__ == "__main__":
    main()