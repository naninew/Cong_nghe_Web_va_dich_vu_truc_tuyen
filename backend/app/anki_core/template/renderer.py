"""
Anki Template Rendering Engine.
Parses mustache tokens, conditional sections, filters, and renders full HTML cards.
"""

import re
from typing import Dict, Any, Optional
from .filters import (
    filter_text,
    filter_hint,
    filter_cloze,
    render_sound_tags,
    strip_sound_tags,
)


class TemplateRenderer:
    """Renderer for Anki card questions and answers."""

    def __init__(self, media_base_url: str = "/media"):
        self.media_base_url = media_base_url

    def _apply_field(
        self,
        token: str,
        fields: Dict[str, str],
        card_ord: int = 0,
        is_back: bool = False,
    ) -> str:
        """Apply filters and return field value."""
        parts = token.split(":")
        field_name = parts[-1].strip()
        filter_names = [p.strip().lower() for p in parts[:-1]]

        val = fields.get(field_name, "")

        for flt in reversed(filter_names):
            if flt == "text":
                val = filter_text(val)
            elif flt == "hint":
                val = filter_hint(val, field_name)
            elif flt == "cloze":
                val = filter_cloze(val, card_ord, is_back)

        return val

    def _render_section(
        self,
        template: str,
        fields: Dict[str, str],
        card_ord: int = 0,
        is_back: bool = False,
    ) -> str:
        """Process conditionals and variable replacements."""
        # 1. Process Positive Conditionals: {{#FieldName}} ... {{/FieldName}}
        pos_cond_pattern = re.compile(
            r"\{\{#([\w\-\.]+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL
        )

        def replace_pos_cond(match):
            field_name = match.group(1).strip()
            content = match.group(2)
            val = fields.get(field_name, "")
            # Check if field is non-empty
            if val and val.strip():
                return self._render_section(content, fields, card_ord, is_back)
            return ""

        rendered = pos_cond_pattern.sub(replace_pos_cond, template)

        # 2. Process Negative Conditionals: {{^FieldName}} ... {{/FieldName}}
        neg_cond_pattern = re.compile(
            r"\{\{\^([\w\-\.]+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL
        )

        def replace_neg_cond(match):
            field_name = match.group(1).strip()
            content = match.group(2)
            val = fields.get(field_name, "")
            if not val or not val.strip():
                return self._render_section(content, fields, card_ord, is_back)
            return ""

        rendered = neg_cond_pattern.sub(replace_neg_cond, rendered)

        # 3. Process Variables and Filters: {{filter:Field}} or {{Field}}
        var_pattern = re.compile(r"\{\{([^#\^/].*?)\}\}")

        def replace_var(match):
            token = match.group(1).strip()
            if token == "FrontSide":
                # Special token, handled separately
                return "{{FrontSide}}"
            return self._apply_field(token, fields, card_ord, is_back)

        rendered = var_pattern.sub(replace_var, rendered)
        return rendered

    def _rewrite_media_urls(self, html: str) -> str:
        """Rewrite relative <img src="..."> to {media_base_url}/..."""
        def img_sub(m):
            prefix = m.group(1)
            src = m.group(2)
            suffix = m.group(3)
            if not (src.startswith("http://") or src.startswith("https://") or src.startswith("data:") or src.startswith("/")):
                clean_base = self.media_base_url.rstrip("/")
                return f'{prefix}{clean_base}/{src}{suffix}'
            return m.group(0)

        pattern = re.compile(r'(<img[^>]+src=["\'])([^"\']+)(["\'])', re.IGNORECASE)
        return pattern.sub(img_sub, html)

    def render_card(
        self,
        qfmt: str,
        afmt: str,
        fields: Dict[str, str],
        css: str = "",
        card_ord: int = 0,
    ) -> Dict[str, str]:
        """
        Renders front HTML, back HTML, and scoped CSS for a card.
        
        :param qfmt: Question template format.
        :param afmt: Answer template format.
        :param fields: Dictionary mapping field names to field values.
        :param css: Notetype CSS styling.
        :param card_ord: Card ordinal index (0-indexed).
        :return: Dict containing 'front_html', 'back_html', 'css'.
        """
        # Render Front
        front_rendered = self._render_section(qfmt, fields, card_ord, is_back=False)
        front_html = render_sound_tags(front_rendered, self.media_base_url)
        front_html = self._rewrite_media_urls(front_html)

        # Render Back with {{FrontSide}} replacement
        front_side_clean = strip_sound_tags(front_rendered)
        afmt_prepared = afmt.replace("{{FrontSide}}", front_side_clean)

        back_rendered = self._render_section(
            afmt_prepared, fields, card_ord, is_back=True
        )
        back_html = render_sound_tags(back_rendered, self.media_base_url)
        back_html = self._rewrite_media_urls(back_html)

        return {
            "front_html": front_html,
            "back_html": back_html,
            "css": css or "",
        }
