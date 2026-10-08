from abc import ABC, abstractmethod
from collections import deque


class File:
    def __init__(self, name: str, size_bytes: int, ext: str):
        self.name = name
        self.size_bytes = size_bytes
        self.ext = ext.lstrip(".")


class Directory:
    def __init__(self, name: str, children: list[Directory | File]):
        self.name = name
        self.children = children


class Filter(ABC):
    @abstractmethod
    def matches(self, file: File) -> bool:
        """Return True if file matches this filter"""
        pass


# =========
# Single Filter
# =========


class ExtensionFilter(Filter):
    def __init__(self, ext):
        self.ext = ext.lstrip(".")

    def matches(self, file: File) -> bool:
        return self.ext == file.ext


class SizeFilter(Filter):
    comparator_map = {
        "<": lambda a, b: a < b,
        ">": lambda a, b: a > b,
        "<=": lambda a, b: a <= b,
        ">=": lambda a, b: a >= b,
        "=": lambda a, b: a == b,
    }

    def __init__(self, size_bytes, comparator: str = "="):
        self.size_bytes = size_bytes
        self.comparator = comparator

    def matches(self, file: File) -> bool:
        return self.comparator_map[self.comparator](file.size_bytes, self.size_bytes)


class NameFilter(Filter):
    def __init__(self, name: str):
        self.name = name

    def matches(self, file: File) -> bool:
        return self.name in file.name


class NotFilter(Filter):
    def __init__(self, filter: Filter):
        self.filter = filter

    def matches(self, file: File) -> bool:
        return not self.filter.matches(file)


# =========
# Composite Filter
# =========


class AndFilter(Filter):
    def __init__(self, *filters: Filter):
        self.filters = filters

    def matches(self, file: File) -> bool:
        return all(filter.matches(file) for filter in self.filters)


class OrFilter(Filter):
    def __init__(self, *filters: Filter):
        self.filters = filters

    def matches(self, file: File) -> bool:
        return any(filter.matches(file) for filter in self.filters)


class FileSearch:
    def search(self, directory: Directory, filter: Filter) -> list[File]:
        q = deque([directory])
        result = []
        while q:
            node = q.popleft()

            if isinstance(node, File):
                if filter.matches(node):
                    result.append(node)
                continue

            for child in node.children:
                q.append(child)
        return result


if __name__ == "__main__":

    root = Directory(
        "root",
        [
            File(
                "report",
                2_000,
                "txt",
            ),
            File(
                "photo",
                5_000_000,
                "jpg",
            ),
            Directory(
                "documents",
                [
                    File("annual_report", 20_000_000, "pdf"),
                    File("notes", 500, "txt"),
                    File("big_report", 15_000_000, "txt"),
                ],
            ),
        ],
    )

    searcher = FileSearch()

    # --------------------------------------------------------
    # Example 1:
    # Find all txt files
    # --------------------------------------------------------

    txt_filter = ExtensionFilter("txt")

    print(
        searcher.search(
            root,
            txt_filter,
        )
    )

    # --------------------------------------------------------
    # Example 2:
    # Find txt files > 1 MB
    # --------------------------------------------------------

    large_txt_filter = AndFilter(
        ExtensionFilter("txt"),
        SizeFilter(1_000_000, ">"),
    )

    print(
        searcher.search(
            root,
            large_txt_filter,
        )
    )

    # --------------------------------------------------------
    # Example 3:
    #
    # (extension == txt AND size > 1 MB)
    # OR
    # name contains "annual"
    # --------------------------------------------------------

    complex_filter = OrFilter(
        AndFilter(
            ExtensionFilter("txt"),
            SizeFilter(1_000_000, ">"),
        ),
        NameFilter("annual"),
    )

    print(
        searcher.search(
            root,
            complex_filter,
        )
    )
