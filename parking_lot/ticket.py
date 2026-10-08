from dataclasses import dataclass
from uuid import UUID


@dataclass
class Ticket:
    ticket_id: UUID
    spot_id: UUID
    spot_type: str
    vehicle_type: str
    entry_time: int

    def __eq__(self, other: Ticket) -> bool:
        return self.ticket_id == other.ticket_id

    def __hash__(self) -> int:
        return hash(self.ticket_id)
