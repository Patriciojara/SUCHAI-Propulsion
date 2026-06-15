# Loggers independientes SUCHAI STM32 CAN-FD

## Preparación

```bash
pip3 install python-can
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
```

## ICM-42688-V

```bash
python3 icm42688_logger.py --print
python3 icm42688_logger.py --output icm_test.csv
```

## AK09940A

El script activa automáticamente G1/PE5, usado como ON 1V8, antes de leer el AK.

```bash
python3 ak09940a_logger.py --print
python3 ak09940a_logger.py --output ak_test.csv
python3 ak09940a_logger.py --no-power-on --print
python3 ak09940a_logger.py --power-off-exit --print
```

## INA260

```bash
python3 ina260_logger.py --print
python3 ina260_logger.py --sensor 3v3 --output ina3v3.csv
python3 ina260_logger.py --sensor bat --output inabat.csv
python3 ina260_logger.py --sensor both --output ina_both.csv
```

## TMP102

```bash
python3 tmp102_logger.py --print
python3 tmp102_logger.py --output tmp102.csv
```

Todos los CSV incluyen timestamp_iso, epoch_s y elapsed_s para graficar y comparar ensayos.
