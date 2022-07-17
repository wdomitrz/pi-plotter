def parse(file_name):
    # Read lines
    with open(file_name, "r") as gcode_file:
        lines = gcode_file.read().splitlines()

    # Remove comments
    lines = [line.split(";")[0] for line in lines]
    # Split into commands
    lines = [line.split() for line in lines]

    commands = []
    absolute_move = False
    for line in lines:
        # Skip empty lines (and lines with only comments)
        if len(line) == 0:
            pass

        if line[0] in ["G00", "G01"]:
            # Move
            new_command = {}
            for param in line[1:]:
                if param[0] in ["E", "F", "S"]:
                    # Ignore unsupported commands
                    pass
                elif param[0] == "Z":
                    if float(param[1:]) < 1.5:
                        new_command["command"] = "pen_down"
                    else:
                        new_command["command"] = "pen_up"
                elif param[0] in ["X", "Y"]:
                    if absolute_move:
                        new_command["command"] = "absolute_move"
                    else:
                        new_command["command"] = "relative"
                    new_command[param[0]] = float(param[1:])
                else:
                    raise RuntimeError(
                        f"Unsupported parameter {param} to command {line[0]}")
            if "command" in new_command:
                commands.append(new_command)
        elif line[0] in ["G91"]:
            absolute_move = False
        elif line[0] in ["G90"]:
            absolute_move = True
        elif line[0] in ["G21"]:
            # Do nothing - set units to millimeters
            pass
        elif line[0] in ["G28"]:
            # Do nothing - auto home
            pass
        else:
            raise RuntimeError(
                f"Unknown Command {line[0]} with params {line[1:]}")

    return commands
