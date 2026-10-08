from typing import Protocol


class SilverResult(Protocol):
    @property
    def rows_inserted(self) -> int:
        ...

    @property
    def rows_updated(self) -> int:
        ...