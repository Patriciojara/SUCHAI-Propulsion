#!/usr/bin/env python3
"""
s12.py

Atajo: activa S12 por 5 segundos y luego la apaga.
No baja can0. Si can0 ya está UP, lo deja tal cual.
"""

from control_salida import controlar_salida

if __name__ == "__main__":
    controlar_salida("s12", "pulso", tiempo=5, candump=False)
