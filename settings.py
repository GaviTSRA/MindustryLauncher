import os

class Settings:
    def __init__(self, file) -> None:
        self.file = file
        self.data_types = {
            "S": str,
            "I": int,
            "B": bool,
            "[": list
        }
        if not os.path.exists(file):
            with open(file, "w") as fi:
                fi.write("")

    def get(self, name, default):
        with open(self.file, "r") as fi:
            data = fi.readlines()
        with open(self.file, "r") as fi:
            old = fi.read()
        res = ""
        for line in data:
            if line.startswith(name+"="):
                res = line.split("=")[1].replace("\n","")

        if res == "":
            d = self.to_string(default)
            with open(self.file, "w") as fi:
                fi.write(f"{old}{name}={d}\n")
            return default

        return self.from_string(res)

    def set(self, name, value):
        with open(self.file, "r") as fi:
            data = fi.readlines()
        new_data = ""
        for line in data:    
            if not line.startswith(name+"=") and line != "\n":
                new_data += line
        with open(self.file, "w") as fi:
            fi.write(f"{new_data}{name}={self.to_string(value)}\n")

    def has(self, name):
        with open(self.file, "r") as fi:
            data = fi.readlines()
        for line in data:
            if line.startswith(name+"="):
                return True
        return False

    def to_string(self, value):
        if type(value) == int:
            return "I"+str(value)
        elif type(value) == bool:
            return "B" + ("true" if value else "false")
        elif type(value) == list:
            res = ""
            for val in value:
                res += self.to_string(val) + ","
            return "["+res.strip(",")+"]"
        else:
            return "S"+value

    def from_string(self, value):
        data_type = self.data_types[value[0]]
        value = value[1:]
        if data_type == int:
            return int(value)
        elif data_type == bool:
            return True if value == "true" else False
        elif data_type == list:
            result = []
            value = value[:-1]
            while len(value) > 1:
                if value == "]": break
                next = value.split(",")[0]
                if next.startswith("["):
                    next = "".join(value.split("]")[0]) + "]"
                    value = value[1:]
                value = value[len(next)+1:]
                result.append(self.from_string(next))
            return result
        return value
