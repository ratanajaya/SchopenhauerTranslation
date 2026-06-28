# English Translation Plan

## Project Goal

Translate the full book from German into clear, modern English while preserving the seriousness, precision, and philosophical force of the original. The translation should be easier for a present-day reader to follow, but it should not flatten Schopenhauer's argument, simplify technical distinctions, or turn the prose into paraphrase.

The work will proceed sequentially, chapter by chapter, using the Markdown files in `original-epub-extract-md` as the source text.

Each translated file should keep the same base filename unless a later publishing step requires a different naming scheme. Recommended output folder: `english-translation`.

## Translation Style

Use modern, easily understood English sentences wherever possible. Long German periods should often be divided into two or more English sentences, but only where doing so improves clarity without changing the chain of thought.

Preserve philosophical density. When a sentence carries a careful distinction, do not replace it with a loose summary. Make the reasoning explicit in fluent English.

Prefer direct, contemporary vocabulary over archaic English, except where a technical term has an established translation. For example, use "consciousness" rather than "consciousness of self" unless the German specifically requires the longer phrase.

Retain key Schopenhauer terms consistently. Before changing a recurring term, check `_docs/translation_glossary_notes.md`.

This is not a one-to-one sentence or paragraph translation. The English version should be edited as readable English prose: break up long source paragraphs and shape the argument into clear units of thought. Keep the full meaning, sequence of reasoning, and technical vocabulary.

When improving the writing, favor clarity over literal syntax. Recast long German constructions into natural English order, divide overloaded sentences, and use paragraph breaks to mark transitions between thesis, explanation, example, contrast, and conclusion.

## Quotes And Foreign-Language Passages

German text should be translated into English.

Non-German quotes should remain intact in the body text. Add an English translation immediately after the quote, using this format:

```markdown
> `Sors de l'enfance, ami, réveille-toi!`
> Translation: Leave childhood behind, friend; wake up!
```

For short inline non-German phrases, keep the original phrase and add the English translation in parentheses:

```markdown
`a priori` (prior to experience)
```

If a non-German passage already has a source footnote or explanatory note, preserve that note and add the English translation without deleting the original.

If the original uses Latin or French as a technical phrase that is standard in philosophy, keep it in italics or code style as already marked, then add a translation only the first time it appears in a chapter unless clarity calls for repetition.

## Paragraph Formatting

Keep one blank line between paragraphs.

Use paragraphing as an editorial tool. A source paragraph may become several English paragraphs when the original contains multiple conceptual moves. Good break points include: a new claim, a supporting example, a contrast introduced by "however" or "by contrast," a quoted passage, a return to the main argument, or a concluding formulation.

Keep Markdown headings as headings. Do not bury section numbers or book divisions inside paragraphs.

Keep mottoes, epigraphs, and stand-alone quotations as blockquotes.

Convert line breaks inside title pages, signatures, and verse-like quotes into readable Markdown line breaks or separate lines.

Keep footnotes as Markdown footnotes. If a footnote is German, translate it. If it contains a non-German quote, keep the original quote and add an English translation.

## Chapter Workflow

For each chapter:

1. Read the full source chapter before translating.
2. Check the glossary and continuity notes for recurring terms, names, works, and prior decisions.
3. Draft the English translation in the matching output file.
4. Preserve all headings, footnotes, mottoes, and significant paragraph breaks, while adding new paragraph breaks where English readability requires them.
5. Add translations after non-German quotes.
6. Review the chapter for clarity, consistency, and paragraph flow.
7. Update `_docs/translation_glossary_notes.md` with new decisions, uncertain terms, recurring names, and cross-chapter continuity notes.

## Review Passes

Each chapter should receive three passes:

1. Translation pass: produce a complete English draft.
2. Editorial pass: smooth sentence flow, modernize syntax, improve paragraphing, and check that no argument has been softened or skipped.
3. Continuity pass: check recurring terms, quotes, names, and footnotes against the glossary.

## Consistency Rules

Use the glossary as the source of truth for recurring terms.

Do not silently change established translations of key terms. If a better translation becomes necessary, record the change in the glossary and note which prior chapters may need revision.

Keep proper names and work titles consistent. When a title has a widely recognized English version, prefer that version and record it.

Track uncertain choices rather than resolving them casually. A note marked "Review later" is better than an inconsistent translation.

## File And Folder Plan

Recommended translation output:

```text
english-translation/
  chapter-0001.md
  chapter-0002.md
  ...
  chapter-0074.md
```

Documentation:

```text
_docs/
  book_translation_plan.md
  translation_glossary_notes.md
```

## Definition Of Done

The whole-book translation is complete when:

1. Every source chapter has a matching English Markdown file.
2. All German prose has been translated into English.
3. All non-German quotes remain intact and have English translations.
4. Paragraphs, headings, mottoes, and footnotes are cleanly formatted.
5. The glossary and continuity notes cover the major recurring terms, names, titles, and editorial decisions.
6. A final consistency pass has been completed across all chapters.


## Translated files

1. `chapter-0001.md` - title/front matter
2. `chapter-0002.md` - editor's notes and prefaces
3. `chapter-0003.md` - opening of Book One, section 1
4. `chapter-0004.md` - section 2, subject and object
5. `chapter-0005.md` - section 3, intuitive and abstract representation
6. `chapter-0006.md` - section 4, matter, causality, and understanding
7. `chapter-0007.md` - section 5, external world, dreams, and will
8. `chapter-0008.md` - section 6, body, animal understanding, and semblance
9. `chapter-0009.md` - section 7, representation as starting point
10. `chapter-0010.md` - section 8, reflection, concepts, and reason
11. `chapter-0011.md` - section 9, concepts, logic, and persuasion
12. `chapter-0012.md` - section 10, certainty, knowledge, and science
13. `chapter-0013.md` - section 11, feeling as non-conceptual consciousness
14. `chapter-0014.md` - section 12, abstract knowledge, application, and intuition
15. `chapter-0015.md` - section 13, laughter, wit, foolishness, and pedantry
