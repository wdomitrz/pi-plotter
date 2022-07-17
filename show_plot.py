import gcode_parser
import matplotlib.pyplot as plt


def scatter(xs, ys):
    plt.plot(xs, ys, ".-", color="black")


def main():
    commands = gcode_parser.parse("test.gcode")
    xs = [0]
    ys = [0]
    for command in commands:
        if command["command"] == "pen_down":
            xs = [xs[-1]]
            ys = [ys[-1]]
            scatter(xs, ys)
        elif command["command"] == "pen_up":
            scatter(xs, ys)
            xs = [xs[-1]]
            ys = [ys[-1]]
        elif command["command"] in ["absolute_move", "relative_move"]:

            pos_mm = (command["X"] if "X" in command else 0,
                      command["Y"] if "Y" in command else 0)
            if command["command"] == "absolute_move":
                xs.append(pos_mm[0])
                ys.append(pos_mm[1])
            else:
                xs.append(pos_mm[0] + xs[-1])
                ys.append(pos_mm[1] + ys[-1])
        else:
            raise RuntimeError(
                f"Unknown command {command['command']} with params {command}")
    scatter(xs, ys)
    plt.show()


if __name__ == "__main__":
    main()
