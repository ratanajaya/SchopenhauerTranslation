# Editorial Review — v1.0.0

Reviewed September 30, 2026. Every item in the earlier review list has a
disposition below. The German extraction remains unchanged. These are
targeted checks against published witnesses, not a complete critical
collation of every sentence or every citation in Schopenhauer.

## Witnesses and method

- **G:** [Grisebach / Reclam German Volume I, 1892](https://projekt-gutenberg.org/authors/arthur-schopenhauer/books/die-welt-als-wille-und-vorstellung-band-i/). The title page and editor's remarks establish the source edition.
- **H1:** [Haldane and Kemp, *The World as Will and Idea*, Volume I, seventh edition, 1909](https://www.gutenberg.org/files/38427/38427-h/38427-h.html). Used to collate quotations and clarify extraction faults, not to replace this translation's prose.
- **H2:** [The same translation, Volume II, sixth edition, 1909](https://www.gutenberg.org/files/40097/40097-h/40097-h.html). The Kant appendix is at the beginning; this witness's English volume numbering differs from the German work.
- **E:** [Epictetus, Schenkl's Greek text, Perseus](https://github.com/PerseusDL/canonical-greekLit/tree/master/data/tlg0557): *Encheiridion* 5.1 and *Discourses* 4.1.42.
- **D:** [Diogenes Laertius, Hicks's Greek text, Perseus](https://github.com/PerseusDL/canonical-greekLit/tree/master/data/tlg0004/tlg001), Book III, discussion of the Ideas.
- **A:** [Alcinous, *Didaskalikos* 9.2, in George Boys-Stones's Greek and Latin source collection](https://drupal-s3fs-prod.s3.eu-west-1.amazonaws.com/resources/academic/1415/1067/1461/Platonist_Philosophy_Texts.pdf), printed p. 141, PDF p. 59.
- **P:** [Plato, *Sophist* 258e, Burnet's Greek text, Perseus](https://github.com/PerseusDL/canonical-greekLit/tree/master/data/tlg0059/tlg007).
- **Additional Greek witnesses:** Plato's *Timaeus*, *Phaedo*, *Republic*, and Aristotle's *Politics* in the same Perseus collection; Homer's *Iliad* VIII.485–486, XVIII.113, XXI.272 and *Odyssey* XI.620–621 there; [Aristotle, *Posterior Analytics* I.27](https://www.physics.ntua.gr/mourmouras/greats/aristoteles/analytika_ystera.html). [Perseus's dictionary](https://atlas.perseus.tufts.edu/dictionaries/entry/urn%3Acite2%3Ascaife-viewer%3Adictionary-entries.atlas_v1%3Ashort-def-2651/) confirms ἀκαταπληξία.

Exact before/after replacements are in [editorial_changes.json](editorial_changes.json).
Greek lettering uses ordinary κ, ρ, θ, φ, π and Unicode NFC. Verified passages
use polytonic spelling. Word divisions and obvious transcription faults
were collated against the witnesses before accents and breathings were
normalized editorially. Historical quotation variants remain; this
reading edition does not claim a new critical recension of all quotations.

## Disposition of previous review items

| Passage | Decision and evidence |
| --- | --- |
| **0018, §16 — Epictetus and Stoics** | Restored word divisions and letters in notes 1–2 from E; retained Latin and English renderings. The second quotation is *Discourses* IV.1.42, not III.26 as in the extract; the correction is noted. H1 confirms the other Stoic quotations. Restored συμφωνον, εμπειριαν, συμβαινοντων, normalized spelling, and repaired a literal PowerShell newline escape between Greek and Latin. Restored the missing “with nature” qualification in the Greek parenthesis. |
| **0027, §25 — Diogenes Laertius** | Checked against D and H1; restored standard lettering and polytonic spelling. Retained Schopenhauer's introductory “Plato says” paraphrase; Hicks frames the quotation differently. |
| **0043, §41 — Alcinous** | Collated *Didaskalikos* 9.2 with A and H1. Corrected ποος/προς, punctuation, and polytonic spelling, following A's αλλ’ ουδε. Checked the retained Latin gloss; repaired adjacent corum/eorum and φνσει/φύσει faults. The English preserves the quotation's distinct classes of things. |
| **0050, §48 — derogatory description** | Retained the author's words; the edition page identifies antisemitic and other derogatory generalizations as historical prejudices without endorsing them. |
| **0053, §51 — omission and notes** | H1 confirms the contrast between temporal development in poetry and the visual arts. Keep the supplied English sense with an editorial note identifying the extraction's omission; do not invent a missing German verb. Retain notes 1–3 and the explicit cross-reference from note 2 to Horace in note 1. |
| **0055, §53 — Oupnek'hat** | H1 confirms the Latin epigraph and vol. II p. 216 attribution. No Latin emendation. English now reads “At the time when knowledge appeared, love arose from the midst,” without supplying an unstated antecedent for “its.” This verifies Schopenhauer's quotation, not a Sanskrit source for Anquetil-Duperron's Latin wording. |
| **0059, §57 — ruling concern** | H1 prints πρυτανευουσα. Replaced corrupted ποντανενονοα with πρυτανεύουσα, glossed “presiding.” |
| **0065, §63 — esoteric/exoteric** | H1 explicitly distinguishes esoteric teaching and exoteric popular religion. Restored “or exoteric teaching.” The same-site German transcription retains the duplicated term and was not treated as independent corroboration. |
| **0070, §68 — mysteries** | H1 confirms σμικρα και μεγαλα μυστηρια. Restored μεγάλα and normalized σμικρὰ καὶ μεγάλα μυστήρια, retaining the English gloss. Also normalized δεύτερος πλοῦς. |
| **0073, §71 — Plato** | Compared P and H1. Repaired damaged Greek letters and οντως/ουτως; corrected Latin oppsitam/oppositam; supplied *Sophist* 258e. Retained Schopenhauer's historical quotation opening instead of silently substituting Burnet's τὴν γὰρ θατέρου. |
| **0074 — quotations and references** | H2 confirms αποσυλησας, Μωσης αττικιζων, Clement, and Metrodorus. Corrected extraction faults and the broken Aristotle infinity quotations. Restored θεωριαν and final αρετας in Stobaeus, and corrected φυχης, ρρονησιν, αωφοσυνην. Restored Simplicius's verbs, λογισμον, and Latin naturae. Historical Stobaeus grammatical variants are identified in a footnote. H2 confirms Wolff's Cosmologia I.2 §93 and Ontologia §178 references; no separate Latin Wolff quotation occurs in the current extract, so the earlier blanket warning was reclassified rather than inventing a quotation. |
| **0074 — Bruno poem** | H2 prints four consecutive lines in one note. Reunited them and their English rendering in note 2; removed note 1, an extraction split of the final two lines, and its nested reference. The complete poem remains. |
| **0007, 0009, 0010, 0022 — Greek policy** | H1 supplies corresponding historical quotations. Retained their words; standardized glyphs, polytonic spelling, and Unicode throughout. The Parmenides quotation keeps Schopenhauer's historical wording rather than replacing it with another modern recension. |
| **Titles, names, historical pagination** | Use the glossary and *The World as Will and Representation*. Grisebach is editor of the German source; Ratanajaya is translator and publisher of this edition. Historical page references remain historical references, not a modern critical-edition concordance. |

## Reader-facing limitations

The expanded Greek audit also repaired the Aristotle quotation in §15,
Plato's book III epigraph and quotations in §§31–32, Homer's lines in §51
and §§55–57, the Pythagorean number quotation in §52, and other Greek
quotations and technical terms. The epigraph's combination of *Timaeus*
27d–28a is explained in a footnote. Schopenhauer's condensed Plato and
Aristotle quotations are retained as quotations in his work, rather than
expanded into the full ancient passages. In the appendix, the missing
δυνατῶν in the Diodorus–Chrysippus discussion is restored; the English
“becomes possible” is emended to “becomes actual,” following H2. The German
extract itself has the defective reading; the emendation is explained in
a footnote and agrees with the surrounding argument. For ἀκαταπληξία, the standard dictionary form
replaces the historical ακαταπληξις; this is an explicit orthographic
emendation, not a change to the English argument.

The final prose scan found the earlier §39 note preserving two known
transcription errors in the *Hamlet* excerpt. “thon” and “beffets” are now
“thou” and “buffets,” checked against the [Folger Shakespeare Library,
Act 3, scene 2](https://www.folger.edu/explore/shakespeares-works/hamlet/read/3/2/).
The reader's note records the correction instead of preserving corrupt text.

The §51 omission is explained at the passage. Historical wording in the
appendix's Stobaeus quotation is marked explicitly. These are documented
source limitations rather than unidentified extraction corruption. The
edition note describes the collation and contextualizes the author's
prejudices. Every ancient quotation has not been newly edited from
manuscripts, and every bibliographic citation has not been independently
reconstructed in its original edition.
