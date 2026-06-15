# Logger de todos los sensores SUCHAI por CAN-FD

Este script lee y guarda en un solo CSV:

- ICM-42688-V por ID `0x200`
- AK09940A por ID `0x201`
- INA260 3V3 por ID `0x202`
- INA260 BAT por ID `0x203`
- TMP102 por ID `0x204`

## Preparar CAN-FD

```bash
pip3 install python-can

sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
```

## Ejecutar

```bash
python3 all_sensors_logger.py --print
```

Guardar con nombre específico:

```bash
python3 all_sensors_logger.py --output ensayo_01.csv --print
```

Guardar sin imprimir todo:

```bash
python3 all_sensors_logger.py --output ensayo_01.csv
```

## Opciones útiles

No leer algún sensor:

```bash
python3 all_sensors_logger.py --no-ak --output sin_ak.csv
python3 all_sensors_logger.py --no-icm --output sin_icm.csv
python3 all_sensors_logger.py --no-ina --output sin_ina.csv
python3 all_sensors_logger.py --no-tmp102 --output sin_tmp.csv
```

No activar 1V8/G1/PE5 para el AK:

```bash
python3 all_sensors_logger.py --no-power-on-ak --print
```

Apagar 1V8 del AK al salir:

```bash
python3 all_sensors_logger.py --power-off-ak-exit --print
```

Ver mensajes crudos:

```bash
python3 all_sensors_logger.py --show-raw --print
```

## Columnas principales del CSV

Tiempo:

- `timestamp_iso`
- `epoch_s`
- `elapsed_s`

Identificación:

- `can_id`
- `sensor`
- `raw_text`

ICM:

- `ax_g`, `ay_g`, `az_g`
- `ax_ms2`, `ay_ms2`, `az_ms2`
- `gx_dps`, `gy_dps`, `gz_dps`
- `icm_temp_c`

AK:

- `mx_uT`, `my_uT`, `mz_uT`
- `mag_norm_uT`

INA:

- `current_mA`
- `voltage_mV`
- `voltage_V`
- `power_mW`

TMP102:

- `tmp102_temp_c`
