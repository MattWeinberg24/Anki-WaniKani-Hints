
from anki import hooks
from anki.template import TemplateRenderContext, TemplateRenderOutput
from anki.media import CheckMediaResponse

from aqt import mw, gui_hooks

from enum import Enum
import json
from pathlib import Path

from .static import css
from .api_utils import get_radicals_from_kanji, SubjectError

class HintType(str, Enum):
    RADICAL = "radical"
    # TODO: MNEMONIC = "mnemonic"

# initialization
config = mw.addonManager.getConfig(__name__)
cache = {}
cache_is_updated = False
cache_path = Path("./cache.json")
if not cache_path.is_file():
    with open(cache_path.name, 'w') as f:
        f.write("{}")
        print("Created local cache")
else:
    with open(cache_path.name, 'r') as f:
        cache = json.load(f)

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


def on_field_filter(text: str, name: str, filter: str, context: TemplateRenderContext):
    radical_filter = config["radical_filter"]

    if filter != radical_filter:
        return text

    token = config["token"]
    output = ""
    for c in text:
        if not is_kanji(c):
            output += c
            continue
        
        radical_names = ""
        # check local cache for existing hint
        if c in cache:
            radical_names = cache[c]
            print(f"{c} located in cache!")
        # otherwise grab hints from WaniKani via API
        else:
            radicals = get_radicals_from_kanji(c, token)
            if isinstance(radicals, SubjectError):
                output += c
                print(radicals)
                continue
            radical_names = ", ".join([r[0] for r in radicals])
            # add to cache
            cache[c] = radical_names
            print(f"writing {c} to cache")
            with open(cache_path.name, "w") as f:
                json.dump(cache, f, indent=4)

        output += format_hint(c, HintType.RADICAL, radical_names)
    
    return output
hooks.field_filter.append(on_field_filter)


def on_card_render(output: TemplateRenderOutput, context: TemplateRenderContext):
    headers = f"<style>{css}</style>"
    output.question_text = headers + output.question_text
    output.answer_text = headers + output.answer_text
hooks.card_did_render.append(on_card_render)
