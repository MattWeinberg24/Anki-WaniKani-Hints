
from anki import hooks
from anki.template import TemplateRenderContext, TemplateRenderOutput
from anki.media import CheckMediaResponse

from aqt import mw, gui_hooks

from enum import Enum
import json
from pathlib import Path

from .static import css
from .api_utils import get_subject_by_slug, get_subject_by_id, SubjectError, SubjectType

class HintType(str, Enum):
    RADICAL = "radical"
    # TODO: MNEMONIC = "mnemonic"

CACHE_PATH = f"{Path(__file__).parent}/cache.json"
EMPTY_CACHE = f"""{{
    "{SubjectType.RADICAL.value}": {{}},
    "{SubjectType.KANJI.value}": {{}},
    "{SubjectType.VOCABULARY.value}": {{}}
}}"""

config = mw.addonManager.getConfig(__name__)
cache = {}

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


def format_hint(text: str, type: HintType, hint: str) -> str:
    """Formats field text such that a tooltip is added

    Args:
        text (str): previous field text
        type (HintType): type of hint being added
        hint (str): the hint to add

    Returns:
        str: updated field text (includes tooltip)
    """
    output = f'<div id="tooltip-{type.value}" class="tooltip">'
    output += f"<span>{text}</span>"
    output += f'<div id="bottom-{type.value}" class="bottom">'
    output += f'<span id="{type.value}">{hint}</span>'
    output += "</div></div>"
    return output


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
            radical_entry["image_url"] = [img["url"] for img in radical_data["character_images"] if img["content_type"] == "image/png" and img["metadata"]["dimensions"] == "32x32"][0]

            cache[SubjectType.RADICAL.value][id] = radical_entry

    cache[SubjectType.KANJI.value][slug] = kanji_entry

    # rewrite cache file
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=4)
    
    return kanji_entry


def on_field_filter(text: str, name: str, filter: str, context: TemplateRenderContext):
    radical_filter = config["radical_filter"]

    if filter != radical_filter:
        return text

    output = ""
    for c in text:
        if not is_kanji(c):
            output += c
            continue
        
        kanji_entry = {}
        if c in cache[SubjectType.KANJI.value]:
            # get the ids of radicals this kanji is composed of
            kanji_entry = cache[SubjectType.KANJI.value][c]
        else:
            # otherwise grab hints from WaniKani via API
            kanji_entry = query_cache_kanji(c)
            if isinstance(kanji_entry, SubjectError):
                print(kanji_entry)
                output += c
                continue
            
        radical_ids = kanji_entry["radical_ids"]
        # query the radical cache for each of their corresponding names
        radical_cache = cache[SubjectType.RADICAL.value]
        radical_names = [radical_cache[str(id)]["slug"] for id in radical_ids]

        radical_names_str = ", ".join(radical_names)
        output += format_hint(c, HintType.RADICAL, radical_names_str)
    
    return output


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
