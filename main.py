from __future__ import annotations

import sys
from typing import Iterator, TextIO, Tuple

from linked_list import LinkedList
from webpage import Webpage
from word import Word

WEBPAGES_FILE = "webpages.txt"


def tokens(stream: TextIO) -> Iterator[str]:
    """Yield whitespace-separated tokens, matching C++ `operator>>` on strings."""
    for line in stream:
        yield from line.split()


def is_hyperlink(item: str) -> bool:
    return "http://" in item or "https://" in item


def count_items(path: str) -> Tuple[int, int, int]:
    page_count = 0
    url_count = 0
    word_count = 0

    with open(path, encoding="utf-8") as input_file:
        token_stream = tokens(input_file)
        for item in token_stream:
            if item == "NEWPAGE":
                page_count += 1
                # C++ consumes the page URL here without counting it as a link/word.
                try:
                    next(token_stream)
                except StopIteration:
                    break
            elif is_hyperlink(item):
                url_count += 1
            else:
                word_count += 1

    return page_count, url_count, word_count

# I’ll implement PageRank from the assignment stub: iterate the loaded pages, apply the 50-iteration weight update, and surface those scores in search results.
#I’ll add PageRank on the page table (50 iterations, 10%/90% split), resolve only in-corpus links, and print integer scores next to search hits.
def google_rank(webpage_hash: Webpage) -> None:
    webpage_hash.compute_page_rank()


def load_indexes(path: str, page_count: int, word_count: int) -> Tuple[Webpage, Word]:
    webpage_hash = Webpage(page_count)
    word_hash = Word(word_count)

    page_id = 1
    current_page = ""
    hyperlinks = LinkedList()
    words = LinkedList()

    with open(path, encoding="utf-8") as read_file:
        token_stream = tokens(read_file)
        for item in token_stream:
            if item == "NEWPAGE":
                try:
                    item = next(token_stream)
                except StopIteration:
                    break
                hyperlinks = LinkedList()
                words = LinkedList()
                webpage_hash.add_item(page_id, item, words, hyperlinks)
                current_page = item
                page_id += 1
            elif is_hyperlink(item):
                hyperlinks.insert(item)
            else:
                words.insert(item)
                pages = word_hash.get_linked_list(item)
                if pages is None:
                    pages = LinkedList()
                    pages.insert(current_page)
                    word_hash.add_item(item, pages)
                else:
                    pages.insert(current_page)

    return webpage_hash, word_hash


def query_loop(word_hash: Word, webpage_hash: Webpage) -> None:
    while True:
        command = input("Enter the Word:  ")
        parts = command.split()
        if not parts:
            continue
        command = parts[0]
        if command == "Exit":
            sys.exit(0)
        word_hash.find_word(command, webpage_hash)


def main() -> None:
    try:
        page_count, _url_count, word_count = count_items(WEBPAGES_FILE)
    except OSError:
        print("Error Opening File... ")
        sys.exit(1)

    try:
        webpage_hash, word_hash = load_indexes(WEBPAGES_FILE, page_count, word_count)
    except OSError:
        print("Error Opening File... ")
        sys.exit(1)

    google_rank(webpage_hash)
    query_loop(word_hash, webpage_hash)


if __name__ == "__main__":
    main()
