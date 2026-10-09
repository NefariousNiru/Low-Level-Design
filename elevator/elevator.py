"""
Requirements:

Building
- floors
- elevators

Elevator
- direction: UP, DOWN, IDLE
- current floor
- requests

ExternalRequest -> Outside elevator
InternalRequest -> Inside elevator
"""
import heapq
from enum import StrEnum
from uuid import UUID
from abc import ABC, abstractmethod


class ElevatorDirection(StrEnum):
    UP = "UP"
    DOWN = "DOWN"
    IDLE = "IDLE"


class ElevatorRequestType(StrEnum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class Elevator:
    def __init__(self):
        self.current_floor = 0
        self.direction = ElevatorDirection.IDLE
        self.up_stops = []          # Min Heap
        self.down_stops = []        # Max Heap

    def add_stop(self, floor: int):
        if floor > self.current_floor:
            heapq.heappush(self.up_stops, floor)
        elif floor < self.current_floor:
            heapq.heappush_max(self.down_stops, floor)

    def step(self):
        if self.direction == ElevatorDirection.IDLE:
            self._chose_direction()

        if self.direction == ElevatorDirection.IDLE:
            return

        if self.direction == ElevatorDirection.UP:
            self.current_floor += 1
        else:
            self.current_floor -= 1

        self._serve_current_floor()
        self._update_direction()

    def has_requests_at_or_beyond(self, floor: int, direction: ElevatorDirection) -> bool:
        if direction == ElevatorDirection.UP:
            return any(stop >= floor for stop in self.up_stops)

        if direction == ElevatorDirection.DOWN:
            return any(stop <= floor for stop in self.down_stops)

        return False

    def _chose_direction(self):
        if self.up_stops:
            self.direction = ElevatorDirection.UP
        elif self.down_stops:
            self.direction = ElevatorDirection.DOWN

    def _serve_current_floor(self):
        if (
            self.direction == ElevatorDirection.UP and
            self.up_stops and self.up_stops[0] == self.current_floor
        ):
            heapq.heappop(self.up_stops)

        elif (
            self.direction == ElevatorDirection.DOWN and
            self.down_stops and self.down_stops[0] == self.current_floor
        ):
            heapq.heappop_max(self.down_stops)

    def _update_direction(self):
        if self.direction == ElevatorDirection.UP:
            if not self.up_stops:
                if self.down_stops:
                    self.direction = ElevatorDirection.DOWN
                else:
                    self.direction = ElevatorDirection.IDLE

        elif self.direction == ElevatorDirection.DOWN:
            if not self.down_stops:
                if self.up_stops:
                    self.direction = ElevatorDirection.UP
                else:
                    self.direction = ElevatorDirection.IDLE


class ElevatorSelectionStrategy(ABC):

    @abstractmethod
    def choose(
        self,
        elevators: dict[UUID, Elevator],
        floor: int,
        direction: ElevatorDirection,
    ) -> tuple[UUID, Elevator]:
        pass


class SweepNearestStrategy(ElevatorSelectionStrategy):
    def choose(
        self,
        elevators: dict[UUID, Elevator],
        floor: int,
        direction: ElevatorDirection,
    ) -> tuple[UUID, Elevator]:

        committed = []
        idle = []
        moving_toward = []
        others = []

        for elevator_id, elevator in elevators.items():

            distance = abs(elevator.current_floor - floor)

            is_moving_toward = (
                (
                    direction == ElevatorDirection.UP
                    and elevator.direction == ElevatorDirection.UP
                    and elevator.current_floor <= floor
                )
                or
                (
                    direction == ElevatorDirection.DOWN
                    and elevator.direction == ElevatorDirection.DOWN
                    and elevator.current_floor >= floor
                )
            )

            # Priority 1:
            # Already moving this way AND its existing sweep
            # naturally reaches/passes the caller.
            if (
                is_moving_toward
                and elevator.has_requests_at_or_beyond(
                    floor,
                    direction
                )
            ):
                committed.append(
                    (distance, elevator_id)
                )

            # Priority 2
            elif elevator.direction == ElevatorDirection.IDLE:
                idle.append(
                    (distance, elevator_id)
                )

            # Priority 3:
            # Correct direction, but we'd need to extend its route.
            elif is_moving_toward:
                moving_toward.append(
                    (distance, elevator_id)
                )

            # Priority 4
            else:
                others.append(
                    (distance, elevator_id)
                )

        candidates = (
            committed
            or idle
            or moving_toward
            or others
        )

        if not candidates:
            raise Exception("No elevators available")

        _, elevator_id = min(
            candidates,
            key=lambda x: x[0]
        )

        return elevator_id, elevators[elevator_id]


class ElevatorManager:
    def __init__(self, floors: int, elevators: dict[UUID, Elevator], selection_strategy: ElevatorSelectionStrategy):
        self.floors = floors
        self.elevators = elevators
        self.selection_strategy = selection_strategy

    def request(self, current_floor: int, direction: ElevatorDirection):
        elevator_id, elevator = self.selection_strategy.choose(self.elevators, current_floor, direction)
        elevator.add_stop(current_floor)
        return elevator_id

    def select_floor(self, elevator_id: UUID, floor: int):
        if elevator_id not in self.elevators:
            raise Exception("Elevator not found")
        self.elevators[elevator_id].add_stop(floor)

    def step(self):
        for elevator in self.elevators.values():
            elevator.step()
