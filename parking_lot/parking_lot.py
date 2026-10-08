import time
import uuid
from typing import Optional
from uuid import UUID

from parking_lot.errors import NoSpotsAvailable, InvalidTicket
from parking_lot.hourly_pricing import HourlyPricing
from parking_lot.parking_spot import ParkingSpot
from parking_lot.pricing_strategy import PricingStrategy
from parking_lot.ticket import Ticket
from parking_lot.vehicle_type import VehicleType


class ParkingLot:
    def __init__(
        self,
        spots: set[ParkingSpot],
        pricing_strategy: PricingStrategy = None,
    ) -> None:

        self.pricing_strategy = pricing_strategy or HourlyPricing()
        self.spots: set[ParkingSpot] = spots
        self.occupied_spots: dict[UUID, ParkingSpot] = {}
        self.active_tickets: dict[UUID, Ticket] = {}

    def enter(self, vehicle: VehicleType) -> Ticket:
        """Enter a vehicle into parking lot"""
        spot = self._find_spot(vehicle=vehicle)
        if not spot:
            raise NoSpotsAvailable()

        ticket = self._create_ticket(spot=spot, vehicle=vehicle)
        self.spots.remove(spot)
        self.occupied_spots[spot.spot_id] = spot
        self.active_tickets[ticket.ticket_id] = ticket
        return ticket

    def exit(self, ticket: Ticket) -> float:
        if ticket.ticket_id not in self.active_tickets:
            raise InvalidTicket()

        ticket_system = self.active_tickets[ticket.ticket_id]
        time_hours = (time.time() - ticket_system.entry_time) / 3600

        spot = self.occupied_spots[ticket_system.spot_id]
        spot.occupied = False
        self.spots.add(spot)

        del self.active_tickets[ticket_system.ticket_id]
        del self.occupied_spots[ticket_system.spot_id]

        return self.pricing_strategy.get_price(time_hours)

    def _find_spot(self, vehicle: VehicleType) -> Optional[ParkingSpot]:
        for spot in self.spots:
            if not spot.occupied and self._is_parking_spot_valid(
                vehicle=vehicle, spot=spot
            ):
                return spot
        return None

    @staticmethod
    def _create_ticket(spot: ParkingSpot, vehicle: VehicleType) -> Ticket:
        entry_ts = int(time.time())
        ticket_id = uuid.uuid4()
        ticket = Ticket(
            ticket_id=ticket_id,
            spot_id=spot.spot_id,
            vehicle_type=vehicle,
            spot_type=spot.spot_type,
            entry_time=entry_ts,
        )
        spot.occupied = True
        spot.entry_time = entry_ts
        return ticket

    @staticmethod
    def _is_parking_spot_valid(vehicle: VehicleType, spot: ParkingSpot) -> bool:
        return vehicle.value == spot.spot_type.value
