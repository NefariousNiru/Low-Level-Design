from abc import ABC, abstractmethod
from collections.abc import Iterable

from .errors import PackageNotFound
from .models import Package


class PackageRepository(ABC):
    """Abstraction over wherever package metadata comes from.

    This is deliberately tiny.  In an interview we do not need a database,
    HTTP client, cache, etc.  The important design point is that dependency
    resolution should not care *where* metadata is stored.
    """

    @abstractmethod
    def get(self, package_name: str) -> Package:
        raise NotImplementedError


class InMemoryPackageRepository(PackageRepository):
    """Simple repository used by the demo/tests."""

    def __init__(self, packages: Iterable[Package]) -> None:
        self._packages = {package.name: package for package in packages}

    def get(self, package_name: str) -> Package:
        try:
            return self._packages[package_name]
        except KeyError as exc:
            raise PackageNotFound(package_name) from exc
