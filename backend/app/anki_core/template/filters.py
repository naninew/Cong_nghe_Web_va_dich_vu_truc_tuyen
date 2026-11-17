"""
Anki Template Filters.
Supports text, hint, cloze, and sound tag parsing.
"""

import re
from typing import Dict, Any


def filter_text(value: str) -> str:
    """Strip all HTML tags from value."""
    if not value:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", "", value)
    return clean.strip()


def filter_hint(value: str, field_name: str = "Hint") -> str:
    """Wrap value in a collapsible hint container."""
    if not value or not value.strip():
        return ""
    clean_id = re.sub(r"\W+", "_", field_name).lower()
    return f"""
<div class="anki-hint-container" id="hint_wrap_{clean_id}">
    <a href="#" class="anki-hint-link" onclick="this.style.display='none';document.getElementById('hint_body_{clean_id}').style.display='block';return false;">
        Show {field_name}
    </a>
    <div class="anki-hint-body" id="hint_body_{clean_id}" style="display:none;">
        {value}
    </div>
</div>
""".strip()


def filter_cloze(value: str, card_ord: int, is_back: bool) -> str:
    """
    Render cloze deletions for a specific card ordinal (0-indexed).
    Anki cloze uses 1-indexed: {{c1::answer::hint}}.
    """
    if not value:
        return ""
    target_cloze = card_ord + 1

    def replace_cloze(match):
        cloze_num = int(match.group(1))
        answer = match.group(2)
        hint = match.group(4) if match.group(4) else ""

        if cloze_num == target_cloze:
            if is_back:
                return f'<span class="cloze">{answer}</span>'
            else:
                placeholder = f"[{hint}]" if hint else "[...]"
                return f'<span class="cloze-placeholder">{placeholder}</span>'
        else:
            # Other clozes display their answer normally
            return answer

    # Match {{c1::answer}} or {{c1::answer::hint}}
    pattern = re.compile(r"\{\{c(\d+)::(.*?)(::(.*?))?\}\}", re.DOTALL)
    return pattern.sub(replace_cloze, value)


def render_sound_tags(html: str, media_base_url: str = "/media") -> str:
    """Transform [sound:filename.mp3] into HTML5 audio player or audio button."""
    if not html:
        return ""

    def replace_sound(match):
        filename = match.group(1).strip()
        audio_src = f"{media_base_url}/{filename}"
        return f"""
<span class="anki-audio-player" data-sound="{filename}">
    <button type="button" class="audio-btn inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary-fixed text-on-primary-fixed hover:bg-primary-fixed-dim transition-all text-xs font-semibold shadow-sm active:translate-y-0.5" onclick="if(window.playAnkiAudio) {{ window.playAnkiAudio('{filename}'); }} else {{ new Audio('{audio_src}').play().catch(e=>console.warn(e)); }}">
        <span class="material-symbols-outlined text-sm leading-none">volume_up</span>
        <span>Audio</span>
    </button>
</span>
""".strip()

    pattern = re.compile(r"\[sound:(.*?)\]", re.IGNORECASE)
    return pattern.sub(replace_sound, html)


def strip_sound_tags(html: str) -> str:
    """Remove [sound:...] tags from string (used when generating {{FrontSide}})."""
    if not html:
        return ""
    return re.sub(r"\[sound:.*?\]", "", html, flags=re.IGNORECASE)
