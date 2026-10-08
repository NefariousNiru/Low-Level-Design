from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Package:
    """Domain entity describing one installable package.

    dependencies stores package *names*, not Package objects.  That keeps the
    entity simple and prevents us from having to construct the entire graph in
    memory up front.  The repository is responsible for resolving names.
    """

    name: str
    dependencies: tuple[str, ...] = ()
