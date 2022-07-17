#!/usr/bin/env python3
# %%

import math
import time

from gpiozero import OutputDevice as Stepper
from gpiozero import Servo


class PenUpDown:
    def __init__(self, *, pin=17, start_up=False, start_down=False, delay=0.2):
        self.pin = pin
        self.delay = delay
        self.servo = Servo(self.pin)
        assert(not(start_up and start_down)
               ), "Pen cannot start both up and down"
        if start_up:
            self.up()
        elif start_down:
            self.down()

    def __del__(self):
        self.up()

    def up(self):
        self.servo.max()
        time.sleep(self.delay)

    def down(self):
        self.servo.min()
        time.sleep(self.delay)


class Motor:
    DEFAULT_MOVE_SEQUENCE = [[1, 0, 0, 1],
                             [1, 0, 0, 0],
                             [1, 1, 0, 0],
                             [0, 1, 0, 0],
                             [0, 1, 1, 0],
                             [0, 0, 1, 0],
                             [0, 0, 1, 1],
                             [0, 0, 0, 1]]

    def __init__(self, *, pins, inverted,
                 initial_position=0, move_sequence=None):
        self.pins = pins
        self.inverted = inverted
        self.current_position = initial_position
        self.move_sequence = self.DEFAULT_MOVE_SEQUENCE if move_sequence is None else move_sequence
        self.inputs = [Stepper(pin) for pin in self.pins]

    def __del__(self):
        for input in self.inputs:
            input.off()

    def to(self, *, position):
        for input, value in zip(self.inputs, position):
            if value == 0:
                input.on()
            else:
                input.off()

    def step(self, multiplier=1):

        step = -1 if self.inverted else 1
        step *= multiplier

        self.current_position += step
        self.current_position %= len(self.move_sequence)

        self.to(position=self.move_sequence[self.current_position])


class DefaultLeftMotor(Motor):
    def __init__(self, pins=[24, 25, 8, 7], inverted=False):
        super().__init__(pins=pins, inverted=inverted)


class DefaultRightMotor(Motor):
    def __init__(self, pins=[14, 15, 18, 23], inverted=True):
        super().__init__(pins=pins, inverted=inverted)


class CombinedMotors:
    def __init__(self, *, left, right, delay=0.003):
        self.left = left
        self.right = right
        self.delay = delay

    def go(self, *, steps, speed_mult=1, time_mult=1):
        sleep_time = time_mult * self.delay

        for left_step, right_step in steps:
            self.left.step(multiplier=left_step * speed_mult)
            self.right.step(multiplier=right_step * speed_mult)
            time.sleep(sleep_time)


def get_area_of_a_triengle(*, edges_lengths):
    """
    We use the Heron's formula here
    https://en.wikipedia.org/wiki/Heron%27s_formula
    """
    assert(len(edges_lengths) == 3), "Triangle should have 3 edges"
    half_of_the_perimeter = sum(edges_lengths) / 2
    area = math.sqrt(math.prod(
        [half_of_the_perimeter] + [half_of_the_perimeter - edge_length for edge_length in edges_lengths]))
    return area


def get_height_of_a_triange_to_the_first_edge(*, edges_lengths):
    """
    We calculate a height of a triangle using its area
    """
    assert(len(edges_lengths) == 3), "Triangle should have 3 edges"
    area = get_area_of_a_triengle(edges_lengths=edges_lengths)
    height = 2 * area / edges_lengths[0]
    return height


