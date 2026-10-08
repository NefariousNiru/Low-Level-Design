import time
import uuid
from abc import ABC, abstractmethod
from enum import StrEnum
from uuid import UUID


class PizzaBase(StrEnum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"


class ToppingQty(StrEnum):
    LESS = "Less"
    NORMAL = "Normal"
    EXTRA = "Extra"


class Pizza:
    def __init__(self, base: PizzaBase):
        self.base = base
        self.toppings: dict[str, ToppingQty] = {}


class Pricing(ABC):
    @abstractmethod
    def get_price(self, item: PizzaBase | tuple[str, ToppingQty]) -> float:
        pass


class SimplePricing(Pricing):
    def __init__(self, topping_prices: dict[str, float], base_prices: dict[PizzaBase, float], topping_qty_multiplier: dict[ToppingQty, float]):
        self.topping_prices = topping_prices
        self.base_prices = base_prices
        self.topping_qty_multiplier = topping_qty_multiplier

    def get_price(self, item: PizzaBase | tuple[str, ToppingQty]) -> float:
        if isinstance(item, PizzaBase):
            return self.base_prices[item]
        topping, qty = item
        return self.topping_prices[topping] * self.topping_qty_multiplier[qty]


class Order:
    def __init__(self, bill_id: UUID, pizza: Pizza, price: float):
        self.bill_id = bill_id
        self.pizza = pizza
        self.price = price

class PizzaManagement:
    def __init__(self,
             topping_prices: dict[str, float],
             topping_qty_multiplier: dict[ToppingQty, float],
             base_prices: dict[PizzaBase, float],
             pricing: Pricing = None,
        ):
        self.pricing = pricing or SimplePricing(
            topping_prices=topping_prices,
            base_prices=base_prices,
            topping_qty_multiplier=topping_qty_multiplier
        )
        self.orders: dict[UUID, Order] = {}

    def finalize(self, bill_id: UUID) -> Order:
        self._check_valid_bill(bill_id)

        pizza_order = self.orders[bill_id]

        # Prepping
        time.sleep(5)
        del self.orders[bill_id]

        return pizza_order

    def place_new_order(self, base: PizzaBase) -> dict:
        bill_id = uuid.uuid4()
        pizza = Pizza(base=base)
        price = self.pricing.get_price(item=base)

        new_order = Order(bill_id=bill_id, pizza=pizza, price=price)
        self.orders[bill_id] = new_order

        return {"bill_id": bill_id, "price": price}

    def update_base(self, bill_id: UUID, new_base: PizzaBase) -> float:
        self._check_valid_bill(bill_id)

        order = self.orders[bill_id]
        old_base_price = self.pricing.get_price(item=order.pizza.base)
        new_base_price = self.pricing.get_price(item=new_base)

        order.pizza.base = new_base
        order.price -= old_base_price
        order.price += new_base_price

        return order.price

    def cancel_order(self, bill_id: UUID) -> float:
        self._check_valid_bill(bill_id)
        del self.orders[bill_id]
        return 0.0

    def add_topping(self, bill_id: UUID, topping: str, topping_qty: ToppingQty) -> float:
        self._check_valid_bill(bill_id)

        order = self.orders[bill_id]

        if topping in order.pizza.toppings:
            raise Exception("Topping already added")

        order.pizza.toppings[topping] = topping_qty
        order.price += self.pricing.get_price(item=(topping, topping_qty))

        return order.price

    def remove_topping(self, bill_id: UUID, topping: str) -> float:
        self._check_valid_bill(bill_id)

        order = self.orders[bill_id]

        if topping not in order.pizza.toppings:
            raise Exception("Topping not present")

        qty = order.pizza.toppings[topping]
        order.price -= self.pricing.get_price(item=(topping, qty))
        del order.pizza.toppings[topping]

        return order.price

    def update_topping_qty(self, bill_id: UUID, topping: str, new_topping_qty: ToppingQty) -> float:
        self._check_valid_bill(bill_id)

        order = self.orders[bill_id]
        if topping not in order.pizza.toppings:
            raise Exception("Topping not present")

        old_topping_price = self.pricing.get_price((topping, order.pizza.toppings[topping]))
        new_topping_price = self.pricing.get_price((topping, new_topping_qty))

        order.pizza.toppings[topping] = new_topping_qty
        order.price -= old_topping_price
        order.price += new_topping_price

        return order.price

    def _check_valid_bill(self, bill_id: UUID):
        if bill_id not in self.orders:
            raise Exception(f"No such pizza order: {bill_id}. Start by adding a base")