from abc import abstractmethod, ABC
from uuid import UUID


class Product:
    def __init__(self, id: UUID, name: str, price: float):
        self.id = id
        self.name = name
        self.price = price


class Stock:
    def __init__(self, id: UUID, product: Product, qty: int, low_stock_threshold: int):
        self.id = id
        self.product = product
        self.qty = qty
        self.low_stock_threshold = low_stock_threshold


class StockObserver(ABC):
    @abstractmethod
    def notify(self, stock: Stock, warehouse: Warehouse):
        pass

class EmailNotifier(StockObserver):
    def notify(self, stock: Stock, warehouse: Warehouse):
        pass


class SMSNotifier(StockObserver):
    def notify(self, stock: Stock, warehouse: Warehouse):
        pass


class Warehouse:
    def __init__(self, id, location: str, stocks: list[Stock]):
        self.id = id
        self.location = location
        self.stocks = {stock.id: stock for stock in stocks}

    def get_stock(self, stock_id: UUID) -> Stock:
        if stock_id not in self.stocks:
            raise Exception(f"No such stock: {stock_id}")
        return self.stocks[stock_id]


class InventoryManager:
    def __init__(self, warehouses: list[Warehouse], stock_observers: list[StockObserver]):
        self.warehouses = {warehouse.id: warehouse for warehouse in warehouses}
        self.stock_observers = stock_observers

    def get_stock(self, warehouse_id: UUID, stock_id: UUID):
        self._validate_warehouse(warehouse_id)
        warehouse = self.warehouses[warehouse_id]
        return warehouse.get_stock(stock_id=stock_id)

    def add_stock(self, warehouse_id: UUID, qty: int, stock_id: UUID):
        self._validate_qty(qty)
        stock = self.get_stock(warehouse_id=warehouse_id, stock_id=stock_id)
        stock.qty += qty

    def remove_stock(self, warehouse_id: UUID, stock_id: UUID, qty: int):
        self._validate_qty(qty)
        stock = self.get_stock(warehouse_id=warehouse_id, stock_id=stock_id)

        if stock.qty < qty:
            raise Exception(f"Cannot fulfill {qty} stocks. Available {stock.qty}")

        original_qty = stock.qty
        stock.qty -= qty

        if original_qty > stock.low_stock_threshold >= stock.qty:
            self.notify(stock=stock, warehouse=self.warehouses[warehouse_id])

    def transfer_stock(self, from_warehouse_id: UUID, to_warehouse_id: UUID, stock_id: UUID, qty: int):
        self._validate_qty(qty)

        from_stock = self.get_stock(from_warehouse_id, stock_id)
        to_stock = self.get_stock(to_warehouse_id, stock_id)

        if from_stock.qty < qty:
            raise Exception(f"Cannot fulfill {qty} stocks. Available {from_stock.qty}")

        original_from_stock_qty = from_stock.qty
        from_stock.qty -= qty
        to_stock.qty += qty

        if original_from_stock_qty > from_stock.low_stock_threshold >= from_stock.qty:
            self.notify(stock=from_stock, warehouse=self.warehouses[from_warehouse_id])

    def get_product_locations(self, stock_id: UUID):
        locations = []
        for warehouse_id in self.warehouses.keys():
            try:
                stock = self.get_stock(warehouse_id=warehouse_id, stock_id=stock_id)
                locations.append((self.warehouses[warehouse_id], stock))
            except Exception:
                continue
        return locations

    def notify(self, stock: Stock, warehouse: Warehouse):
        for observer in self.stock_observers:
            observer.notify(stock=stock, warehouse=warehouse)

    def add_observer(self, observer: StockObserver):
        self.stock_observers.append(observer)

    def remove_observer(self, observer: StockObserver):
        self.stock_observers.remove(observer)

    def _validate_warehouse(self, warehouse_id: UUID):
        if warehouse_id not in self.warehouses:
            raise Exception(f"Warehouse {warehouse_id} not found")

    @staticmethod
    def _validate_qty(qty: int):
        if qty <= 0:
            raise Exception(f"Qty must be greater than zero: {qty}")
