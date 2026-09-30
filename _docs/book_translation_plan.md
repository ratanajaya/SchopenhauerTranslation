# English Translation Plan

Status: content files 0001–0074 are translated. The v1.0.0 release package is prepared locally in `dist/`; [editorial review](human_review_notes.md) and [release validation](release-validation.md) record the publication checks. These 74 files contain the front matter, four books (§§1–71), and the Kant appendix.

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
16. `chapter-0016.md` - section 14, science, proof, evidence, and judgment
17. `chapter-0017.md` - section 15, mathematics, error, explanation, and philosophy
18. `chapter-0018.md` - section 16, practical reason and Stoic ethics
19. `chapter-0019.md` - section 17, opening of Book Two and objectivation of the will
20. `chapter-0020.md` - section 18, body as objecthood of the will
21. `chapter-0021.md` - section 19, analogy from one's own body to will in nature
22. `chapter-0022.md` - section 20, motives, physiology, and body as objecthood of the will
23. `chapter-0023.md` - section 21, will as thing in itself and inner essence of nature
24. `chapter-0024.md` - section 22, expansion of the concept will beyond force
25. `chapter-0025.md` - section 23, groundlessness, necessity, stimuli, and inorganic forces as will
26. `chapter-0026.md` - section 24, forms of cognition, limits of aetiology, and will as inner essence
27. `chapter-0027.md` - section 25, unity of will, grades of objectivation, and Plato's Ideas
28. `chapter-0028.md` - section 26, natural forces, laws of nature, and occasional causes
29. `chapter-0029.md` - section 27, aetiology, vital force, conflict among grades of will, and cognition
30. `chapter-0030.md` - section 28, unity of will, teleology, inner and outer purposiveness
31. `chapter-0031.md` - section 29, end of Book Two, will as endless striving
32. `chapter-0032.md` - section 30, opening of Book Three, Platonic Idea as object of art
33. `chapter-0033.md` - section 31, Kant's thing in itself and Plato's Ideas
34. `chapter-0034.md` - section 32, Idea as adequate objecthood and time as fragmented view of the eternal Ideas
35. `chapter-0035.md` - section 33, cognition serving the will and the subject's change in aesthetic cognition
36. `chapter-0036.md` - section 34, pure will-less subject of cognition and aesthetic contemplation of the Idea
37. `chapter-0037.md` - section 35, Ideas distinguished from their appearances in nature and history
38. `chapter-0038.md` - section 36, art, genius, imagination, and the kinship of genius with madness
39. `chapter-0039.md` - section 37, shared aesthetic receptivity and art as an aid to cognition of the Idea
40. `chapter-0040.md` - section 38, will-free aesthetic pleasure and its subjective condition
41. `chapter-0041.md` - section 39, the beautiful and sublime, their degrees, and sublime character
42. `chapter-0042.md` - section 40, the alluring and the disgusting as obstacles to aesthetic contemplation
43. `chapter-0043.md` - section 41, beauty, the Idea, and the aesthetic expression of materials
44. `chapter-0044.md` - section 42, subjective and objective sources of aesthetic enjoyment
45. `chapter-0045.md` - section 43, architecture and waterworks as expressions of material forces
46. `chapter-0046.md` - section 44, gardening, landscape painting, and animal depiction
47. `chapter-0047.md` - section 45, human beauty, grace, and individual character
48. `chapter-0048.md` - section 46, why sculpture cannot depict Laocoön's cry
49. `chapter-0049.md` - section 47, drapery in sculpture and clarity in writing
50. `chapter-0050.md` - section 48, history painting, inner significance, and resignation
51. `chapter-0051.md` - section 49, Idea and concept, genuine art and imitation
52. `chapter-0052.md` - section 50, allegory and symbol in visual art and poetry
53. `chapter-0053.md` - section 51, poetry, lyric song, character, and tragedy
54. `chapter-0054.md` - section 52, music as an immediate image of the will
55. `chapter-0055.md` - section 53, opening of Book Four and philosophy's immanent ethical inquiry
56. `chapter-0056.md` - section 54, life, death, the present, and affirmation or denial of the will
57. `chapter-0057.md` - section 55, freedom, necessity, and intelligible, empirical, and acquired character
58. `chapter-0058.md` - section 56, endless striving and the essential suffering of life
59. `chapter-0059.md` - section 57, pain and boredom as the poles of human life
60. `chapter-0060.md` - section 58, negative happiness, art, and the emptiness of ordinary life
61. `chapter-0061.md` - section 59, experiential confirmation of suffering and critique of optimism
62. `chapter-0062.md` - section 60, affirmation of the will, procreation, and eternal justice
63. `chapter-0063.md` - section 61, egoism and the will's conflict with itself
64. `chapter-0064.md` - section 62, injustice, property, right, the state, and punishment
65. `chapter-0065.md` - section 63, eternal justice, individuation, and the myth of transmigration
66. `chapter-0066.md` - section 64, retribution, conscience, and self-sacrificing vengeance
67. `chapter-0067.md` - section 65, good and evil, malice, and anguish of conscience
68. `chapter-0068.md` - section 66, intuitive cognition, justice, beneficence, and compassion
69. `chapter-0069.md` - section 67, love as compassion and the account of weeping
70. `chapter-0070.md` - section 68, denial of the will to live and the two paths to resignation
71. `chapter-0071.md` - section 69, suicide and its distinction from denial of the will
72. `chapter-0072.md` - section 70, necessity, freedom, and the Christian doctrines of grace and rebirth
73. `chapter-0073.md` - section 71, relative nothingness and the close of Book Four
74. `chapter-0074.md` - appendix, critique of Kantian philosophy
