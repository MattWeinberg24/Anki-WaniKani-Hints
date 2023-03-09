
from anki import hooks
from anki.template import TemplateRenderContext, TemplateRenderOutput

from aqt import mw

from enum import Enum

from .static import css

class HintType(str, Enum):
    RADICAL = "radical"
    # TODO: MNEMONIC = "mnemonic"

config = mw.addonManager.getConfig(__name__)


def format_hint(text: str, type: HintType, hint: str):
    new_text = f'<div id="tooltip-{type.value}" class="tooltip">'
    new_text += f"<span>{text}</span>"
    new_text += f'<div id="bottom-{type.value}" class="bottom">'
    new_text += f'<span id="{type.value}">{hint}</span>'
    new_text += "</div></div>"
    return new_text


def on_field_filter(text: str, name: str, filter: str, context: TemplateRenderContext):
    radical_filter = config["radical_filter"]

    if filter != radical_filter:
        return text
    
    return format_hint(text, HintType.RADICAL, "test")


def on_card_render(output: TemplateRenderOutput, context: TemplateRenderContext):
    headers = f"<style>{css}</style>"
    output.question_text = headers + output.question_text
    output.answer_text = headers + output.answer_text


hooks.field_filter.append(on_field_filter)
hooks.card_did_render.append(on_card_render)
