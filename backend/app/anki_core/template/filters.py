"""
Anki Template Filters.
Supports text, hint, cloze, type, furigana/kana/kanji, tts, sound tags and field sanitising.
"""

import html
import re
from itertools import count
from typing import List
from urllib.parse import quote

_hint_ids = count(1)

# ---------------------------------------------------------------------------
# Sanitising (field content comes from imported .apkg files = untrusted)
# ---------------------------------------------------------------------------
_DANGEROUS_BLOCKS = re.compile(
    r"<\s*(script|iframe|object|embed|frame|frameset|base|meta|link)\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_DANGEROUS_SINGLE = re.compile(
    r"<\s*/?\s*(script|iframe|object|embed|frame|frameset|base|meta|link)\b[^>]*>", re.IGNORECASE
)
_EVENT_ATTR = re.compile(r"\s+on[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.IGNORECASE)
_JS_URL = re.compile(
    r"(\s(?:href|src|xlink:href|action|formaction)\s*=\s*[\"']?)\s*(?:javascript\s*:|vbscript\s*:|data:text/html)[^\"'\s>]*",
    re.IGNORECASE,
)


def sanitize_html(value: str) -> str:
    """Remove scripts, embedded frames, inline event handlers and javascript: URLs."""
    if not value:
        return ""
    value = _DANGEROUS_BLOCKS.sub("", value)
    value = _DANGEROUS_SINGLE.sub("", value)
    value = _EVENT_ATTR.sub("", value)
    value = _JS_URL.sub(r"\1#", value)
    return value


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
def filter_text(value: str) -> str:
    """Strip all HTML tags and decode entities."""
    if not value:
        return ""
    clean = re.sub(r"<[^>]+>", "", value)
    return html.unescape(clean).strip()


def filter_hint(value: str, field_name: str = "Hint") -> str:
    """
    Collapsible hint. No inline JavaScript: the link carries ``data-hint-target`` and the
    study page opens it with a delegated click handler (inline handlers are stripped by DOMPurify).
    """
    if not value or not value.strip():
        return ""
    body_id = f"hint_body_{next(_hint_ids)}"
    label = html.escape(field_name)
    return (
        f'<div class="anki-hint-container">'
        f'<a href="#" class="anki-hint-link" data-hint-target="{body_id}">Show {label}</a>'
        f'<div class="anki-hint-body" id="{body_id}" style="display:none;">{value}</div>'
        f"</div>"
    )


_CLOZE = re.compile(r"\{\{c(\d+)::(.*?)(?:::(.*?))?\}\}", re.DOTALL)


def filter_cloze(value: str, card_ord: int, is_back: bool) -> str:
    """
    Render cloze deletions for a specific card ordinal (0-indexed).
    Anki cloze uses 1-indexed: {{c1::answer::hint}}.
    """
    if not value:
        return ""
    target = card_ord + 1

    def replace(m: re.Match) -> str:
        num, answer, hint = int(m.group(1)), m.group(2), m.group(3)
        if num != target:
            return answer
        if is_back:
            return f'<span class="cloze">{answer}</span>'
        placeholder = f"[{hint}]" if hint else "[...]"
        return f'<span class="cloze cloze-placeholder">{placeholder}</span>'

    return _CLOZE.sub(replace, value)


def cloze_answers(value: str, card_ord: int) -> List[str]:
    """Answers of the active cloze (used by {{type:cloze:Field}})."""
    target = card_ord + 1
    return [m.group(2) for m in _CLOZE.finditer(value or "") if int(m.group(1)) == target]


def filter_type_answer(expected: str, is_back: bool) -> str:
    """
    {{type:Field}}: an input box on the front, the correct answer on the back.
    Never leaks the answer on the front side.
    """
    if not is_back:
        return '<input type="text" class="anki-typeans" autocomplete="off" placeholder="Nhập đáp án..." />'
    return f'<div class="anki-typeans-answer"><code>{html.escape(filter_text(expected))}</code></div>'


# Anki furigana syntax: "漢字[かんじ]" (an optional space separates groups)
_FURIGANA = re.compile(r" ?([^ >]+?)\[(.+?)\]")


def _furigana_sub(value: str, fmt) -> str:
    def repl(m: re.Match) -> str:
        if m.group(2).startswith("sound:"):
            return m.group(0)
        return fmt(m.group(1), m.group(2))

    return _FURIGANA.sub(repl, value or "")


def filter_furigana(value: str) -> str:
    return _furigana_sub(value, lambda base, ruby: f"<ruby><rb>{base}</rb><rt>{ruby}</rt></ruby>")


def filter_kanji(value: str) -> str:
    return _furigana_sub(value, lambda base, ruby: base)


def filter_kana(value: str) -> str:
    return _furigana_sub(value, lambda base, ruby: ruby)


# ---------------------------------------------------------------------------
# Sound tags
# ---------------------------------------------------------------------------
def render_sound_tags(html_str: str, media_base_url: str = "/media") -> str:
    """
    Transform [sound:filename.mp3] into an audio button (filename safely escaped).
    No inline JavaScript: the study page plays ``data-src`` via a delegated click handler.
    """
    if not html_str:
        return ""

    def replace_sound(match: re.Match) -> str:
        filename = match.group(1).strip()
        src = f"{media_base_url.rstrip('/')}/{quote(filename)}"
        return (
            f'<span class="anki-audio-player" data-sound="{html.escape(filename, quote=True)}">'
            f'<button type="button" class="audio-btn inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full '
            f'bg-primary-fixed text-on-primary-fixed hover:bg-primary-fixed-dim transition-all text-xs font-semibold '
            f'shadow-sm active:translate-y-0.5" data-src="{html.escape(src, quote=True)}">'
            f'<span class="material-symbols-outlined text-sm leading-none">volume_up</span><span>Audio</span>'
            f"</button></span>"
        )

    return re.sub(r"\[sound:(.*?)\]", replace_sound, html_str, flags=re.IGNORECASE)


def strip_sound_tags(html_str: str) -> str:
    """Remove [sound:...] tags from string (used when generating {{FrontSide}})."""
    if not html_str:
        return ""
    return re.sub(r"\[sound:.*?\]", "", html_str, flags=re.IGNORECASE)
