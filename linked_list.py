from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass
class Item:
    data: str
    next: Optional[Item] = None


class LinkedList:
    """Sorted singly linked list of unique strings."""

    def __init__(self) -> None:
        self.first: Optional[Item] = None
        self.curr: Optional[Item] = None

    def __contains__(self, key: str) -> bool:
        return self.find(key)

    def __iter__(self) -> Iterator[str]:
        curr = self.first
        while curr is not None:
            yield curr.data
            curr = curr.next

    def find(self, key: str) -> bool:
        """Linear search for key. Leaves curr on the match, or None if missing."""
        self.curr = self.first
        while self.curr is not None and self.curr.data != key:
            self.curr = self.curr.next
        return self.curr is not None

    def insert(self, key: str) -> None:
        """Insert key in sorted order if not already present."""
        if self.find(key):
            return

        node = Item(data=key)

        if self.first is None:
            self.first = node
            return

        self.curr = self.first
        prev: Optional[Item] = None
        while self.curr is not None:
            if self.curr.data >= node.data:
                break
            prev = self.curr
            self.curr = self.curr.next

        if self.curr is self.first:
            node.next = self.first
            self.first = node
        else:
            assert prev is not None
            node.next = self.curr
            prev.next = node

    def print(self) -> None:
        for value in self:
            print(value)
