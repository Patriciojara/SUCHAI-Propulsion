#!/usr/bin/env python3
"""
apagar_s4.py

Script para apaga la salida S4.
No baja can0. Si can0 ya está UP, lo deja tal cual.
"""

from control_salida import controlar_salida

if __name__ == "__main__":
    controlar_salida("s4", "off", tiempo=5, candump=False)
