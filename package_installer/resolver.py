from abc import ABC, abstractmethod
from enum import Enum, auto

from .errors import DependencyCycle
from .models import Package
from .repository import PackageRepository


class DependencyResolver(ABC):
    """STRATEGY PATTERN.

    PackageInstaller depends on this interface, not on DFS directly.  DFS is a
    natural implementation today, but the installer does not need to change if
    resolution rules later become version-aware or use a different algorithm.

    Do not add Strategy just to say "design pattern" in an interview.  Here it
    is justified because dependency resolution is a separable algorithm that
    can realistically vary independently of installation itself.
    """

    @abstractmethod
    def resolve(
        self, root_package: str, repository: PackageRepository
    ) -> list[Package]:
        """Return packages in valid installation order, dependencies first."""
        raise NotImplementedError


class _VisitState(Enum):
    """Three-color DFS state.

    UNSEEN is represented by absence from the dictionary.
    VISITING means the node is on the *current recursion path*.
    VISITED means the node and all of its dependencies are fully processed.
    """

    VISITING = auto()
    VISITED = auto()


class DFSDependencyResolver(DependencyResolver):
    """Resolve dependencies with post-order DFS / topological ordering.

    Core invariant:
        A package is appended to `order` only AFTER every dependency has been
        appended.  Therefore iterating `order` from left to right is safe for
        installation.

    Cycle detection:
        Encountering VISITING means we reached a package already on the current
        DFS path, so there is a directed cycle.  VISITED is different: reaching
        a fully processed package through another branch is perfectly valid.

    Complexity for the reachable graph:
        Time:  O(V + E)
        Space: O(V) for visit state + recursion/path + result.
    """

    def resolve(
        self, root_package: str, repository: PackageRepository
    ) -> list[Package]:
        state: dict[str, _VisitState] = {}
        order: list[Package] = []
        path: list[str] = []

        def dfs(package_name: str) -> None:
            current_state = state.get(package_name)

            # Already completely resolved through another dependency branch.
            # This also prevents the same shared dependency from being emitted
            # twice, e.g. A -> B -> D and A -> C -> D.
            if current_state is _VisitState.VISITED:
                return

            if current_state is _VisitState.VISITING:
                # Find where this package first appeared in the active path so
                # the exception reports only the actual cycle.
                cycle_start = path.index(package_name)
                cycle = path[cycle_start:] + [package_name]
                raise DependencyCycle(cycle)

            package = repository.get(package_name)
            state[package_name] = _VisitState.VISITING
            path.append(package_name)

            for dependency_name in package.dependencies:
                dfs(dependency_name)

            # All dependencies are now safe, so post-order append guarantees
            # dependency-before-dependent installation order.
            path.pop()
            state[package_name] = _VisitState.VISITED
            order.append(package)

        dfs(root_package)
        return order
