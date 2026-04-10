import spidev
import time

SPI_BUS = 0
SPI_DEVICE = 0

CMD_SET_DUTY_PA10 = 0xA0
CMD_PWM_OFF_PA10  = 0xA1
CMD_SET_DUTY_PA8  = 0xB0
CMD_PWM_OFF_PA8   = 0xB1
CMD_SET_FREQ      = 0xA2

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = 100000
spi.mode = 0

def send_command_with_response(cmd, d1, d2):
    # 1) Enviamos comando
    spi.xfer2([cmd, d1, d2])

    # 2) Ahora leemos la respuesta (STM manda lo que preparó en el callback)
    resp = spi.xfer2([0x00, 0x00, 0x00])
    print(f"Respuesta STM: {resp}")  # [cmd_recibido, duty_ch1, duty_ch3]
    return resp

def set_duty_pa10(duty):
    duty = max(0, min(100, int(duty)))
    return send_command_with_response(CMD_SET_DUTY_PA10, duty, 0)

def off_pa10():
    return send_command_with_response(CMD_PWM_OFF_PA10, 0, 0)

def set_duty_pa8(duty):
    duty = max(0, min(100, int(duty)))
    return send_command_with_response(CMD_SET_DUTY_PA8, duty, 0)

def off_pa8():
    return send_command_with_response(CMD_PWM_OFF_PA8, 0, 0)

def set_freq(freq_hz):
    freq_hz = max(20, min(20000, int(freq_hz)))
    hi = (freq_hz >> 8) & 0xFF
    lo = freq_hz & 0xFF
    return send_command_with_response(CMD_SET_FREQ, hi, lo)

def main():
    print("Comandos:")
    print("  d10=NN   -> duty PA10")
    print("  d8=NN    -> duty PA8")
    print("  off10    -> OFF PA10")
    print("  off8     -> OFF PA8")
    print("  f=NNNN   -> frecuencia Hz")
    print("  q        -> salir")

    while True:
        s = input("> ").strip().lower()
        if s == "q":
            break
        elif s.startswith("d10="):
            set_duty_pa10(int(s[4:]))
        elif s.startswith("d8="):
            set_duty_pa8(int(s[3:]))
        elif s == "off10":
            off_pa10()
        elif s == "off8":
            off_pa8()
        elif s.startswith("f="):
            set_freq(int(s[2:]))
        else:
            print("Comandos no válidos.")

if __name__ == "__main__":
    main()
