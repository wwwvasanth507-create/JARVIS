import { describe, it, expect } from 'vitest';
import { parseMarkdown, escapeHtml, formatInlineMarkdown } from '../utils/markdown';

describe('Markdown and HTML Sanitization Utility', () => {
  it('escapes dangerous HTML tags to prevent XSS injection', () => {
    const rawDangerous = '<script>alert("xss")</script><img src="x" onerror="steal()" />';
    const escaped = escapeHtml(rawDangerous);
    expect(escaped).not.toContain('<script>');
    expect(escaped).toContain('&lt;script&gt;');
    expect(escaped).not.toContain('<img');
    expect(escaped).toContain('&lt;img');
  });

  it('formats inline code with code tags', () => {
    const text = 'Use `print("hello")` to output text';
    const formatted = formatInlineMarkdown(text);
    expect(formatted).toContain('<code class="inline-code">print(&quot;hello&quot;)</code>');
  });

  it('formats bold and italic text', () => {
    const text = 'This is **bold** and *italic* text';
    const formatted = formatInlineMarkdown(text);
    expect(formatted).toContain('<strong>bold</strong>');
    expect(formatted).toContain('<em>italic</em>');
  });

  it('parses text into paragraphs and blocks', () => {
    const content = 'First paragraph.\n\nSecond paragraph.';
    const blocks = parseMarkdown(content);
    expect(blocks.length).toBe(1);
    expect(blocks[0].type).toBe('text');
    expect(blocks[0].content).toContain('First paragraph.');
    expect(blocks[0].content).toContain('Second paragraph.');
  });

  it('extracts fenced code blocks with language', () => {
    const markdown = 'Here is some code:\n```python\ndef add(a, b):\n    return a + b\n```\nDone!';
    const blocks = parseMarkdown(markdown);
    expect(blocks.length).toBe(3);
    expect(blocks[0].type).toBe('text');
    expect(blocks[0].content).toContain('Here is some code:');

    expect(blocks[1].type).toBe('codeblock');
    expect(blocks[1].language).toBe('python');
    expect(blocks[1].content).toBe('def add(a, b):\n    return a + b');

    expect(blocks[2].type).toBe('text');
    expect(blocks[2].content).toContain('Done!');
  });

  it('handles untyped code blocks gracefully', () => {
    const markdown = '```\ngeneric code\n```';
    const blocks = parseMarkdown(markdown);
    expect(blocks.length).toBe(1);
    expect(blocks[0].type).toBe('codeblock');
    expect(blocks[0].language).toBe('text');
    expect(blocks[0].content).toBe('generic code');
  });

  it('handles markdown lists safely and separates items', () => {
    const markdown = '- Item 1\n- Item 2\n- Item 3';
    const blocks = parseMarkdown(markdown);
    expect(blocks.length).toBe(1);
    expect(blocks[0].type).toBe('list');
    expect(blocks[0].items).toEqual(['Item 1', 'Item 2', 'Item 3']);
  });
});
