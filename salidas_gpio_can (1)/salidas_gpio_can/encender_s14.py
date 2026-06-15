#!/usr/bin/env python3
"""
encender_s14.py

Script para enciende sin apagar la salida S14.
No baja can0. Si can0 ya está UP, lo deja tal cual.
"""

from control_salida import controlar_salida

if __name__ == "__main__":
    controlar_salida("s14", "on", tiempo=5, candump=False)
