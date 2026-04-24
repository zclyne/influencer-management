from typing import Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
    def create(self, **values: object) -> T: ...

    def get(self, entity_id: str) -> T | None: ...

    def update(self, entity: T, **values: object) -> T: ...

    def archive(self, entity: T) -> T: ...

