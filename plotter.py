#!/usr/bin/env python3
from gpiozero import Servo
from gpiozero import OutputDevice as Stepper
import time


class PenUpDown:
    def __init__(self, pin=17, initial_state="Down"):
        self.pin = pin
        self.servo = Servo(self.pin)
        if initial_state == "Up":
            self.up()
        elif initial_state == "Down":
            self.down()

    def up(self):
        self.servo.max()

    def down(self):
        self.servo.min()


class Motor:
    DEFAULT_MOVE_SEQUENCE = [[1, 0, 0, 1],
                             [1, 0, 0, 0],
                             [1, 1, 0, 0],
                             [0, 1, 0, 0],
                             [0, 1, 1, 0],
                             [0, 0, 1, 0],
                             [0, 0, 1, 1],
                             [0, 0, 0, 1]]

    def __init__(self, pins, inverted, delay=0.002,
                 initial_position=0, move_sequence=None):
        self.pins = pins
        self.inverted = inverted
        self.current_position = initial_position
        self.delay = delay
        self.move_sequence = self.DEFAULT_MOVE_SEQUECE if move_sequence is None else move_sequence
        self.inputs = [Stepper(pin) for pin in self.pins]

    def go(self, *, n_steps, up=False, down=False, speed_mult=1, time_mult=1):
        assert(
            up != down), f"Expected exactly one from up={up} and down={down} to be True"

        step = 1 if up else -1
        step *= speed_mult

        sleep_time = time_mult * self.delay

        for _ in range(n_steps):
            self.current_position += step
            self.current_position %= len(self.move_sequence)

            for input, value in zip(
                    self.inputs, self.move_sequence[self.current_position]):
                if value == 0:
                    input.on()
                else:
                    input.off()
            time.sleep(sleep_time)


class DefaultLeftMotor(Motor):
    def __init__(self, pins=[24, 25, 8, 7], inverted=True):
        super().__init__(pins=pins, inverted=inverted)


class DefaultRightMotor(Motor):
    def __init__(self, pins=[14, 15, 18, 23], inverted=False):
        super().__init__(pins=pins, inverted=inverted)
