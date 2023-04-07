# anki/qt dependencies
from anki import hooks
from anki.template import TemplateRenderContext, TemplateRenderOutput
from aqt import mw

# general python dependencies
import json
from pathlib import Path

# custom dependencies
from .api_utils import *
from .static import html, css
from .util import is_kanji

CACHE_PATH = f"{Path(__file__).parent}/user_files/cache.json"
EMPTY_CACHE = f"""{{
    "{SubjectType.RADICAL.value}": {{}},
    "{SubjectType.KANJI.value}": {{}},
    "{SubjectType.VOCABULARY.value}": {{}}
}}"""

config = mw.addonManager.getConfig(__name__)
cache = {}

def query_cache_vocab(slug: str, rewrite=True):
    """
    Query the WaniKani API for information on the provided vocabulary,
    then add relevant data to the local cache

    Args:
        slug (str): vocabulary string
        rewrite (bool, optional): whether or not to rewrite cache.json. Defaults to True.

    Returns:
        dict | SubjectError: newly cached vocabulary data entry if success,
                             SubjectError if fail
    """

    token = config["token"]
    # query WaniKani API for vocab data
    vocab_data = get_subject_by_slug(SubjectType.VOCABULARY, slug, token)
    if isinstance(vocab_data, SubjectError):
        # if vocab not in WaniKani, cache a special value
        if vocab_data == SubjectError.INVALID_SLUG:
            cache[SubjectType.VOCABULARY.value][slug] = None
            # rewrite cache file (if flag is set)
            if rewrite:
                with open(CACHE_PATH, "w") as f:
                    json.dump(cache, f, indent=4)
        return vocab_data

    # build vocab cache entry
    vocab_entry = {}
    vocab_entry["mm"] = vocab_data["meaning_mnemonic"]
    vocab_entry["rm"] = vocab_data["reading_mnemonic"]

    # cache data for all kanji the vocab is composed of (if not already in cache)
    for c in slug:
        if not is_kanji(c) or c in cache[SubjectType.KANJI.value]:
            continue
        kanji_entry = query_cache_kanji(c, rewrite=False)
        if isinstance(kanji_entry, SubjectError):
            print(kanji_entry)

    cache[SubjectType.VOCABULARY.value][slug] = vocab_entry

    # rewrite cache file (if flag is set)
    if rewrite:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=4)
    
    return vocab_entry


def query_cache_kanji(slug: str, rewrite=True):
    """
    Query the WaniKani API for information on the provided kanji and its radicals,
    then add relevant data to the local cache

    Args:
        slug (str): kanji character
        rewrite (bool, optional): whether or not to rewrite cache.json. Defaults to True.

    Returns:
        dict | SubjectError: newly cached kanji data entry if success,
                             SubjectError if fail
    """

    token = config["token"]
    # query WaniKani API for kanji data
    kanji_data = get_subject_by_slug(SubjectType.KANJI, slug, token)
    if isinstance(kanji_data, SubjectError):
        # if kanji not in WaniKani, cache a special value
        if kanji_data == SubjectError.INVALID_SLUG:
            cache[SubjectType.KANJI.value][slug] = None
            # rewrite cache file (if flag is set)
            if rewrite:
                with open(CACHE_PATH, "w") as f:
                    json.dump(cache, f, indent=4)
        return kanji_data

    # build kanji cache entry
    kanji_entry = {}
    kanji_entry["meaning"] = kanji_data["meanings"][0]["meaning"]
    kanji_entry["mm"] = kanji_data["meaning_mnemonic"]
    kanji_entry["rm"] = kanji_data["reading_mnemonic"]
    kanji_entry["radical_ids"] = kanji_data["component_subject_ids"]

    # cache data for all radicals the kanji is composed of (if not already in cache)
    for id in kanji_entry["radical_ids"]:
        # if radical data not in cache...
        if id not in cache[SubjectType.RADICAL.value]:
            radical_entry = query_cache_radical(id, rewrite=False)
            if isinstance(radical_entry, SubjectError):
                print(radical_entry)

    cache[SubjectType.KANJI.value][slug] = kanji_entry

    # rewrite cache file (if flag is set)
    if rewrite:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=4)
    
    return kanji_entry


def query_cache_radical(id: int, rewrite=True):
    """
    Query the WaniKani API for information on the provided radical,
    then add relevant data to the local cache

    Args:
        id (int): id of the radical within the WaniKani API
        rewrite (bool, optional): whether or not to rewrite cache.json. Defaults to True.

    Returns:
        dict | SubjectError: newly cached radical data entry if success,
                             SubjectError if fail
    """

    token = config["token"]
    # query WaniKani API for radical data
    radical_data = get_subject_by_id(id, token)
    if isinstance(radical_data, SubjectError):
        return radical_data

    #build radical cache entry
    radical_entry = {}
    radical_entry["slug"] = radical_data["slug"]

    # NOTE: Uncomment the below if extra radical information should be stored. 
    #
    # radical_entry["mm"] = radical_data["meaning_mnemonic"]
    # radical_entry["chr"] = radical_data["characters"]
    # if len(radical_data["character_images"]) > 0:
    #     radical_entry["image_url"] = [img["url"]
    #         for img in radical_data["character_images"] 
    #         if img["content_type"] == "image/png"
    #         and img["metadata"]["dimensions"] == "32x32"
    #     ][0]

    # cache the radical entry (note: `id` key gets converted to string for json)
    cache[SubjectType.RADICAL.value][str(id)] = radical_entry

    # rewrite cache file (if flag is set)
    if rewrite:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=4)

    return radical_entry


