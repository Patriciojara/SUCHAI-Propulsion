#!/usr/bin/env python3
import argparse
import csv
import math
import re
import signal
import time
from datetime import datetime

import can


# =========================
# CAN IDs
# =========================
CAN_TX_ID = 0x100
CAN_ACK_ID = 0x101

CAN_ICM_ID = 0x200
CAN_AK_ID = 0x201
CAN_INA3V3_ID = 0x202
CAN_INABAT_ID = 0x203
CAN_TMP102_ID = 0x204


# =========================
# Comandos CAN
# =========================
CMD_GPIO_SET = 0x30

CMD_ICM_WHO = 0x41
CMD_ICM_STREAM = 0x42

CMD_AK_WHO = 0x51
CMD_AK_STREAM = 0x52

CMD_INA_WHO = 0x60
CMD_INA_STREAM = 0x63

CMD_TMP102_GET = 0x70
CMD_TMP102_STREAM = 0x71


# =========================
# Escalas ICM
# Firmware actual:
# ACCEL_CONFIG0 = 0x06 -> +/-16 g
# GYRO_CONFIG0  = 0x06 -> +/-2000 dps
# =========================
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


def set_g1_1v8(bus, enabled: bool):
    """
    Según tu firmware:
    G1 = PE5 = ON 1V8.
    Se usa para alimentar/activar el AK si corresponde.
    """
    send_fd(bus, [CMD_GPIO_SET, 0x01, 0x01 if enabled else 0x00])


def request_checks(bus):
    send_fd(bus, [CMD_ICM_WHO])
    time.sleep(0.05)

    send_fd(bus, [CMD_AK_WHO])
    time.sleep(0.05)

    send_fd(bus, [CMD_INA_WHO])
    time.sleep(0.05)

    send_fd(bus, [CMD_TMP102_GET])


def enable_streams(bus, use_icm=True, use_ak=True, use_ina=True, use_tmp102=True):
    if use_icm:
        send_fd(bus, [CMD_ICM_STREAM, 0x01])
        time.sleep(0.05)

    if use_ak:
        send_fd(bus, [CMD_AK_STREAM, 0x01])
        time.sleep(0.05)

    if use_ina:
        send_fd(bus, [CMD_INA_STREAM, 0x01])
        time.sleep(0.05)

    if use_tmp102:
        send_fd(bus, [CMD_TMP102_STREAM, 0x01])
        time.sleep(0.05)


def disable_streams(bus, use_icm=True, use_ak=True, use_ina=True, use_tmp102=True):
    if use_icm:
        send_fd(bus, [CMD_ICM_STREAM, 0x00])
        time.sleep(0.05)

    if use_ak:
        send_fd(bus, [CMD_AK_STREAM, 0x00])
        time.sleep(0.05)

    if use_ina:
        send_fd(bus, [CMD_INA_STREAM, 0x00])
        time.sleep(0.05)

    if use_tmp102:
        send_fd(bus, [CMD_TMP102_STREAM, 0x00])
        time.sleep(0.05)


def parse_icm(text):
    """
    Formato esperado:
    ICM A=986,13,-1773 G=22,-4,-23 T=30.4C
    """
    pattern = (
        r"ICM\s+A=(-?\d+),(-?\d+),(-?\d+)\s+"
        r"G=(-?\d+),(-?\d+),(-?\d+)\s+"
        r"T=(-?\d+(?:\.\d+)?)C"
    )

    m = re.search(pattern, text)

    if not m:
        return None

    ax_raw = int(m.group(1))
    ay_raw = int(m.group(2))
    az_raw = int(m.group(3))

    gx_raw = int(m.group(4))
    gy_raw = int(m.group(5))
    gz_raw = int(m.group(6))

    temp_c = float(m.group(7))

    ax_g = ax_raw / ACCEL_LSB_PER_G
    ay_g = ay_raw / ACCEL_LSB_PER_G
    az_g = az_raw / ACCEL_LSB_PER_G

    gx_dps = gx_raw / GYRO_LSB_PER_DPS
    gy_dps = gy_raw / GYRO_LSB_PER_DPS
    gz_dps = gz_raw / GYRO_LSB_PER_DPS

    return {
        "sensor": "ICM42688V",
        "ax_raw": ax_raw,
        "ay_raw": ay_raw,
        "az_raw": az_raw,
        "gx_raw": gx_raw,
        "gy_raw": gy_raw,
        "gz_raw": gz_raw,
        "ax_g": ax_g,
        "ay_g": ay_g,
        "az_g": az_g,
        "ax_ms2": ax_g * GRAVITY,
        "ay_ms2": ay_g * GRAVITY,
        "az_ms2": az_g * GRAVITY,
        "accel_norm_g": math.sqrt(ax_g**2 + ay_g**2 + az_g**2),
        "gx_dps": gx_dps,
        "gy_dps": gy_dps,
        "gz_dps": gz_dps,
        "gyro_norm_dps": math.sqrt(gx_dps**2 + gy_dps**2 + gz_dps**2),
        "icm_temp_c": temp_c,
    }


