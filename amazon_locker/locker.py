import random
import time
import uuid
from enum import IntEnum
from abc import ABC, abstractmethod


class AccessCode:
    def __init__(self, access_code, expiry):
        self.access_code = access_code
        self.expiry = expiry

    def is_valid(self):
        return int(time.time()) < self.expiry


class CompartmentConfiguration:
    def __init__(self, config: dict[CompartmentType, int]):
        for size, qty in config.items():
            compartment_type = CompartmentType(size)
            compartments = [Compartment(compartment_type) for _ in range(qty)]
            setattr(self, f"{compartment_type.name}", compartments)

    def get(self, size: str):
        return getattr(self, f"{size.upper()}")


class CompartmentType(IntEnum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


class PackageType(IntEnum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


class Package:
    def __init__(
        self, id: uuid.UUID, package_type: PackageType, customer_id: uuid.UUID
    ):
        self.id = id
        self.package_type = package_type
        self.customer_id = customer_id


class Compartment:
    def __init__(self, type: CompartmentType):
        self.id = uuid.uuid4()
        self.type = type
        self.package: Package | None = None

    def retrieve(self) -> Package:
        """Retrieve package if contains"""
        if not self.package:
            raise ValueError("Compartment is empty")
        package = self.package
        self.package = None
        return package

    def deposit(self, package: Package) -> None:
        if not package:
            raise ValueError("Package is empty")
        if self.package:
            raise ValueError("Compartment is not empty")
        if package.package_type > self.type:
            raise ValueError("Compartment is smaller than package")
        self.package = package


class AllocationStrategy(ABC):
    @abstractmethod
    def allocate(
        self, compartments: CompartmentConfiguration, package_type: PackageType
    ) -> CompartmentType:
        pass


class AllocationGreedy(AllocationStrategy):
    def allocate(
        self, compartments: CompartmentConfiguration, package_type: PackageType
    ) -> CompartmentType:
        """Greedy Strategy that allocates to the smallest available compartment"""
        eligible = []
        for size, q in vars(compartments).items():
            if q and CompartmentType[size] >= package_type:
                eligible.append((CompartmentType[size], q))

        if not eligible:
            raise Exception("All compartments are occupied")

        type, _ = min(eligible, key=lambda minSize: minSize[0].value)
        return type


class AllocationService:
    def __init__(
        self,
        allocation_strategy: AllocationStrategy | None = None,
        compartments: CompartmentConfiguration | None = None,
    ) -> None:
        self.strategy = allocation_strategy or AllocationGreedy()
        self.compartments: CompartmentConfiguration = (
            compartments or self.get_factory_default()
        )

    def allocate(self, package: Package) -> Compartment:
        """Allocate package to a compartment"""
        compartment_type = self.strategy.allocate(
            self.compartments, package.package_type
        )
        pool = self.compartments.get(compartment_type.name)
        compartment = pool.pop()
        compartment.deposit(package)
        return compartment

    def deallocate(self, compartment: Compartment) -> None:
        """Deallocate compartment by adding it back to empty compartments"""
        self.compartments.get(compartment.type.name).append(compartment)

    @staticmethod
    def get_factory_default() -> CompartmentConfiguration:
        return CompartmentConfiguration(
            {
                CompartmentType.SMALL: 10,
                CompartmentType.MEDIUM: 15,
                CompartmentType.LARGE: 20,
            }
        )


class CodeDelivery(ABC):
    @abstractmethod
    def send(self, code, package: Package):
        pass


class EmailCodeDelivery(CodeDelivery):
    def __init__(self):
        self.user_id_email_map = {}

    def send(self, code, package: Package):
        email_id = self.user_id_email_map.get(package.customer_id)
        message = (
            f"Your Amazon package with ID {package.id} is delivered. Use code {code}"
        )
        # Send message here


class Locker:
    def __init__(
        self,
        code_delivery: CodeDelivery | None = None,
    ):
        self.allocation_service = AllocationService()
        self.access_code_map: dict[str, tuple[AccessCode, Compartment]] = {}
        self.code_delivery: CodeDelivery = code_delivery or EmailCodeDelivery()

    def retrieve(self, code: str) -> Package:
        entry = self.access_code_map.get(code)
        if not entry:
            raise Exception(f"Code {code} is not valid/expired")

        access_code, compartment = entry
        if not access_code.is_valid():
            raise Exception(f"Code {code} is not valid/expired")

        package = compartment.retrieve()

        self.allocation_service.deallocate(compartment)
        del self.access_code_map[code]
        return package

    def deposit(self, package: Package):
        compartment = self.allocation_service.allocate(package)
        access_code = self.generate_access_code()
        self.access_code_map[access_code.access_code] = (access_code, compartment)
        self.code_delivery.send(access_code.access_code, package)

    def generate_access_code(self) -> AccessCode:
        seven_day_seconds = 7 * 24 * 60 * 60

        for _ in range(50):
            # Try 50 times
            code = str(random.randint(100_000, 999_999))
            if code not in self.access_code_map:
                return AccessCode(code, int(time.time()) + seven_day_seconds)

        raise Exception("Could not generate access code at this moment")

    def retrieve_expired(self):
        expired_codes = [
            code
            for code, (access_code, _) in self.access_code_map.items()
            if not access_code.is_valid()
        ]

        packages = []

        for code in expired_codes:
            _, compartment = self.access_code_map[code]

            package = compartment.retrieve()
            packages.append(package)

            self.allocation_service.deallocate(compartment)
            del self.access_code_map[code]

        return packages
