class ParkingLotError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"Error {code}: {message}")


class NoSpotsAvailable(ParkingLotError):
    def __init__(self, message: str = "") -> None:
        super().__init__(1001, "No parking spots available." + message)


class InvalidTicket(ParkingLotError):
    def __init__(self, message: str = "") -> None:
        super().__init__(1002, "Invalid Ticket" + message)