def parse_ak(text):
    """
    Formato esperado:
    AK M=12.34,-5.67,40.12uT T=...
    """
    pattern = r"AK\s+M=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)uT\s+T=(\d+)"

    m = re.search(pattern, text)

    if not m:
        return None

    mx_uT = float(m.group(1))
    my_uT = float(m.group(2))
    mz_uT = float(m.group(3))
    temp_raw = int(m.group(4))

    return {
        "sensor": "AK09940A",
        "mx_uT": mx_uT,
        "my_uT": my_uT,
        "mz_uT": mz_uT,
        "mag_norm_uT": math.sqrt(mx_uT**2 + my_uT**2 + mz_uT**2),
        "ak_temp_raw": temp_raw,
    }


def parse_ina(text):
    """
    Formato esperado:
    INA3V3 I=0.00mA V=3313.75mV P=0mW
    INABAT I=-3.75mA V=1.25mV P=0mW
    """
    pattern = r"(INA3V3|INABAT)\s+I=(-?\d+(?:\.\d+)?)mA\s+V=(-?\d+(?:\.\d+)?)mV\s+P=(-?\d+)mW"

    m = re.search(pattern, text)

    if not m:
        return None

    name = m.group(1)
    current_mA = float(m.group(2))
    voltage_mV = float(m.group(3))
    power_mW = float(m.group(4))

    return {
        "sensor": name,
        "current_mA": current_mA,
        "voltage_mV": voltage_mV,
        "voltage_V": voltage_mV / 1000.0,
        "power_mW": power_mW,
    }


def parse_tmp102(text):
    """
    Formato esperado:
    TMP102 T=25.37C
    """
    pattern = r"TMP102\s+T=(-?\d+(?:\.\d+)?)C"

    m = re.search(pattern, text)

    if not m:
        return None

    return {
        "sensor": "TMP102",
        "tmp102_temp_c": float(m.group(1)),
    }


def parse_message(can_id, text):
    if can_id == CAN_ICM_ID:
        return parse_icm(text)

    if can_id == CAN_AK_ID:
        return parse_ak(text)

    if can_id in (CAN_INA3V3_ID, CAN_INABAT_ID):
        return parse_ina(text)

    if can_id == CAN_TMP102_ID:
        return parse_tmp102(text)

    return None


def print_row(row):
    sensor = row.get("sensor", "")

    if sensor == "ICM42688V":
        print(
            f"{row['timestamp_iso']} ICM "
            f"ACC[g] x={row['ax_g']:+.3f} y={row['ay_g']:+.3f} z={row['az_g']:+.3f} "
            f"|A|={row['accel_norm_g']:.3f} "
            f"GYRO[dps] x={row['gx_dps']:+.2f} y={row['gy_dps']:+.2f} z={row['gz_dps']:+.2f} "
            f"T={row['icm_temp_c']:.1f}C"
        )

    elif sensor == "AK09940A":
        print(
            f"{row['timestamp_iso']} AK  "
            f"M[uT] x={row['mx_uT']:+.2f} y={row['my_uT']:+.2f} z={row['mz_uT']:+.2f} "
            f"|M|={row['mag_norm_uT']:.2f}uT"
        )

    elif sensor in ("INA3V3", "INABAT"):
        print(
            f"{row['timestamp_iso']} {sensor} "
            f"I={row['current_mA']:+.2f}mA "
            f"V={row['voltage_V']:.3f}V "
            f"P={row['power_mW']:.0f}mW"
        )

    elif sensor == "TMP102":
        print(
            f"{row['timestamp_iso']} TMP102 "
            f"T={row['tmp102_temp_c']:.2f}C"
        )


def default_output():
    return f"all_sensors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


