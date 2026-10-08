from parking_lot.pricing_strategy import PricingStrategy


class HourlyPricing(PricingStrategy):
    def __init__(self, hourly_rate: float = 50.0) -> None:
        self.hourly_rate = hourly_rate

    def get_price(self, hours: float) -> float:
        return self.hourly_rate * hours
