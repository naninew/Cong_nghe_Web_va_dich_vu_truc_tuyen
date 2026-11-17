"""
Anki Search Query Parser.
Parses query strings like 'deck:"Japanese" is:due tag:JLPT_N3' into structured filter predicates.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ParsedSearchQuery(BaseModel):
    deck_names: List[str] = []
    tags: List[str] = []
    is_due: bool = False
    is_new: bool = False
    is_learn: bool = False
    is_review: bool = False
    is_suspended: Optional[bool] = None
    is_buried: Optional[bool] = None
    flag: Optional[int] = None
    rated_days: Optional[int] = None
    text_terms: List[str] = []


class SearchQueryParser:
    """Parses Anki query strings into structured search parameters."""

    # Tokenizes respecting quoted substrings
    TOKEN_REGEX = re.compile(r'([^\s":]+:"[^"]*"|[^\s":]+:[^\s]+|"[^"]*"|[^\s]+)')

    @classmethod
    def parse(cls, query_str: str) -> ParsedSearchQuery:
        if not query_str or not query_str.strip():
            return ParsedSearchQuery()

        result = ParsedSearchQuery()
        tokens = cls.TOKEN_REGEX.findall(query_str.strip())

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            if token.lower().startswith("deck:"):
                raw_val = token[5:]
                clean_val = raw_val.strip('"')
                result.deck_names.append(clean_val)

            elif token.lower().startswith("tag:"):
                raw_val = token[4:]
                clean_val = raw_val.strip('"')
                result.tags.append(clean_val)

            elif token.lower().startswith("is:"):
                val = token[3:].lower().strip('"')
                if val == "due":
                    result.is_due = True
                elif val == "new":
                    result.is_new = True
                elif val == "learn":
                    result.is_learn = True
                elif val == "review":
                    result.is_review = True
                elif val == "suspended":
                    result.is_suspended = True
                elif val == "buried":
                    result.is_buried = True

            elif token.lower().startswith("-is:"):
                val = token[4:].lower().strip('"')
                if val == "suspended":
                    result.is_suspended = False
                elif val == "buried":
                    result.is_buried = False

            elif token.lower().startswith("flag:"):
                try:
                    result.flag = int(token[5:].strip('"'))
                except ValueError:
                    pass

            elif token.lower().startswith("rated:"):
                try:
                    result.rated_days = int(token[6:].strip('"'))
                except ValueError:
                    pass

            else:
                # Text match term
                clean_term = token.strip('"')
                if clean_term:
                    result.text_terms.append(clean_term)

        return result
