# LEDs lenteja por CAN

Scripts para controlar los LEDs de lenteja:

- Rojo: PB13 / G4
- Blanco: PE8 / G5
- Azul: PE4 / G6

## Secuencia que hacen los scripts

1. Encienden `GPIO17` de la Raspberry Pi.
2. Revisan si `can0` está levantado.
3. Si `can0` ya está UP, no lo bajan ni lo reinician.
4. Si `can0` está apagado, lo levantan con:

```bash
ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
```

5. No ejecutan `candump -tz can0`, para que Python no quede pegado.
6. Activan 3V3 desde la placa:

```bash
cansend can0 100##1300201
```

7. Ejecutan la acción del LED: `on`, `off`, `toggle` o `get`.

## Uso con script general

```bash
sudo python3 led_lenteja.py rojo on
sudo python3 led_lenteja.py rojo off
sudo python3 led_lenteja.py rojo toggle
sudo python3 led_lenteja.py rojo get
```

```bash
sudo python3 led_lenteja.py blanco on
sudo python3 led_lenteja.py blanco off
sudo python3 led_lenteja.py blanco toggle
sudo python3 led_lenteja.py blanco get
```

```bash
sudo python3 led_lenteja.py azul on
sudo python3 led_lenteja.py azul off
sudo python3 led_lenteja.py azul toggle
sudo python3 led_lenteja.py azul get
```

## Uso con scripts directos

```bash
sudo python3 rojo_on.py
sudo python3 rojo_off.py
sudo python3 rojo_toggle.py
sudo python3 rojo_get.py
```

```bash
sudo python3 blanco_on.py
sudo python3 blanco_off.py
sudo python3 blanco_toggle.py
sudo python3 blanco_get.py
```

```bash
sudo python3 azul_on.py
sudo python3 azul_off.py
sudo python3 azul_toggle.py
sudo python3 azul_get.py
```

## Comandos usados

### Rojo / PB13 / G4

```bash
cansend can0 100##1300401   # ON
cansend can0 100##1300400   # OFF
cansend can0 100##13104     # TOGGLE
cansend can0 100##13204     # GET
```

### Blanco / PE8 / G5

```bash
cansend can0 100##1300501   # ON
cansend can0 100##1300500   # OFF
cansend can0 100##13105     # TOGGLE
cansend can0 100##13205     # GET
```

### Azul / PE4 / G6

```bash
cansend can0 100##1300601   # ON
cansend can0 100##1300600   # OFF
cansend can0 100##13106     # TOGGLE
cansend can0 100##13206     # GET
```

## Importante

Si quieres ver el tráfico CAN, ejecuta esto en otra terminal:

```bash
candump -tz can0
```

No se incluye dentro de los scripts para evitar que el Python quede detenido.
