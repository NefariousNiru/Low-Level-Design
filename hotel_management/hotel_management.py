import bisect
import uuid
from abc import abstractmethod, ABC
from enum import StrEnum
from uuid import UUID
from datetime import date


class RoomType(StrEnum):
    SINGLE = "single"
    DOUBLE = "double"
    SUITE = "suite"


class Interval:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class Reservation:
    def __init__(self, room_id: UUID, guests: list[Guest], amount: float, dates: Interval):
        self.id = uuid.uuid4()
        self.room_id = room_id
        self.guest = guests
        self.amount = amount
        self.dates = dates


class Room:
    def __init__(self, room_id: UUID, room_type: RoomType, reservations: list[Reservation], capacity: int):
        self.room_id = room_id
        self.room_type = room_type
        self.reservations = reservations
        self.capacity = capacity


class Guest:
    def __init__(self, guest_id: UUID, guest_name: str, guest_age: int):
        self.guest_id = guest_id
        self.guest_name = guest_name
        self.guest_age = guest_age


class ReservationPolicy(ABC):
    @abstractmethod
    def can_accommodate(self, guests: list[Guest], room: Room):
        pass


class DefaultReservationPolicy(ReservationPolicy):
    def can_accommodate(self, guests: list[Guest], room: Room):

        # Room type is invalid
        if len(guests) > room.capacity:
            raise Exception("Invalid room type, pick a bigger room")

        # Cannot accommodate only minors
        if len([True for guest in guests if guest.guest_age >= 18]) == 0:
            raise Exception("Accommodation for all minors not allowed")


class PricingPolicy(ABC):
    @abstractmethod
    def get_price(self, guests: list[Guest], room_type: RoomType, dates: Interval) -> float:
        pass


class DefaultPricingPolicy(PricingPolicy):
    def __init__(self, nightly_rate: float):
        self.nightly_rate = nightly_rate

    def get_price(self, guests: list[Guest], room_type: RoomType, dates: Interval) -> float:
        return self.nightly_rate * (dates.end - dates.start).days


class CancellationPolicy(ABC):
    @abstractmethod
    def can_cancel_reservation(self, reservation: Reservation):
        pass


class DefaultCancellationPolicy(CancellationPolicy):
    def can_cancel_reservation(self, reservation: Reservation):
        if date.today() >= reservation.dates.start:
            raise Exception("Cancellation for reservations not allowed beyond start date")


class HotelManagement:
    def __init__(self,
                 rooms: dict[UUID, Room],
                 reservation_policy: ReservationPolicy,
                 pricing_policy: PricingPolicy,
                 cancellation_policy: CancellationPolicy,
        ):
        self.rooms = rooms
        self.reservation_policy = reservation_policy or DefaultReservationPolicy()
        self.pricing_policy = pricing_policy or DefaultPricingPolicy(nightly_rate=150)
        self.cancellation_policy = cancellation_policy or DefaultCancellationPolicy()
        self._validate()

        # Prefill
        self.reservations = self._get_reservations_from_rooms()


    def search_rooms(self, check_in: date, check_out: date, room_type: RoomType | None = None) -> list[Room]:
        rooms = []
        for room in self.rooms.values():
            if room_type is not None and room.room_type != room_type:
                continue

            available, _ = self._is_available(room, check_in, check_out)
            if available:
                rooms.append(room)

        return rooms

    def book_room(self, room_id: UUID, check_in: date, check_out: date, guests: list[Guest]) -> Reservation:
        if room_id not in self.rooms:
            raise Exception("Room not found")

        room = self.rooms[room_id]
        self.reservation_policy.can_accommodate(guests, room)

        available, idx = self._is_available(room, check_in, check_out)

        if not available:
            raise Exception("Room unavailable")

        new_dates = Interval(check_in, check_out)
        price = self.pricing_policy.get_price(guests, room.room_type, new_dates)

        reservation = Reservation(room.room_id, guests, price, new_dates)
        self.rooms[room_id].reservations.insert(idx, reservation)
        self.reservations[reservation.id] = reservation

        return reservation

    def cancel_reservation(self, reservation_id: UUID) -> float:
        if reservation_id not in self.reservations:
            raise Exception("Reservation not found")

        reservation = self.reservations[reservation_id]
        self.cancellation_policy.can_cancel_reservation(reservation)

        if reservation.room_id not in self.rooms:
            raise Exception("Room not found")

        self.rooms[reservation.room_id].reservations.remove(reservation)
        del self.reservations[reservation.id]
        return reservation.amount

    @staticmethod
    def _is_available(room: Room, check_in: date, check_out: date) -> tuple[bool, int | None]:
        if check_in >= check_out:
            return False, None

        bookings = room.reservations

        idx = bisect.bisect_left(
            bookings,
            check_in,
            key=lambda reservation: reservation.dates.start
        )

        # Does it overlap the reservation immediately before idx?
        if idx > 0:
            previous = bookings[idx - 1]
            if previous.dates.end > check_in:
                return False, None

        # Does it overlap the reservation immediately after idx?
        if idx < len(bookings):
            next_booking = bookings[idx]
            if check_out > next_booking.dates.start:
                return False, None

        return True, idx

    def _validate(self):
        for room in self.rooms.values():
            bookings = room.reservations
            for i in range(len(bookings) - 1):
                if (bookings[i].dates.start > bookings[i + 1].dates.start) or (bookings[i].dates.end > bookings[i + 1].dates.start):
                    raise Exception("Room are overlapping or not sorted")

    def _get_reservations_from_rooms(self):
        reservations: dict[UUID, Reservation] = {}
        for room in self.rooms.values():
            for reservation in room.reservations:
                reservations[reservation.id] = reservation
        return reservations
