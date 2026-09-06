from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List, Optional

from linked_list import LinkedList

PAGE_RANK_ITERATIONS = 50
TELEPORT = 0.1
FOLLOW = 0.9

TABLE_SIZE = 100


def _to_int32(value: int) -> int:
    """Wrap to a C++-style 32-bit signed int."""
    value &= 0xFFFFFFFF
    if value >= 0x80000000:
        value -= 0x100000000
    return value


def _cpp_mod(value: int, modulus: int) -> int:
    """Towards-zero remainder, matching C++11 `operator%` for integers."""
    if modulus == 0:
        raise ZeroDivisionError
    quotient = int(value / modulus)
    return value - quotient * modulus


@dataclass
class Page:
    id: int = 0
    url: str = ""
    weight: float = 0.0
    new_weight: float = 0.0
    words: Optional[LinkedList] = None
    hyperlinks: Optional[LinkedList] = None
    next: Optional[Page] = None


class Webpage:
    """Hash table of web pages, using separate chaining."""

    def __init__(self, table_size: int) -> None:
        # The C++ constructor accepts table_size but always allocates 100 buckets.
        _ = table_size
        self.tablesize = TABLE_SIZE
        self.hash_table: List[Page] = [Page() for _ in range(self.tablesize)]

    def hash(self, key: str) -> int:
        h = 0
        for ch in key:
            h = _to_int32((h + ord(ch)) * 17)
        return abs(_cpp_mod(h, self.tablesize))

    def add_item(self, page_id: int, url: str, words: LinkedList, hyperlinks: LinkedList) -> None:
        assert not self.find_url(url)

        index = self.hash(url)
        bucket = self.hash_table[index]

        if bucket.url == "":
            bucket.id = page_id
            bucket.url = url
            bucket.weight = 0.0
            bucket.new_weight = 0.0
            bucket.words = words
            bucket.hyperlinks = hyperlinks
            return

        node = Page(
            id=page_id,
            url=url,
            weight=0.0,
            new_weight=0.0,
            words=words,
            hyperlinks=hyperlinks,
        )
        ptr = bucket
        while ptr.next is not None:
            ptr = ptr.next
        ptr.next = node

    def iter_pages(self) -> Iterator[Page]:
        """Yield every real page, including collision-chain entries."""
        for bucket in self.hash_table:
            if bucket.url == "":
                continue
            ptr: Optional[Page] = bucket
            while ptr is not None:
                yield ptr
                ptr = ptr.next

    def find_page(self, url: str) -> Optional[Page]:
        if url == "":
            return None
        index = self.hash(url)
        ptr: Optional[Page] = self.hash_table[index]
        while ptr is not None:
            if ptr.url == url:
                return ptr
            ptr = ptr.next
        return None

    def find_url(self, url: str) -> bool:
        return self.find_page(url) is not None

    def compute_page_rank(self, iterations: int = PAGE_RANK_ITERATIONS) -> None:
        """Google PageRank: 10% teleport, 90% follow outgoing links, `iterations` steps.

        Hyperlinks that do not point at a page in this table are ignored, matching
        the assignment (no NEWPAGE record ⇒ drop the link). Outgoing targets are
        resolved once so the 50 iterations do not repeat hash lookups.
        """
        pages = list(self.iter_pages())
        n = len(pages)
        if n == 0:
            return

        # URL → page, used only to resolve links before the iterative updates.
        by_url = {page.url: page for page in pages}
        outgoing: List[List[Page]] = []
        for page in pages:
            targets: List[Page] = []
            if page.hyperlinks is not None:
                for url in page.hyperlinks:
                    target = by_url.get(url)
                    if target is not None:
                        targets.append(target)
            outgoing.append(targets)

        inv_n = 1.0 / n
        for page in pages:
            page.weight = inv_n

        teleport = TELEPORT * inv_n
        for _ in range(iterations):
            for page in pages:
                page.new_weight = teleport
            for page, targets in zip(pages, outgoing):
                t = len(targets)
                if t == 0:
                    continue
                share = FOLLOW * page.weight / t
                for target in targets:
                    target.new_weight += share
            for page in pages:
                page.weight = page.new_weight

    def print(self) -> None:
        for i, bucket in enumerate(self.hash_table):
            if bucket.url == "":
                continue
            ptr: Optional[Page] = bucket
            while ptr is not None:
                print("=========================================")
                print(f"Index = {i}")
                print(f"{ptr.url}       ID: {ptr.id}")
                print(ptr.weight)
                print("--------------------")
                print("Hyper-links: ")
                if ptr.hyperlinks is not None:
                    ptr.hyperlinks.print()
                print("-------------------")
                print("Words: ")
                if ptr.words is not None:
                    ptr.words.print()
                print("=========================================")
                ptr = ptr.next

    def number_of_items_in_index(self, index: int) -> int:
        bucket = self.hash_table[index]
        if bucket.url == "":
            return 0
        count = 1
        ptr = bucket
        while ptr.next is not None:
            ptr = ptr.next
            count += 1
        return count
