#!/usr/bin/env python3
"""
pulso_s6.py

Script para activa por 5 segundos y apaga la salida S6.
No baja can0. Si can0 ya está UP, lo deja tal cual.
"""

from control_salida import controlar_salida

if __name__ == "__main__":
    controlar_salida("s6", "pulso", tiempo=5, candump=False)
