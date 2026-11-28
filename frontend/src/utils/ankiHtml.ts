/**
 * Helpers for showing Anki card HTML rendered by the backend (`rendered.front_html/back_html`).
 *
 * - sanitizeCardHtml(): DOMPurify pass before `v-html`. Card content comes from imported
 *   .apkg files, so it is untrusted: scripts, inline event handlers and javascript: URLs are removed.
 * - handleAnkiHtmlClick(): delegated click handler replacing the inline `onclick` Anki uses
 *   for [sound:...] buttons and {{hint:...}} links. Attach it with `@click` on the container.
 */
import DOMPurify from 'dompurify';

export function sanitizeCardHtml(html: string | null | undefined): string {
  if (!html) return '';
  return DOMPurify.sanitize(html, {
    ADD_TAGS: ['rb'], // ruby base, used by the furigana filter
    FORBID_TAGS: ['style', 'form'],
  });
}

export function handleAnkiHtmlClick(event: MouseEvent): void {
  const target = event.target as HTMLElement | null;
  if (!target) return;

  const hintLink = target.closest<HTMLElement>('[data-hint-target]');
  if (hintLink) {
    event.preventDefault();
    event.stopPropagation();
    const container = hintLink.closest('.anki-hint-container') ?? document;
    const body = container.querySelector<HTMLElement>(`#${CSS.escape(hintLink.dataset.hintTarget || '')}`);
    if (body) body.style.display = 'block';
    hintLink.style.display = 'none';
    return;
  }

  const soundButton = target.closest<HTMLElement>('[data-src]');
  if (soundButton) {
    event.preventDefault();
    event.stopPropagation();
    const src = soundButton.dataset.src || '';
    // only play same-origin media
    if (src.startsWith('/')) {
      new Audio(src).play().catch((err) => console.warn('Audio playback failed', err));
    }
  }
}
