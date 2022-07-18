#!/usr/bin/env python3

import math
import time

from gpiozero import OutputDevice as Stepper
from gpiozero import Servo


class PenUpDown:
    def __init__(self, *, pin=17, start_up=False, start_down=False, delay=0.2):
        self.pin = pin
        self.delay = delay
        self.servo = Servo(self.pin)
        assert not (start_up and start_down), "Pen cannot start both up and down"
        if start_up:
            self.pen_up()
        elif start_down:
            self.pen_down()

    def __del__(self):
        self.pen_up()

    def pen_up(self):
        self.servo.max()
        time.sleep(self.delay)

    def pen_down(self):
        self.servo.min()
        time.sleep(self.delay)


class Motor:
    DEFAULT_MOVE_SEQUENCE = [
        [1, 0, 0, 1],
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
    ]

    def __init__(self, *, pins, inverted, initial_position=0, move_sequence=None):
        self.pins = pins
        self.inverted = inverted
        self.current_position = initial_position
        self.move_sequence = (
            self.DEFAULT_MOVE_SEQUENCE if move_sequence is None else move_sequence
        )
        self.inputs = [Stepper(pin) for pin in self.pins]

    def __del__(self):
        for motors_input in self.inputs:
            motors_input.off()

    def set_state(self, *, position):
        for motor_input, value in zip(self.inputs, position):
            if value == 0:
                motor_input.on()
            else:
                motor_input.off()

    def step(self, multiplier=1):

        step = -1 if self.inverted else 1
        step *= multiplier

        self.current_position += step
        self.current_position %= len(self.move_sequence)

        self.set_state(position=self.move_sequence[self.current_position])


class DefaultLeftMotor(Motor):
    def __init__(self, pins=(24, 25, 8, 7), inverted=True):
        super().__init__(pins=pins, inverted=inverted)


class DefaultRightMotor(Motor):
    def __init__(self, pins=(14, 15, 18, 23), inverted=False):
        super().__init__(pins=pins, inverted=inverted)


class CombinedMotors:
    def __init__(self, *, left=None, right=None, delay=0.003):
        self.left = left if left is not None else DefaultLeftMotor()
        self.right = right if right is not None else DefaultRightMotor()
        self.delay = delay

    def run(self, *, steps, speed_multiplier=1, time_multiplier=1):

        for left_step, right_step in steps:
            self.left.step(multiplier=left_step * speed_multiplier)
            self.right.step(multiplier=right_step * speed_multiplier)
            self.sleep(time_multiplier)
        self.sleep(time_multiplier)

    def sleep(self, time_multiplier=1):
        time.sleep(time_multiplier * self.delay)


def get_area_of_a_triangle(*, edges_lengths):
    """
    We use the Heron's formula here
    https://en.wikipedia.org/wiki/Heron%27s_formula
    """
    assert len(edges_lengths) == 3, "Triangle should have 3 edges"
    half_of_the_perimeter = sum(edges_lengths) / 2
    area = math.sqrt(
        math.prod(
            [half_of_the_perimeter]
            + [half_of_the_perimeter - edge_length for edge_length in edges_lengths]
        )
    )
    return area


def get_height_of_a_triangle_to_the_first_edge(*, edges_lengths):
    """
    We calculate a height of a triangle using its area
    """
    assert len(edges_lengths) == 3, "Triangle should have 3 edges"
    area = get_area_of_a_triangle(edges_lengths=edges_lengths)
    height = 2 * area / edges_lengths[0]
    return height


