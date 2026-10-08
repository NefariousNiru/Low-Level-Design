class Product:
    def __init__(self, id: str, price: float):
        self.id = id
        self.price = price


class Stock:
    def __init__(self, product: Product, qty: int):
        self.product = product
        self.qty = qty


class Catalog:
    def __init__(self, products: dict[str, Stock]):
        self.products = products


class Order:
    def __init__(self, product, change: float):
        self.product = product
        self.change = change


class VendingMachineState:
    def select_item(self, machine: "VendingMachine", selection_key: str) -> float:
        raise Exception("Invalid State")

    def purchase(self, machine: "VendingMachine") -> Order:
        raise Exception("Invalid State")

    def insert_money(self, machine: "VendingMachine", amount: float) -> float:
        raise Exception("Invalid State")


class IdleState(VendingMachineState):
    def select_item(self, machine: "VendingMachine", selection_key: str) -> float:
        return machine._select_item(selection_key)


class SelectedState(VendingMachineState):
    def select_item(self, machine: "VendingMachine", selection_key: str) -> float:
        return machine._select_item(selection_key)

    def insert_money(self, machine: "VendingMachine", amount: float) -> float:
        return machine._insert_money(amount)


class TransactionState(VendingMachineState):
    def insert_money(self, machine: "VendingMachine", amount: float) -> float:
        return machine._insert_money(amount)

    def purchase(self, machine: "VendingMachine") -> Order:
        return machine._purchase()


class VendingMachine:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.state = IdleState()
        self.product: Product | None = None
        self.amount = 0.0
        self.selection_key: str = None

    def select_item(self, selection_key: str) -> float:
        return self.state.select_item(self, selection_key)

    def purchase(self) -> Order:
        return self.state.purchase(self)

    def insert_money(self, amount: float) -> float:
        return self.state.insert_money(self, amount)

    def cancel_item(self) -> float:
        """Cancels item and returns accepted money"""
        amount = self.amount
        self.reset()
        return amount

    def restock(self, selection_key: str, qty: int) -> None:
        if selection_key not in self.catalog.products:
            raise ValueError("Invalid selection")

        if qty <= 0:
            raise ValueError("Quantity must be positive")

        self.catalog.products[selection_key].qty += qty

    def reset(self):
        self.state = IdleState()
        self.product = None
        self.amount = 0.0
        self.selection_key = None

    def set_state(self, state: VendingMachineState) -> None:
        self.state = state

    # Private methods called by states
    def _select_item(self, selection_key: str) -> float:
        if selection_key not in self.catalog.products:
            raise Exception("Invalid Selection")

        stock = self.catalog.products[selection_key]
        if stock.qty == 0:
            raise Exception("Out of Stock")

        self.selection_key = selection_key
        self.product = stock.product
        self.set_state(SelectedState())
        return self.product.price

    def _insert_money(self, amount: float) -> float:
        """Adds money to total and returns pending amount"""
        if amount <= 0:
            raise Exception("Amount cannot be negative")

        self.set_state(TransactionState())
        self.amount += amount
        return self.product.price - self.amount

    def _purchase(self) -> Order:
        if self.amount < self.product.price:
            raise Exception(f"Please insert ${self.product.price - self.amount} more.")

        change = self.amount - self.product.price
        product = Product(self.product.id, self.product.price)
        self.catalog.products[self.selection_key].qty -= 1

        self.reset()
        return Order(product, change)