# Mini Search Engine

A small search engine built from scratch data structures (custom singly linked list, two hand-rolled hash tables) that indexes a corpus of web pages and ranks search results using Google's original PageRank algorithm.

This repo implements the same data structures, hashing behavior, and console output, plus a PageRank extension and a crawler for generating your own test corpora.

## What it does

1. Reads a `webpages.txt` corpus describing pages, the words on each page, and each page's outgoing hyperlinks.
2. Builds two hash tables from that corpus:
   - a **page table**, keyed by URL
   - a **word table** (inverted index), keyed by word → list of pages containing it
3. Runs PageRank over the page table to score every page by importance.
4. Drops into an interactive loop: type a word, get back every page that contains it, sorted by PageRank score (highest first).

```
$ python main.py
Enter the Word:  algorithms
=========================================
Web Pages:
490414 http://cs.university.edu
254792 http://cs.university.edu/faculty
...
=========================================
Enter the Word:  Exit
```

## Files

| File | Role |
|---|---|
| `main.py` | Loads `webpages.txt`, builds both hash tables, runs PageRank, runs the query loop |
| `webpage.py` | `Webpage` hash table (pages, 100 buckets) + `compute_page_rank()` |
| `word.py` | `Word` hash table (inverted index, 10,000 buckets) + result printing |
| `linked_list.py` | Sorted, unique-string singly linked list used inside both hash tables |
| `crawler.py` | Standard-library-only crawler that builds a `webpages.txt` from a real site |
| `webpages.txt` | The corpus `main.py` reads (not included — see **Getting a corpus** below) |

## The `webpages.txt` format

Whitespace-separated tokens. `NEWPAGE <url>` starts a page record; every token after it is either a word on that page or a hyperlink (anything containing `http://` or `https://`), until the next `NEWPAGE`:

```
NEWPAGE http://cs.university.edu
welcome
algorithms
http://cs.university.edu/faculty
http://cs.university.edu/courses
NEWPAGE http://cs.university.edu/faculty
faculty
algorithms
http://cs.university.edu
```

Each word or link is expected to appear at most once per page (the loaders don't dedupe for you — `LinkedList.insert` asserts the key isn't already present).

## Data structures

- **`LinkedList`** — sorted, singly linked, no duplicate values. Backs both the per-page word/link lists and the per-word page lists.
- **`Webpage`** — hash table of `Page` records (`id`, `url`, PageRank `weight`, its `words` list, its `hyperlinks` list), 100 buckets, separate chaining, custom string hash.
- **`Word`** — inverted index: hash table of `Term` records (`word`, the `LinkedList` of page URLs containing it), 10,000 buckets, modulus-90 hash.

## PageRank

Implemented in `Webpage.compute_page_rank()`:

- Every page starts at weight `1/N`.
- Each of 50 iterations, a page's new weight is `10% × (1/N)` (teleport) plus `90%` of the weight fed in by every page that links to it, split evenly across that source page's outgoing links.
- Hyperlinks pointing outside the corpus (no matching `NEWPAGE` record) are ignored — they simply can't be resolved to a target page.
- Pages with **zero resolvable outgoing links** ("dangling" pages) don't redistribute their weight anywhere; it just leaks out of the system each iteration.

`main.py::google_rank()` just calls `compute_page_rank()`; the actual score printing (scaled to a readable integer and sorted descending) happens in `Word._print_pages`.

## Getting a corpus

Three ways to get a working corpus:

**1. Use `crawler.py` on a real site** (recommended — exercises the real link graph):
```
python crawler.py https://www.[university name].edu --max-pages 50 --delay 1.0
```
Standard library only, no `pip install` needed. BFS-crawls same-domain pages, respects `robots.txt`, rate-limits itself, and writes output straight into `webpages.txt` format. Off-domain links are recorded but not followed.

**2. Hand-write a small synthetic file** — useful for verifying PageRank math by hand on a tiny known graph (see the format example above).

**3. Generate a larger synthetic corpus programmatically** for stress-testing edge cases like dangling nodes, link chains, and mutual-reference clusters.

## Running it

```
python main.py
```

Expects `webpages.txt` in the current directory. Type any word to search; type `Exit` to quit.