def main():
    parser = argparse.ArgumentParser(
        description="Logger CSV continuo para todos los sensores: ICM, AK, INA260 y TMP102."
    )

    parser.add_argument("--channel", default="can0", help="Interfaz CAN. Default: can0")
    parser.add_argument("--output", default=None, help="Archivo CSV de salida")

    parser.add_argument("--no-check", action="store_true", help="No consulta WHO/check al inicio")
    parser.add_argument("--no-power-on-ak", action="store_true", help="No activa G1/PE5/1V8 para AK al inicio")
    parser.add_argument("--power-off-ak-exit", action="store_true", help="Apaga G1/PE5/1V8 al salir")

    parser.add_argument("--no-icm", action="store_true", help="No activa/guarda ICM")
    parser.add_argument("--no-ak", action="store_true", help="No activa/guarda AK09940A")
    parser.add_argument("--no-ina", action="store_true", help="No activa/guarda INA260")
    parser.add_argument("--no-tmp102", action="store_true", help="No activa/guarda TMP102")

    parser.add_argument("--no-stream-off", action="store_true", help="No apaga streams al salir")
    parser.add_argument("--print", action="store_true", help="Imprime datos procesados en pantalla")
    parser.add_argument("--show-raw", action="store_true", help="Muestra texto CAN crudo")

    args = parser.parse_args()

    use_icm = not args.no_icm
    use_ak = not args.no_ak
    use_ina = not args.no_ina
    use_tmp102 = not args.no_tmp102

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    output = args.output or default_output()

    bus = can.interface.Bus(
        channel=args.channel,
        interface="socketcan",
        fd=True,
    )

    fieldnames = [
        "timestamp_iso",
        "epoch_s",
        "elapsed_s",
        "can_id",
        "sensor",
        "raw_text",

        # ICM
        "ax_raw",
        "ay_raw",
        "az_raw",
        "gx_raw",
        "gy_raw",
        "gz_raw",
        "ax_g",
        "ay_g",
        "az_g",
        "ax_ms2",
        "ay_ms2",
        "az_ms2",
        "accel_norm_g",
        "gx_dps",
        "gy_dps",
        "gz_dps",
        "gyro_norm_dps",
        "icm_temp_c",

        # AK
        "mx_uT",
        "my_uT",
        "mz_uT",
        "mag_norm_uT",
        "ak_temp_raw",

        # INA
        "current_mA",
        "voltage_mV",
        "voltage_V",
        "power_mW",

        # TMP102
        "tmp102_temp_c",
    ]

    wanted_ids = set()

    if use_icm:
        wanted_ids.add(CAN_ICM_ID)

    if use_ak:
        wanted_ids.add(CAN_AK_ID)

    if use_ina:
        wanted_ids.add(CAN_INA3V3_ID)
        wanted_ids.add(CAN_INABAT_ID)

    if use_tmp102:
        wanted_ids.add(CAN_TMP102_ID)

    print("========================================")
    print(" Logger TODOS los sensores por CAN-FD")
    print("========================================")
    print(f"CAN: {args.channel}")
    print(f"CSV: {output}")
    print("IDs activos:")
    if use_icm:
        print("  ICM      -> 0x200")
    if use_ak:
        print("  AK       -> 0x201")
    if use_ina:
        print("  INA3V3   -> 0x202")
        print("  INABAT   -> 0x203")
    if use_tmp102:
        print("  TMP102   -> 0x204")
    print("Ctrl+C para terminar")
    print("========================================")

    start = time.monotonic()
    samples = 0

    try:
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            f.flush()

            if use_ak and not args.no_power_on_ak:
                print("Activando 1V8 para AK: G1/PE5 ON")
                set_g1_1v8(bus, True)
                time.sleep(0.3)

            if not args.no_check:
                print("Consultando WHO/check inicial...")
                request_checks(bus)

                t0 = time.time()
                while time.time() - t0 < 2.0:
                    msg = bus.recv(timeout=0.2)

                    if msg is None:
                        continue

                    if msg.arbitration_id == CAN_ACK_ID:
                        text = clean_ascii(bytes(msg.data))
                        if text:
                            print(f"ACK: {text}")

            print("Activando streams...")
            enable_streams(
                bus,
                use_icm=use_icm,
                use_ak=use_ak,
                use_ina=use_ina,
                use_tmp102=use_tmp102,
            )

            while running:
                msg = bus.recv(timeout=1.0)

                if msg is None:
                    continue

                if msg.arbitration_id == CAN_ACK_ID:
                    text = clean_ascii(bytes(msg.data))
                    if text and args.show_raw:
                        print(f"ACK: {text}")
                    continue

                if msg.arbitration_id not in wanted_ids:
                    continue

                text = clean_ascii(bytes(msg.data))

                if not text:
                    continue

                if args.show_raw:
                    print(f"RAW 0x{msg.arbitration_id:X}: {text}")

                parsed = parse_message(msg.arbitration_id, text)

                if parsed is None:
                    print(f"No parseado 0x{msg.arbitration_id:X}: {text}")
                    continue

                now = datetime.now().astimezone()

                row = {key: "" for key in fieldnames}
                row.update(parsed)
                row["timestamp_iso"] = now.isoformat(timespec="milliseconds")
                row["epoch_s"] = f"{time.time():.6f}"
                row["elapsed_s"] = f"{time.monotonic() - start:.6f}"
                row["can_id"] = f"0x{msg.arbitration_id:X}"
                row["raw_text"] = text

                writer.writerow(row)
                f.flush()

                samples += 1

                if args.print:
                    print_row(row)
                elif samples % 25 == 0:
                    print(f"Muestras guardadas: {samples}")

    finally:
        if not args.no_stream_off:
            print("\nApagando streams...")
            try:
                disable_streams(
                    bus,
                    use_icm=use_icm,
                    use_ak=use_ak,
                    use_ina=use_ina,
                    use_tmp102=use_tmp102,
                )
            except Exception:
                pass

        if use_ak and args.power_off_ak_exit:
            try:
                set_g1_1v8(bus, False)
                print("1V8 AK OFF")
            except Exception:
                pass

        bus.shutdown()
        print(f"Archivo guardado: {output}")
        print("Listo.")


if __name__ == "__main__":
    main()
