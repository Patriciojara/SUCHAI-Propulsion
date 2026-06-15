#!/usr/bin/env python3
"""
apagar_s3.py

Script para apaga la salida S3.
No baja can0. Si can0 ya está UP, lo deja tal cual.
"""

from control_salida import controlar_salida

if __name__ == "__main__":
    controlar_salida("s3", "off", tiempo=5, candump=False)
