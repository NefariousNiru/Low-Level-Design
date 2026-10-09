from enum import IntEnum
from functools import lru_cache


class Denomination(IntEnum):
    ONE = 1
    TEN = 10
    TWENTY = 20
    FIFTY = 50
    HUNDRED = 100


class CashStock:
    def __init__(self, stock: dict[Denomination, int]):
        self.stock = stock

    def withdraw(self, amount: int) -> dict[Denomination, int]:

        @lru_cache(maxsize=None)
        def solve(i: int, remaining: int):
            if remaining == 0:
                return {}

            if i == len(denominations):
                return None

            denom = denominations[i]
            available = self.stock[denom]

            max_usable = min(available, remaining // denom.value)
            for use in range(max_usable, -1, -1):
                ret = solve(i + 1, remaining - (use * denom.value))
                if ret is not None:
                    return {**ret, denom: use}

            return None

        denominations = sorted(self.stock.keys(), reverse=True)
        result = solve(0, amount)
        print(solve.cache_info())
        if not result:
            raise Exception(f"Not enough cash")

        for denomination, count in sorted(result.items()):
            self.stock[denomination] -= count

        return result

    def restock(self, stock: dict[Denomination, int]):
        for denomination, count in stock.items():
            self.stock[denomination] += count


class ATM:
    def __init__(self, cash_stock: CashStock):
        self.cash_stock = cash_stock

    def withdraw(self, amount: int) -> dict[Denomination, int]:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return self.cash_stock.withdraw(amount)

    def restock(self, stock: dict[Denomination, int]) -> None:
        self.cash_stock.restock(stock)


atm = ATM(
    CashStock({
        Denomination.HUNDRED: 3,
        Denomination.FIFTY: 2,
        Denomination.TWENTY: 5,
        Denomination.TEN: 10,
        Denomination.ONE: 20,
    })
)

val = atm.withdraw(200)
print("\nOutput")
print(val)
