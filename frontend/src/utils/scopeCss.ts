/**
 * Scope an Anki notetype stylesheet to a container so it cannot restyle the app.
 *
 *   .card { color: black }        -> .anki-render { color: black }
 *   body, html { ... }            -> .anki-render { ... }
 *   .front b { ... }              -> .anki-render .front b { ... }
 *   @media (...) { .card {...} }  -> @media (...) { .anki-render {...} }
 *
 * @font-face / @keyframes / @import blocks are kept or dropped as appropriate.
 */
export function scopeCss(css: string, scope = '.anki-render'): string {
  if (!css) return '';
  const src = css.replace(/\/\*[\s\S]*?\*\//g, '').replace(/@import[^;]+;/gi, '');
  return scopeBlock(src, scope);
}

function scopeSelector(sel: string, scope: string): string {
  const s = sel.trim();
  if (!s) return '';
  if (/^(html|body|\.card)$/i.test(s)) return scope;
  if (/^(html|body)\s+/i.test(s)) return s.replace(/^(html|body)\s+/i, `${scope} `);
  if (/^\.card\b/.test(s)) return s.replace(/^\.card/, scope);
  return `${scope} ${s}`;
}

function scopeBlock(css: string, scope: string): string {
  let out = '';
  let i = 0;
  while (i < css.length) {
    const open = css.indexOf('{', i);
    if (open === -1) break;
    const prelude = css.slice(i, open).trim();

    // find the matching closing brace
    let depth = 1;
    let j = open + 1;
    while (j < css.length && depth > 0) {
      if (css[j] === '{') depth++;
      else if (css[j] === '}') depth--;
      j++;
    }
    const body = css.slice(open + 1, j - 1);

    if (/^@(media|supports)/i.test(prelude)) {
      out += `${prelude}{${scopeBlock(body, scope)}}`;
    } else if (/^@(font-face|keyframes|-webkit-keyframes)/i.test(prelude)) {
      out += `${prelude}{${body}}`;
    } else if (prelude.startsWith('@')) {
      // other at-rules (e.g. @page) are irrelevant inside a card
    } else {
      const selectors = prelude.split(',').map((s) => scopeSelector(s, scope)).filter(Boolean);
      if (selectors.length) out += `${selectors.join(', ')}{${body}}`;
    }
    i = j;
  }
  return out;
}
