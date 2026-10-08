from dataclasses import dataclass
from uuid import UUID

from parking_lot.spot_type import SpotType


@dataclass
class ParkingSpot:
    spot_id: UUID
    spot_type: SpotType
    occupied: bool
    entry_time: int

    def __eq__(self, other: ParkingSpot) -> bool:
        return self.spot_id == other.spot_id

    def __hash__(self) -> int:
        return hash(self.spot_id)