class PenController:
    def __init__(self, *, motors: CombinedMotors, pen_up_down=None, cm_to_steps_scale=500,
                 initial_strings_len_cm=(20, 20), distance_between_motors_cm=40.5, distance_between_mounting_points_cm=7.5, time_mult=1, speed_mult=1):
        """
        cm_to_steps_scale=500 means that 500 steps is ~1cm
        """
        self.motors = motors
        self.pen_up_down = pen_up_down
        self.speed_mult = speed_mult
        self.time_mult = time_mult
        self.cm_to_steps_scale = cm_to_steps_scale / speed_mult
        self.distance_between_motors_cm = distance_between_motors_cm
        self.initial_strings_len_cm = initial_strings_len_cm
        self.distance_between_mounting_points_cm = distance_between_mounting_points_cm
        self.initial_height = get_height_of_a_triange_to_the_first_edge(
            edges_lengths=[
                self.distance_between_motors_cm -
                self.distance_between_mounting_points_cm,
                *
                self.initial_strings_len_cm])
        self.current_strings_len_cm = self.initial_strings_len_cm
        self.current_position_cm = self.strings_to_position_cm(
            strings_len_cm=self.current_strings_len_cm)

    def cm_to_steps(self, n):
        return int(n * self.cm_to_steps_scale)

    def steps_to_cm(self, n):
        return n / self.cm_to_steps_scale

    def strings_to_position_cm(self, *, strings_len_cm):
        # We calculate a height of a triangle using its area
        height_cm = get_height_of_a_triange_to_the_first_edge(
            edges_lengths=[
                self.distance_between_motors_cm -
                self.distance_between_mounting_points_cm,
                *
                strings_len_cm])
        position_y_cm = height_cm - self.initial_height
        position_x_cm = (
            self.distance_between_motors_cm - self.distance_between_mounting_points_cm) / 2 - math.sqrt(
            strings_len_cm[0]**2 - height_cm**2)
        return position_x_cm, position_y_cm

    def position_to_strings_cm(self, *, position_cm):
        position_x_cm, position_y_cm = position_cm

        left_triangle_upper_edge_len_cm = (
            self.distance_between_motors_cm - self.distance_between_mounting_points_cm) / 2 + position_x_cm

        right_triangle_upper_edge_len_cm = (
            self.distance_between_motors_cm - self.distance_between_mounting_points_cm) / 2 - position_x_cm

        height_cm = position_y_cm + self.initial_height

        strings_lengths = tuple(
            math.sqrt(
                upper_edge_len_cm ** 2 + height_cm ** 2) for upper_edge_len_cm in (
                left_triangle_upper_edge_len_cm,
                right_triangle_upper_edge_len_cm))

        return strings_lengths

    def relative_line_cm(self, *, goal_position_cm):
        absolute_goal_position_cm = tuple(
            current_pos +
            relative_pos for current_pos,
            relative_pos in zip(
                self.current_position_cm,
                goal_position_cm))
        return self.absolute_line_cm(
            goal_position_cm=absolute_goal_position_cm)

    def absolute_line_cm(self, *, goal_position_cm):
        goal_strings_len_cm = self.position_to_strings_cm(
            position_cm=goal_position_cm)

        return self.move_to_strings_position_cm(
            goal_strings_len_cm=goal_strings_len_cm, goal_position_cm=goal_position_cm)

    def move_to_strings_position_cm(
            self, *, goal_strings_len_cm, goal_position_cm=None):

        strings_len_difference_cm = tuple(map(
            lambda current_goal: current_goal[1] - current_goal[0], zip(
                self.current_strings_len_cm, goal_strings_len_cm)))
        strings_len_difference_steps = tuple(
            map(self.cm_to_steps, strings_len_difference_cm))

        number_of_steps = max(map(abs, strings_len_difference_steps))
        number_of_done_steps = [
            0 for _ in range(
                len(strings_len_difference_steps))]
        steps = []
        for step_number in range(number_of_steps):
            step = []
            for i, total_steps_number in enumerate(
                    strings_len_difference_steps):
                if step_number * abs(total_steps_number) / \
                        number_of_steps >= number_of_done_steps[i]:
                    step.append(1)
                    number_of_done_steps[i] += 1
                else:
                    step.append(0)
                if total_steps_number < 0:
                    step[i] *= -1
            steps.append(tuple(step))

        self.execute_steps(steps=steps)

        return self.set_current_position(
            strings_len_cm=goal_strings_len_cm, position_cm=goal_position_cm)

    def execute_steps(self, *, steps):
        self.motors.go(
            steps=steps,
            speed_mult=self.speed_mult,
            time_mult=self.time_mult)

    def set_current_position(self, *, strings_len_cm=None, position_cm=None):
        assert(not(strings_len_cm is None and position_cm is None)
               ), "Position has to be specified by at least strings length or Cartesian coordinates"

        self.current_strings_len_cm = strings_len_cm if strings_len_cm is not None else self.position_to_strings_cm(
            position_cm=position_cm)
        self.current_position_cm = position_cm if position_cm is not None else self.strings_to_position_cm(
            strings_len_cm=strings_len_cm)

    def go_to_cm(self, position_cm):
        target_x_cm, target_y_cm = position_cm

    def pen_down(self):
        self.pen_up_down.down()

    def pen_up(self):
        self.pen_up_down.up()

# %%
