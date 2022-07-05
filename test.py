import sys
import time
from time import sleep

from gpiozero import OutputDevice as stepper
# from gpiozero import Servo

# # class Servo1:
# #     IN = 17

# servoGPIO = 17

# servo = Servo(servoGPIO)

# while True:

#     servo.min()
#     servo.mid()
#     print("mid")
#     sleep(0.5)
#     servo.max()
#     print("max")
#     sleep(1)
#     servo.min()


# 1
R_IN1 = stepper(14)
R_IN2 = stepper(15)
R_IN3 = stepper(18)
R_IN4 = stepper(23)

# 2
L_IN1 = stepper(24)
L_IN2 = stepper(25)
L_IN3 = stepper(8)
L_IN4 = stepper(7)


# IN1, IN2, IN3, IN4 = L_IN1, L_IN2, L_IN3, L_IN4
IN1, IN2, IN3, IN4 = R_IN1, R_IN2, R_IN3, R_IN4
stepPins = [IN1, IN2, IN3, IN4]  # Motor GPIO pins</p><p>
stepDir = -1        # Set to 1 for clockwise
# Set to -1 for anti-clockwise
# mode = 1            # mode = 1: Low Speed ==> Higher Power
mode = 0  # : High Speed == > Lower Power
if mode == 1:              # Low Speed ==> High Power
    seq = [[1, 0, 0, 1],  # Define step sequence as shown in manufacturers datasheet
           [1, 0, 0, 0],
           [1, 1, 0, 0],
           [0, 1, 0, 0],
           [0, 1, 1, 0],
           [0, 0, 1, 0],
           [0, 0, 1, 1],
           [0, 0, 0, 1]]
else:                    # High Speed ==> Low Power
    seq = [[1, 0, 0, 0],  # Define step sequence as shown in manufacturers datasheet
           [0, 1, 0, 0],
           [0, 0, 1, 0],
           [0, 0, 0, 1]]
stepCount = len(seq)
if len(sys.argv) > 1:  # Read wait time from command line
    waitTime = int(sys.argv[1]) / float(1000)
else:
    waitTime = 0.002    # 2 miliseconds was the maximun speed got on my tests
stepCounter = 0
while True:                          # Start main loop
    for pin in range(0, 4):
        xPin = stepPins[pin]          # Get GPIO
        if seq[stepCounter][pin] != 0:
            xPin.on()
        else:
            xPin.off()
    stepCounter += stepDir
    if (stepCounter >= stepCount):
        stepCounter = 0
    if (stepCounter < 0):
        stepCounter = stepCount + stepDir
    time.sleep(waitTime)     # Wait before moving on
