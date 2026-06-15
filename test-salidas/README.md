# Scripts de salidas por CAN sin candump

Estos scripts activan salidas por CAN usando GPIO17 de la Raspberry Pi.

## Importante

- No ejecutan `candump -tz can0`, por lo tanto el Python no queda pegado.
- No ejecutan `ip link set can0 down` si `can0` ya está levantado.
- Si `can0` está apagado, intentan levantarlo con:

```bash
ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
```

- Cada script `sX.py` prende la salida, espera 1 segundo y luego la apaga.
- Se mantiene GPIO17 encendido al terminar.

## Uso

```bash
chmod +x *.py
sudo python3 s8.py
```

## Script general

Pulso de 1 segundo:

```bash
sudo python3 control_salida.py s8 pulso
```

Encender solamente:

```bash
sudo python3 control_salida.py s8 on
```

Apagar solamente:

```bash
sudo python3 control_salida.py s8 off
```

Cambiar tiempo del pulso:

```bash
sudo python3 control_salida.py s8 pulso --tiempo 3
```

## Salidas incluidas

s1, s2, s3, s4, s5, s6, s7, s8, s9, s12, s13, s14, s15, s16, s17.
