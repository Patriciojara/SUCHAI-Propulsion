#!/usr/bin/env python3
"""
s1.py

Atajo: activa S1 por 5 segundos y luego la apaga.
No baja can0. Si can0 ya está UP, lo deja tal cual.
"""

from control_salida import controlar_salida

if __name__ == "__main__":
    controlar_salida("s1", "pulso", tiempo=5, candump=False)
