import gcode_parser
from plotter import PenController, PenUpDown


def main():
    commands = gcode_parser.parse("test.gcode")
    pen_controller = PenController(pen_up_down=PenUpDown())
    for command in commands:
        if command["command"] == "pen_down":
            pen_controller.pen_down()
        elif command["command"] == "pen_up":
            pen_controller.pen_up()
        elif command["command"] in ["absolute_move", "relative_move"]:
            pos_mm = (command["X"] if "X" in command else None,
                      command["Y"] if "Y" in command else None)
            if command["command"] == "absolute_move":
                pen_controller.absolute_line_mm(goal_position_mm=pos_mm)
            else:
                pen_controller.relative_line_mm(goal_position_mm=pos_mm)
        else:
            raise RuntimeError(
                f"Unknown command {command['command']} with params {command}")


if __name__ == "__main__":
    main()
