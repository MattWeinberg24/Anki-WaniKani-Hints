# anki/qt dependencies
from anki import hooks
from anki.template import TemplateRenderContext, TemplateRenderOutput
from aqt import mw

# general python dependencies
import json
from pathlib import Path

# custom dependencies
from .api_utils import get_subject_by_slug, get_subject_by_id, SubjectError, SubjectType
from .static import html, css
from .util import is_kanji

CACHE_PATH = f"{Path(__file__).parent}/cache.json"
EMPTY_CACHE = f"""{{
    "{SubjectType.RADICAL.value}": {{}},
    "{SubjectType.KANJI.value}": {{}},
    "{SubjectType.VOCABULARY.value}": {{}}
}}"""

config = mw.addonManager.getConfig(__name__)
cache = {}

def query_cache_vocab(slug: str) -> dict | SubjectError:
    """
    Query the WaniKani API for information on the provided vocabulary,
    then add relevant data to the local cache

    Args:
        slug (str): vocabulary string

    Returns:
        dict | SubjectError: newly cached vocabulary data entry if success, SubjectError if fail
    """

    token = config["token"]
    # query WaniKani API for vocab data
    vocab_data = get_subject_by_slug(SubjectType.VOCABULARY, slug, token)
    if isinstance(vocab_data, SubjectError):
        return vocab_data

    # build vocab cache entry
    vocab_entry = {}
    vocab_entry["mm"] = vocab_data["meaning_mnemonic"]
    vocab_entry["rm"] = vocab_data["reading_mnemonic"]

    cache[SubjectType.VOCABULARY.value][slug] = vocab_entry

    # rewrite cache file
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=4)
    
    return vocab_entry


def query_cache_kanji(slug: str) -> dict | SubjectError:
    """
    Query the WaniKani API for information on the provided kanji and its radicals,
    then add relevant data to the local cache

    Args:
        slug (str): kanji character

    Returns:
        dict | SubjectError: newly cached kanji data entry if success, SubjectError if fail
    """

    token = config["token"]
    # query WaniKani API for kanji data
    kanji_data = get_subject_by_slug(SubjectType.KANJI, slug, token)
    if isinstance(kanji_data, SubjectError):
        # if kanji not in WaniKani, cache a special value
        if kanji_data == SubjectError.INVALID_SLUG:
            cache[SubjectType.KANJI.value][slug] = None
            # rewrite cache file
            with open(CACHE_PATH, "w") as f:
                json.dump(cache, f, indent=4)
        return kanji_data

    # build kanji cache entry
    kanji_entry = {}
    kanji_entry["mm"] = kanji_data["meaning_mnemonic"]
    kanji_entry["rm"] = kanji_data["reading_mnemonic"]
    kanji_entry["radical_ids"] = kanji_data["component_subject_ids"]

    # get data for all radicals the kanji is composed of
    for id in kanji_entry["radical_ids"]:
        # if radical data not in cache...
        if id not in cache[SubjectType.RADICAL.value]:
            # query WaniKani API for radical data
            radical_data = get_subject_by_id(id, token)
            if isinstance(radical_data, SubjectError):
                return radical_data

            #build radical cache entry
            radical_entry = {}
            radical_entry["slug"] = radical_data["slug"]
            radical_entry["mm"] = radical_data["meaning_mnemonic"]
            radical_entry["chr"] = radical_data["characters"]
            if len(radical_data["character_images"]) > 0:
                radical_entry["image_url"] = [img["url"]
                    for img in radical_data["character_images"] 
                    if img["content_type"] == "image/png"
                    and img["metadata"]["dimensions"] == "32x32"
                ][0]

            # cache the radical entry (note: `id` key gets converted to string for json)
            cache[SubjectType.RADICAL.value][str(id)] = radical_entry

    cache[SubjectType.KANJI.value][slug] = kanji_entry

    # rewrite cache file
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=4)
    
    return kanji_entry


def prepare_kanji_hint(text: str) -> str:
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
        radical_cache = cache[SubjectType.RADICAL.value]
        radical_names = [radical_cache[str(id)]["slug"] for id in radical_ids]

        # format html (via static.py) to inject into card
        radical_names_str = ", ".join(radical_names)
        output += html.format(
            text=c,
            radical_list=radical_names_str,
            meaning_mnemonic=kanji_entry["mm"],
            reading_mnemonic=kanji_entry["rm"])
    
    return output


def on_field_filter(text: str, name: str, filter: str, context: TemplateRenderContext):
    if filter == config["kanji_filter"]:
        return prepare_kanji_hint(text)
    if filter == config["vocab_filter"]:
        # TODO: implement vocab hints
        return text
    
    return text


def on_card_render(output: TemplateRenderOutput, context: TemplateRenderContext):
    headers = f"<style>{css}</style>"
    output.question_text = headers + output.question_text
    output.answer_text = headers + output.answer_text


# initialization: create and/or open cache
if not Path(CACHE_PATH).is_file():
    with open(CACHE_PATH, 'w') as f:
        f.write(EMPTY_CACHE)
        print(f"Created local cache at {CACHE_PATH}")
with open(CACHE_PATH, 'r') as f:
    cache = json.load(f)
    print(f"Opened local cache at {CACHE_PATH}")


# initialization: apply handlers to hooks
hooks.field_filter.append(on_field_filter)
hooks.card_did_render.append(on_card_render)
