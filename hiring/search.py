import unicodedata


def fold(text):
    """Lowercase `text` and strip accents, so "López" and "LOPEZ" both become "lopez".

    SQLite can't ignore accents (or capitals on non-English letters) in a
    query, so searchable text is folded with this before it's stored, and the
    search words are folded the same way before comparing.
    """
    # NFKD splits "ó" into "o" plus a separate accent mark; then drop the marks.
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_accents.casefold()
