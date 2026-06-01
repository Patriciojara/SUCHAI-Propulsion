import can
from datetime import datetime

with can.Bus(interface="socketcan", channel="can0", fd=True) as bus:
    print("Escuchando can0. Ctrl+C para salir.")

    while True:
        msg = bus.recv()
        if msg is None:
            continue

        t = datetime.fromtimestamp(msg.timestamp).isoformat(timespec="milliseconds")

        data_hex = msg.data.hex(" ").upper()

        try:
            data_ascii = msg.data.decode("ascii", errors="replace")
        except Exception:
            data_ascii = ""

        print(
            f"{t} "
            f"ID=0x{msg.arbitration_id:X} "
            f"{'EXT' if msg.is_extended_id else 'STD'} "
            f"{'FD' if msg.is_fd else 'CAN'} "
            f"{'BRS' if msg.bitrate_switch else ''} "
            f"DLC={msg.dlc} "
            f"LEN={len(msg.data)} "
            f"HEX=[{data_hex}] "
            f"ASCII='{data_ascii}'"
        )