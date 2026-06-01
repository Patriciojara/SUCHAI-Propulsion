from gpiozero import PWMOutputDevice
from time import sleep

# Configura el GPIO 22 BCM, pin físico 15
pin = PWMOutputDevice(17, frequency=500)

# PWM al 10%
pin.value = 1
print("GPIO 22 con PWM: 500 Hz, duty 10%")

# Mantiene la señal por 3 segundos
sleep(10)

# Apaga la señal
pin.off()
print("GPIO 22 apagado")
#pin.on()
#print("GPIO 22 Encendido")
