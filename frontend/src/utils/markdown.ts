/**
 * Safe, zero-dependency Markdown parser and HTML sanitizer for MyLLM.
 *
 * Supports fenced code blocks, inline code, bold, italics, bullet/numbered lists,
 * and paragraphs while strictly escaping all raw HTML to prevent script injection.
 */

export interface MarkdownSegment {
  type: 'text' | 'codeblock' | 'list';
  content: string;
  language?: string;
  items?: string[];
}

export function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function parseMarkdown(rawText: string): MarkdownSegment[] {
  if (!rawText) return [];

  const segments: MarkdownSegment[] = [];
  const lines = rawText.split('\n');

  let inCodeBlock = false;
  let codeLang = '';
  let codeBuffer: string[] = [];

  let textBuffer: string[] = [];

  const flushText = () => {
    if (textBuffer.length > 0) {
      const text = textBuffer.join('\n').trim();
      if (text) {
        // Check for bullet lists
        const textLines = text.split('\n');
        const isList = textLines.every((l) => /^\s*([-*]|\d+\.)\s+/.test(l));
        if (isList && textLines.length > 0) {
          segments.push({
            type: 'list',
            content: '',
            items: textLines.map((l) => l.replace(/^\s*([-*]|\d+\.)\s+/, '').trim()),
          });
        } else {
          segments.push({
            type: 'text',
            content: text,
          });
        }
      }
      textBuffer = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        // End code block
        segments.push({
          type: 'codeblock',
          content: codeBuffer.join('\n'),
          language: codeLang || 'text',
        });
        codeBuffer = [];
        codeLang = '';
        inCodeBlock = false;
      } else {
        // Start code block
        flushText();
        inCodeBlock = true;
        codeLang = line.trim().slice(3).trim().toLowerCase();
      }
      continue;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
    } else {
      textBuffer.push(line);
    }
  }

  // Flush any remaining buffers
  if (inCodeBlock && codeBuffer.length > 0) {
    segments.push({
      type: 'codeblock',
      content: codeBuffer.join('\n'),
      language: codeLang || 'text',
    });
  } else {
    flushText();
  }

  return segments;
}

export function formatInlineMarkdown(text: string): string {
  // First escape HTML entities
  let sanitized = escapeHtml(text);

  // Inline code: `code`
  sanitized = sanitized.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

  // Bold: **text** or __text__
  sanitized = sanitized.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  sanitized = sanitized.replace(/__([^_]+)__/g, '<strong>$1</strong>');

  // Italic: *text* or _text_
  sanitized = sanitized.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  sanitized = sanitized.replace(/_([^_]+)_/g, '<em>$1</em>');

  // Line breaks
  sanitized = sanitized.replace(/\n/g, '<br />');

  return sanitized;
}
