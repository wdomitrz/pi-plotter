import matplotlib.pyplot as plt

import gcode_parser


def scatter(pos):
    pos_x, pos_y = zip(*pos)
    plt.plot(pos_x, pos_y, ".-", color="black")


def main():
    commands = gcode_parser.parse("test.gcode")
    pos = [(0, 0)]
    for command in commands:
        if command["command"] == "pen_down":
            pos = [pos[-1]]
        elif command["command"] == "pen_up":
            scatter(pos)
            pos = [pos[-1]]
        elif command["command"] in ["absolute_move", "relative_move"]:

            last_pos = (
                command["X"] if "X" in command else 0,
                command["Y"] if "Y" in command else 0,
            )
            if command["command"] == "relative_move":
                last_pos = tuple(map(sum, zip(last_pos, pos[-1])))
            pos.append(last_pos)
        else:
            raise RuntimeError(
                f"Unknown command {command['command']} with params {command}"
            )
    scatter(pos)
    plt.show()


if __name__ == "__main__":
    main()
