# Patricio Jara Quiroz
# 11-12-2026

# Este Codigo entrega el estatus actual de algunos sensores.


import spidev
import time
import struct
import math

# ===== Configuración SPI =====
spi = spidev.SpiDev()
spi.open(0, 0)             # SPI0, CE0
spi.max_speed_hz = 500000
spi.mode = 0
spi.bits_per_word = 8

# ===== Escalas (ajústalas si cambias FS en el IMU) =====
ACCEL_LSB_PER_G = 2048.0   # ±16 g
GYRO_LSB_PER_DPS = 16.4    # ±2000 dps

def read_frame():
    rx = spi.xfer2([0x00] * 16)

    # Verificar cabecera
    if rx[0] != 0xAA or rx[1] != 0x55:
        print("Frame inválido:", rx)
        return None

    # Desempaquetar 7 int16 big-endian
    temp_raw, ax, ay, az, gx, gy, gz = struct.unpack(">7h", bytes(rx[2:16]))

    return temp_raw, ax, ay, az, gx, gy, gz


def print_imu(temp_raw, ax, ay, az, gx, gy, gz):
    # Conversión
    temp_c = temp_raw / 132.48 + 25.0

    ax_g = ax / ACCEL_LSB_PER_G
    ay_g = ay / ACCEL_LSB_PER_G
    az_g = az / ACCEL_LSB_PER_G
    a_mag = math.sqrt(ax_g**2 + ay_g**2 + az_g**2)

    gx_dps = gx / GYRO_LSB_PER_DPS
    gy_dps = gy / GYRO_LSB_PER_DPS
    gz_dps = gz / GYRO_LSB_PER_DPS

    # Limpiar pantalla (opcional)
    print("\033[H\033[J", end="")   # ANSI clear screen

    print("===== ICM42688P =====")
    print(f"Temperatura : {temp_c:6.2f} °C")
    print()
    print("Acelerómetro [g]")
    print(f"  X: {ax_g:7.3f}")
    print(f"  Y: {ay_g:7.3f}")
    print(f"  Z: {az_g:7.3f}")
    print(f"  |A|: {a_mag:7.3f}")
    print()
    print("Giroscopio [°/s]")
    print(f"  X: {gx_dps:7.2f}")
    print(f"  Y: {gy_dps:7.2f}")
    print(f"  Z: {gz_dps:7.2f}")
    print("=====================")


# ===== Loop principal =====
while True:
    data = read_frame()
    if data:
        print_imu(*data)

    time.sleep(0.1)   # 10 Hz en pantalla
