from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from linked_list import LinkedList
from webpage import Webpage

# Scale PageRank (a probability) up so search hits print as readable integers.
RANK_SCALE = 1_000_000

TABLE_SIZE = 10000
HASH_MODULUS = 90


@dataclass
class Term:
    word: str = ""
    pages: Optional[LinkedList] = None
    next: Optional[Term] = None


class Word:
    """Hash table mapping terms to the pages they appear on (inverted index)."""

    def __init__(self, word_count: int) -> None:
        # The C++ constructor accepts word_count but always allocates 10000 buckets.
        _ = word_count
        self.tablesize = TABLE_SIZE
        self.hash_table: List[Term] = [Term() for _ in range(self.tablesize)]

    def hash(self, key: str) -> int:
        # Matches the C++ implementation: unsigned accumulator, modulus 90 per char.
        h = 0
        for ch in key:
            h = (h * 2917 + ord(ch)) % HASH_MODULUS
        return h

    def add_item(self, word: str, pages: LinkedList) -> None:
        index = self.hash(word)
        bucket = self.hash_table[index]

        if bucket.word == "":
            bucket.word = word
            bucket.pages = pages
            bucket.next = None
            return

        node = Term(word=word, pages=pages)
        ptr = bucket
        while ptr.next is not None:
            ptr = ptr.next
        ptr.next = node

    def find_word(self, word: str, webpage_hash: Optional[Webpage] = None) -> None:
        index = self.hash(word)
        ptr: Optional[Term] = self.hash_table[index]
        while ptr is not None:
            if ptr.word == word:
                print("=========================================")
                print("Web Pages: ")
                self._print_pages(ptr.pages, webpage_hash)
                print("=========================================")
                return
            ptr = ptr.next
        print("This word was not found!")
        print("=========================================")

    def _print_pages(
        self,
        pages: Optional[LinkedList],
        webpage_hash: Optional[Webpage],
    ) -> None:
        if pages is None:
            return
        if webpage_hash is None:
            pages.print()
            return

        results = []
        for url in pages:
            page = webpage_hash.find_page(url)
            score = int(page.weight * RANK_SCALE) if page is not None else 0
            results.append((score, url))
        # Highest PageRank first; ties keep the linked-list (alphabetical) order.
        results.sort(key=lambda item: item[0], reverse=True)
        for score, url in results:
            print(f"{score} {url}")

    def get_linked_list(self, word: str) -> Optional[LinkedList]:
        index = self.hash(word)
        ptr: Optional[Term] = self.hash_table[index]
        while ptr is not None:
            if ptr.word == word:
                return ptr.pages
            ptr = ptr.next
        return None

    def print(self) -> None:
        for i, bucket in enumerate(self.hash_table):
            if bucket.word == "":
                continue
            print("=========================================")
            print(f"Index = {i}")
            print(bucket.word)
            print("--------------------")
            print("Web Pages: ")
            if bucket.pages is not None:
                bucket.pages.print()
            print("=========================================")