def prepare_vocab_hint(text: str, vocab: str) -> str:
    """
    Organize the string (including the vocab hint) that will be provided to the card 

    Args:
        text (str): text attached to field with the vocab hint filter applied
        vocab (str): the actual vocabulary string to make the hint out of

    Returns:
        str: html string with hint applied,
             or the original text if failure
    """

    vocab_entry = {}
    if vocab in cache[SubjectType.VOCABULARY.value]:
        # attempt to grab vocab data via cache
        vocab_entry = cache[SubjectType.VOCABULARY.value][vocab]
        # if cache indicates that vocab is not in WaniKani API, cancel
        if vocab_entry is None:
            return text
    else:
        # otherwise grab hints from WaniKani via API
        vocab_entry = query_cache_vocab(vocab)
        if isinstance(vocab_entry, SubjectError):
            print(vocab_entry)
            return text
    
    # get the meanings (i.e. names) of kanji the vocab is composed of
    kanji_names = [cache[SubjectType.KANJI.value][c]["meaning"]
        for c
        in vocab
        if is_kanji(c)
    ]

    # format html (via static.py) to inject into card
    kanji_names_str = ", ".join(kanji_names)
    return html.format(
        text=text,
        component_list=kanji_names_str,
        meaning_mnemonic=vocab_entry["mm"],
        reading_mnemonic=vocab_entry["rm"]
    )
    

def prepare_kanji_hint(text: str) -> str:
    """
    Organize the string (including the kanji hint(s)) that will be provided to the card 

    Args:
        text (str): text attached to field with the kanji hint filter applied

    Returns:
        str: html string with hint(s) applied to each kanji,
             or the original text (for each kanji) if failure
    """

    output = ""

    for c in text:
        if not is_kanji(c):
            output += c
            continue

        kanji_entry = {}
        if c in cache[SubjectType.KANJI.value]:
            # attempt to grab kanji data via cache
            kanji_entry = cache[SubjectType.KANJI.value][c]
            # if cache indicates that kanji is not in WaniKani API, skip it
            if kanji_entry is None:
                output += c
                continue
        else:
            # otherwise grab hints from WaniKani via API
            kanji_entry = query_cache_kanji(c)
            if isinstance(kanji_entry, SubjectError):
                print(kanji_entry)
                output += c
                continue

        # get the ids of radicals this kanji is composed of
        radical_ids = kanji_entry["radical_ids"]
        # query the radical cache for each of their corresponding names
        radical_names = [cache[SubjectType.RADICAL.value][str(id)]["slug"]
            for id
            in radical_ids
        ]

        # format html (via static.py) to inject into card
        radical_names_str = ", ".join(radical_names)
        output += html.format(
            text=c,
            component_list=radical_names_str,
            meaning_mnemonic=kanji_entry["mm"],
            reading_mnemonic=kanji_entry["rm"]
        )
    
    return output


def on_field_filter(text: str, name: str, filter: str, context: TemplateRenderContext) -> str:
    """
    hook handler for "field_filter"

    Args:
        text (str): field text
        name (str): field name
        filter (str): filter name
        context (TemplateRenderContext): Anki render context (allows access to note)

    Returns:
        str: html to apply to field
    """

    # if kanji hint filter detected...
    if filter == config["kanji_filter"]:
        return prepare_kanji_hint(text)

    # if vocab hint filter detected...
    if filter == config["vocab_filter"]:
        field = config["vocab_field"]
        # if set, use "field"'s value instead of the text itself as the "vocab"
        if field is not None:
            note = context.note()
            return prepare_vocab_hint(text, note[field])

        # otherwise it is assumed the "vocab" is the same as the text the hint appears on
        return prepare_vocab_hint(text, text)

    return text


def on_card_render(output: TemplateRenderOutput, context: TemplateRenderContext):
    """
    hook handler for "card_did_render"

    Args:
        output (TemplateRenderOutput): Anki render output (to be edited)
        context (TemplateRenderContext): Anki render context (allows access to note)
    """

    # apply CSS to card on both sides
    headers = f"<style>{css}</style>"
    output.question_text = headers + output.question_text
    output.answer_text = headers + output.answer_text


# initialization: create and/or open cache
if not Path(CACHE_PATH).is_file():
    Path(CACHE_PATH).parent.mkdir(parents=True)  # create user_files directory
    with open(CACHE_PATH, 'w') as f:  # create and write default cache.json
        f.write(EMPTY_CACHE)
        print(f"Created local cache at {CACHE_PATH}")
with open(CACHE_PATH, 'r') as f:
    cache = json.load(f)  # store cache dict in global variable
    print(f"Opened local cache at {CACHE_PATH}")


# initialization: apply handlers to hooks
hooks.field_filter.append(on_field_filter)
hooks.card_did_render.append(on_card_render)