class PenController:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        *,
        motors=None,
        pen_up_down=None,
        mm_to_steps_scale=50,
        initial_strings_len_mm=(200, 200),
        distance_between_motors_mm=405,
        distance_between_mounting_points_mm=75,
        time_multiplier=1,
        speed_multiplier=1
    ):
        """
        mm_to_steps_scale=50 means that 50 steps is ~1mm
        """
        self.motors = motors if motors is not None else CombinedMotors()
        self.pen_up_down = pen_up_down
        self.speed_multiplier = speed_multiplier
        self.time_multiplier = time_multiplier
        self.mm_to_steps_scale = mm_to_steps_scale / speed_multiplier
        self.distance_between_motors_mm = distance_between_motors_mm
        self.initial_strings_len_mm = initial_strings_len_mm
        self.distance_between_mounting_points_mm = distance_between_mounting_points_mm
        self.initial_height = get_height_of_a_triangle_to_the_first_edge(
            edges_lengths=[
                self.distance_between_motors_mm
                - self.distance_between_mounting_points_mm,
                *self.initial_strings_len_mm,
            ]
        )
        self.current_strings_len_mm = self.initial_strings_len_mm
        self.current_position_mm = self.strings_to_position_mm(
            strings_len_mm=self.current_strings_len_mm
        )

    def __del__(self):
        self.pen_up()
        self.absolute_line_mm(goal_position_mm=(0, 0))

    def mm_to_steps(self, millimeters):
        return int(millimeters * self.mm_to_steps_scale)

    def steps_to_mm(self, steps):
        return steps / self.mm_to_steps_scale

    def strings_to_position_mm(self, *, strings_len_mm):
        # We calculate a height of a triangle using its area
        height_mm = get_height_of_a_triangle_to_the_first_edge(
            edges_lengths=[
                self.distance_between_motors_mm
                - self.distance_between_mounting_points_mm,
                *strings_len_mm,
            ]
        )
        position_y_mm = height_mm - self.initial_height
        position_x_mm = (
            self.distance_between_motors_mm - self.distance_between_mounting_points_mm
        ) / 2 - math.sqrt(strings_len_mm[0] ** 2 - height_mm**2)
        return position_x_mm, position_y_mm

    def position_to_strings_mm(self, *, position_mm):
        position_x_mm, position_y_mm = position_mm

        left_triangle_upper_edge_len_mm = (
            self.distance_between_motors_mm - self.distance_between_mounting_points_mm
        ) / 2 + position_x_mm

        right_triangle_upper_edge_len_mm = (
            self.distance_between_motors_mm - self.distance_between_mounting_points_mm
        ) / 2 - position_x_mm

        height_mm = position_y_mm + self.initial_height

        strings_lengths = tuple(
            math.sqrt(upper_edge_len_mm**2 + height_mm**2)
            for upper_edge_len_mm in (
                left_triangle_upper_edge_len_mm,
                right_triangle_upper_edge_len_mm,
            )
        )

        return strings_lengths

    def relative_line_mm(self, *, goal_position_mm):
        goal_position_mm = tuple(
            relative_pos if relative_pos is not None else 0
            for relative_pos in goal_position_mm
        )
        absolute_goal_position_mm = tuple(
            map(sum, zip(goal_position_mm, self.current_position_mm))
        )
        return self.absolute_line_mm(goal_position_mm=absolute_goal_position_mm)

    def absolute_line_mm(self, *, goal_position_mm):
        goal_position_mm = tuple(
            absolute_pos if absolute_pos is not None else current_pos
            for absolute_pos, current_pos in zip(
                goal_position_mm, self.current_position_mm
            )
        )
        goal_strings_len_mm = self.position_to_strings_mm(position_mm=goal_position_mm)

        return self.move_to_strings_position_mm(
            goal_strings_len_mm=goal_strings_len_mm, goal_position_mm=goal_position_mm
        )

    def move_to_strings_position_mm(
        self, *, goal_strings_len_mm, goal_position_mm=None
    ):

        strings_len_difference_mm = tuple(
            map(
                lambda current_goal: current_goal[1] - current_goal[0],
                zip(self.current_strings_len_mm, goal_strings_len_mm),
            )
        )
        strings_len_difference_steps = tuple(
            map(self.mm_to_steps, strings_len_difference_mm)
        )

        number_of_steps = max(map(abs, strings_len_difference_steps))
        number_of_done_steps = [0 for _ in range(len(strings_len_difference_steps))]
        steps = []
        for step_number in range(number_of_steps):
            step = []
            for i, total_steps_number in enumerate(strings_len_difference_steps):
                if (
                    step_number * abs(total_steps_number) / number_of_steps
                    >= number_of_done_steps[i]
                ):
                    step.append(1)
                    number_of_done_steps[i] += 1
                else:
                    step.append(0)
                if total_steps_number < 0:
                    step[i] *= -1
            steps.append(tuple(step))

        self.execute_steps(steps=steps)

        return self.set_current_position(
            strings_len_mm=goal_strings_len_mm, position_mm=goal_position_mm
        )

    def execute_steps(self, *, steps):
        self.motors.run(
            steps=steps,
            speed_multiplier=self.speed_multiplier,
            time_multiplier=self.time_multiplier,
        )

    def set_current_position(self, *, strings_len_mm=None, position_mm=None):
        assert not (
            strings_len_mm is None and position_mm is None
        ), "Position has to be specified by at least strings length or Cartesian coordinates"

        self.current_strings_len_mm = (
            strings_len_mm
            if strings_len_mm is not None
            else self.position_to_strings_mm(position_mm=position_mm)
        )
        self.current_position_mm = (
            position_mm
            if position_mm is not None
            else self.strings_to_position_mm(strings_len_mm=strings_len_mm)
        )

    def go_to_mm(self, position_mm):
        return self.absolute_line_mm(goal_position_mm=position_mm)

    def pen_down(self):
        self.pen_up_down.down()

    def pen_up(self):
        self.pen_up_down.up()
