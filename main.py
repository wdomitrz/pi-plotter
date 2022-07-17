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
        elif command["command"] == "absolute_move":
            pen_controller.absolute_line_mm(command["X"], command["Y"])
        elif command["command"] == "relative_move":
            pen_controller.relative_line_mm(command["X"], command["Y"])
        else:
            raise RuntimeError(
                f"Unknown command {command['command']} with params {command}")


if __name__ == "__main__":
    main()
