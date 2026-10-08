from .models import Package
from .repository import PackageRepository
from .resolver import DependencyResolver


class PackageInstaller:
    """Application/service layer coordinating resolve -> install.

    Think of this as the small public FACADE of the subsystem:
        installer.install("app")

    Callers do not need to understand graph traversal or repository details.
    The class intentionally does NOT implement dependency traversal itself;
    that responsibility belongs to DependencyResolver.

    Interview assumption:
        Actual OS/package-manager side effects are out of scope.  `_install_one`
        represents that boundary and records installation in memory so the core
        behavior is executable and testable.
    """

    def __init__(
        self,
        repository: PackageRepository,
        resolver: DependencyResolver,
    ) -> None:
        self._repository = repository
        self._resolver = resolver

        # Installed state belongs to the installer, not Package.  Package is
        # metadata; whether it is installed is machine/environment state.
        self._installed: set[str] = set()
        self._installation_log: list[str] = []

    def install(self, package_name: str) -> list[str]:
        """Install one package and any missing dependencies.

        Returns only packages installed by THIS call.  That makes idempotency
        visible in tests/demo:

            first install("A")  -> ["D", "B", "C", "A"]
            second install("A") -> []

        Important ordering decision:
        We resolve the full dependency graph *before* mutating installed state.
        Therefore a missing package or dependency cycle fails before we perform
        any installation work.
        """
        if package_name in self._installed:
            return []

        install_order = self._resolver.resolve(package_name, self._repository)
        installed_now: list[str] = []

        for package in install_order:
            # A shared dependency may already have been installed by an earlier
            # top-level request.  Installation should be idempotent.
            if package.name in self._installed:
                continue

            self._install_one(package)
            installed_now.append(package.name)

        return installed_now

    def _install_one(self, package: Package) -> None:
        """Boundary where real installation side effects would happen.

        In production this could invoke an OS package manager, unpack an
        artifact, write files, etc.  Keeping it separate lets the graph logic
        remain deterministic and easy to test.
        """
        self._installed.add(package.name)
        self._installation_log.append(package.name)

    def is_installed(self, package_name: str) -> bool:
        return package_name in self._installed

    @property
    def installation_log(self) -> tuple[str, ...]:
        # Expose an immutable view so callers cannot corrupt internal state.
        return tuple(self._installation_log)
