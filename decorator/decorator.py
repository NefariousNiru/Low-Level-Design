from abc import abstractmethod, ABC


class Coffee(ABC):
    @abstractmethod
    def cost(self):
        pass

class BasicCoffee(Coffee):
    def cost(self):
        return 3.0


class CoffeeDecorator(Coffee):
    def __init__(self, coffee: Coffee):
        self.coffee = coffee

    def cost(self):
        return self.coffee.cost()


class MilkDecorator(CoffeeDecorator):
    def __init__(self, coffee: Coffee):
        super().__init__(coffee)
        self.coffee = coffee

    def cost(self):
        return self.coffee.cost() + 1


class MintDecorator(CoffeeDecorator):
    def __init__(self, coffee: Coffee):
        super().__init__(coffee)
        self.coffee = coffee

    def cost(self):
        return self.coffee.cost() + 5


class ChocoChipDecorator(CoffeeDecorator):
    def __init__(self, coffee: Coffee):
        super().__init__(coffee)
        self.coffee = coffee

    def cost(self):
        return self.coffee.cost() + 10


coffee = (
    MilkDecorator(
        MintDecorator(
            ChocoChipDecorator(
                BasicCoffee()
            )
        )
    )
)

print(coffee.cost())