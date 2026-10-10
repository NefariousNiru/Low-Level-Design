from abc import abstractmethod, ABC


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class Light:
    def __init__(self):
        self.state = False

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False

class TurnOnCommand(Command):
    def __init__(self, light: Light):
        self.light = light

    def execute(self):
        self.light.turn_on()


class TurnOffCommand(Command):
    def __init__(self, light: Light):
        self.light = light

    def execute(self):
        self.light.turn_off()


class Button(Command):
    def __init__(self, command: Command):
        self.command = command

    def execute(self):
        self.command.execute()

light = Light()
print("Initial Light: ", light.state)
print("==============================")


button_on = Button(TurnOnCommand(light))
print("\nON BUTTON")
button_on.execute()
print(light.state)

print("\nOFF BUTTON")
button_off = Button(TurnOffCommand(light))
button_off.execute()
print(light.state)