class PackageInstallerError(Exception):
    """Base exception so callers can catch all domain errors together."""


class PackageNotFound(PackageInstallerError):
    def __init__(self, package_name: str) -> None:
        super().__init__(f"Package not found: {package_name}")


class DependencyCycle(PackageInstallerError):
    def __init__(self, cycle: list[str]) -> None:
        # Showing the cycle is much more useful than merely saying "cycle exists".
        # Example: A -> B -> C -> A
        super().__init__(f"Dependency cycle detected: {' -> '.join(cycle)}")
        self.cycle = cycle
