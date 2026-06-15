# Scripts para activar/apagar salidas por CAN-FD

Estos scripts fueron generados usando tus comandos de:

- Activar salidas inj.txt
- Apagar salidas inj.txt

## Importante

Estos scripts **NO ejecutan**:

```bash
sudo ip link set can0 down
```

Esto es para no interrumpir lecturas paralelas, por ejemplo sensores.

Si `can0` ya está encendido, el script lo deja tal como está.
Si `can0` está apagado, intenta levantarlo con:

```bash
sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
```

También deja `GPIO17` en HIGH antes de mandar comandos CAN.

## Instalar dependencias

```bash
sudo apt update
sudo apt install -y can-utils python3-rpi.gpio
```

## Uso rápido

Entrar a la carpeta:

```bash
cd salidas_gpio_can
chmod +x *.py
```

Ejemplo salida 8 por 5 segundos:

```bash
sudo python3 s8.py
```

También puedes usar:

```bash
sudo python3 pulso_s8.py
```

Encender salida 8 sin apagarla automáticamente:

```bash
sudo python3 encender_s8.py
```

Apagar salida 8:

```bash
sudo python3 apagar_s8.py
```

## Script general

También puedes controlar cualquier salida con:

```bash
sudo python3 control_salida.py s8 pulso
sudo python3 control_salida.py s8 on
sudo python3 control_salida.py s8 off
```

Cambiar tiempo del pulso:

```bash
sudo python3 control_salida.py s8 pulso --tiempo 10
```

Correr candump mientras se ejecuta el pulso:

```bash
sudo python3 control_salida.py s8 pulso --candump
```

## Salidas disponibles

| Salida | Pin / timer según archivo de activar |
|---|---|
| S1 | PA10 / TIM1_CH3 |
| S2 | PA9 / TIM1_CH2 |
| S3 | PA8 / TIM1_CH1 |
| S4 | PC9 / TIM8_CH4 |
| S5 | PA0 / TIM2_CH1 |
| S6 | PA1 / TIM5_CH2 |
| S7 | PA2 / TIM15_CH1 |
| S8 | PA3 / TIM15_CH2 |
| S9 | PB1 / TIM3_CH4 |
| S12 | PB3 / TIM2_CH2 |
| S13 | PC6 / TIM3_CH1 |
| S14 | PD15 / TIM4_CH4 |
| S15 | PD14 / TIM4_CH3 |
| S16 | PB11 / TIM2_CH4 |
| S17 | PE14 / TIM1_CH4 |

## Archivos generados por salida

Para cada salida existen:

- `sX.py`: atajo para pulso de 5 segundos.
- `pulso_sX.py`: activa switch, enciende la salida, espera 5 segundos y apaga.
- `encender_sX.py`: activa switch y enciende la salida.
- `apagar_sX.py`: apaga la salida.

Donde `X` corresponde al número de salida, por ejemplo `s1`, `s8`, `s17`.

## Nota

No se generaron S10 ni S11 porque no aparecen en los archivos entregados.
