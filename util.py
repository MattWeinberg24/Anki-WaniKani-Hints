def is_kanji(c: str) -> bool:
    """
    Tests whether a provided character is a kanji or not
    (courtesy of https://github.com/midse/anki-kakijun)

    Args:
        c (str): unicode character to test

    Returns:
        bool: true if kanji, false if not
    """
    c = ord(c)
    return (
        (c >= 0x4E00 and c <= 0x9FC3)
        or (c >= 0x3400 and c <= 0x4DBF)
        or (c >= 0xF900 and c <= 0xFAD9)
        or (c >= 0x2E80 and c <= 0x2EFF)
        or (c >= 0x20000 and c <= 0x2A6DF)
    )
