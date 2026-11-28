"""
Anki Template Rendering Engine.

Templates are parsed once into a tree (text / {{field}} / {{#section}} / {{^section}}),
then rendered. Field *values* are inserted as-is and never re-parsed as template syntax,
so note content containing "{{" cannot break or inject into the template.

Supported:
  * {{Field}}, field names with spaces / unicode
  * {{#Field}}...{{/Field}}, {{^Field}}...{{/Field}} (nestable)
  * filters (chainable, applied right-to-left): text, hint, cloze, type, furigana, kana, kanji, tts
  * special fields: FrontSide, Tags, Deck, Subdeck, Card, Type, CardFlag
  * [sound:...] tags and relative <img src> rewriting to the user's media folder
"""

import re
from typing import Dict, List, Optional, Tuple, Union
from .filters import (
    cloze_answers,
    filter_cloze,
    filter_furigana,
    filter_hint,
    filter_kana,
    filter_kanji,
    filter_text,
    filter_type_answer,
    render_sound_tags,
    sanitize_html,
    strip_sound_tags,
)

_TAG = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)

# Node types: ("text", str) | ("var", token) | ("section", negated, name, children)
Node = Union[Tuple[str, str], Tuple[str, bool, str, list]]


def parse_template(template: str) -> List[Node]:
    root: List[Node] = []
    stack: List[Tuple[str, List[Node]]] = [("", root)]
    pos = 0
    for m in _TAG.finditer(template or ""):
        if m.start() > pos:
            stack[-1][1].append(("text", template[pos:m.start()]))
        pos = m.end()
        token = m.group(1).strip()
        if token.startswith("#") or token.startswith("^"):
            name = token[1:].strip()
            children: List[Node] = []
            stack[-1][1].append(("section", token[0] == "^", name, children))
            stack.append((name, children))
        elif token.startswith("/"):
            name = token[1:].strip()
            # close the matching open section (tolerate mis-nesting like Anki's legacy renderer)
            for i in range(len(stack) - 1, 0, -1):
                if stack[i][0] == name:
                    del stack[i:]
                    break
        elif token:
            stack[-1][1].append(("var", token))
    if pos < len(template or ""):
        stack[-1][1].append(("text", template[pos:]))
    return root


_EMPTY_FIELD = re.compile(r"<br\s*/?>|</?div>|&nbsp;|\s", re.IGNORECASE)


def _field_is_empty(val: Optional[str]) -> bool:
    """Anki semantics: only whitespace / <br> / <div> / &nbsp; counts as empty (an <img> is content)."""
    return not val or not _EMPTY_FIELD.sub("", val)


class TemplateRenderer:
    """Renderer for Anki card questions and answers."""

    def __init__(self, media_base_url: str = "/media"):
        self.media_base_url = media_base_url

    # ------------------------------------------------------------------
    def _lookup(self, name: str, fields: Dict[str, str]) -> Optional[str]:
        if name in fields:
            return fields[name]
        lowered = name.lower()
        for key, val in fields.items():
            if key.lower() == lowered:
                return val
        return None

    def _apply_field(
        self,
        token: str,
        fields: Dict[str, str],
        card_ord: int = 0,
        is_back: bool = False,
    ) -> str:
        """Resolve "{{filter:filter:Field}}"."""
        parts = token.split(":")
        field_name = parts[-1].strip()
        filters = [p.strip().lower() for p in parts[:-1]]
        val = self._lookup(field_name, fields)
        if val is None:
            return ""  # Anki shows an error for unknown fields; render nothing instead.

        if "type" in filters:
            expected = val
            if "cloze" in filters:
                expected = ", ".join(cloze_answers(val, card_ord))
            return filter_type_answer(expected, is_back)

        for flt in reversed(filters):
            if flt == "text":
                val = filter_text(val)
            elif flt == "hint":
                val = filter_hint(val, field_name)
            elif flt == "cloze":
                val = filter_cloze(val, card_ord, is_back)
            elif flt == "furigana":
                val = filter_furigana(val)
            elif flt == "kana":
                val = filter_kana(val)
            elif flt == "kanji":
                val = filter_kanji(val)
            elif flt.startswith("tts"):
                val = filter_text(val)  # no TTS engine on the web: show the text
            # unknown filters: pass the value through unchanged
        return val

    def _render_nodes(
        self, nodes: List[Node], fields: Dict[str, str], card_ord: int, is_back: bool
    ) -> str:
        out: List[str] = []
        for node in nodes:
            kind = node[0]
            if kind == "text":
                out.append(node[1])
            elif kind == "var":
                out.append(self._apply_field(node[1], fields, card_ord, is_back))
            else:
                _, negated, name, children = node
                val = self._lookup(name, fields)
                non_empty = not _field_is_empty(val)
                if non_empty != negated:
                    out.append(self._render_nodes(children, fields, card_ord, is_back))
        return "".join(out)

    def _render_section(
        self,
        template: str,
        fields: Dict[str, str],
        card_ord: int = 0,
        is_back: bool = False,
    ) -> str:
        return self._render_nodes(parse_template(template), fields, card_ord, is_back)

    def _rewrite_media_urls(self, html: str) -> str:
        """Rewrite relative <img src="..."> to {media_base_url}/..."""
        base = self.media_base_url.rstrip("/")

        def img_sub(m: re.Match) -> str:
            src = m.group(2)
            if src.startswith(("http://", "https://", "data:", "/")):
                return m.group(0)
            return f"{m.group(1)}{base}/{src}{m.group(3)}"

        pattern = re.compile(r'(<img[^>]+src=["\'])([^"\']+)(["\'])', re.IGNORECASE)
        return pattern.sub(img_sub, html)

    def render_card(
        self,
        qfmt: str,
        afmt: str,
        fields: Dict[str, str],
        css: str = "",
        card_ord: int = 0,
        special_fields: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Renders front HTML, back HTML, and CSS for a card.

        :param qfmt: Question template format.
        :param afmt: Answer template format.
        :param fields: Dictionary mapping field names to field values.
        :param css: Notetype CSS styling.
        :param card_ord: Card ordinal index (0-indexed).
        :param special_fields: Values for Tags / Deck / Subdeck / Card / Type / CardFlag.
        :return: Dict containing 'front_html', 'back_html', 'css'.
        """
        ctx: Dict[str, str] = {k: sanitize_html(v or "") for k, v in fields.items()}
        for key, val in (special_fields or {}).items():
            ctx.setdefault(key, sanitize_html(val or ""))

        front_rendered = self._render_section(qfmt, ctx, card_ord, is_back=False)
        front_html = self._rewrite_media_urls(render_sound_tags(front_rendered, self.media_base_url))

        back_ctx = dict(ctx)
        back_ctx["FrontSide"] = strip_sound_tags(front_rendered)
        back_rendered = self._render_section(afmt, back_ctx, card_ord, is_back=True)
        back_html = self._rewrite_media_urls(render_sound_tags(back_rendered, self.media_base_url))

        return {"front_html": front_html, "back_html": back_html, "css": css or ""}
