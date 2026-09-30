"""Regression checks for footnote navigation and malformed input failures."""
import unittest
from xml.etree import ElementTree as ET
from export_translated_chapters_to_epub import MarkdownToXhtml, parse_footnotes


class ExporterTests(unittest.TestCase):
    def document(self, text):
        return ET.fromstring('<div xmlns:epub="http://www.idpf.org/2007/ops">' + text + '</div>')

    def test_repeated_and_nested_footnotes_have_unique_references_and_returns(self):
        renderer = MarkdownToXhtml('chapter', {'1': 'First', '2': 'Compare note [^1].'})
        tree = self.document(renderer.render(['Text [^1] and again [^1], then [^2].']))
        anchors = [e.get('id') for e in tree.iter() if e.get('id')]
        self.assertEqual(len(anchors), len(set(anchors)))
        notes = {e.get('id'): e for e in tree.iter() if e.get('{http://www.idpf.org/2007/ops}type') == 'footnote'}
        refs = [e for e in tree.iter() if e.get('{http://www.idpf.org/2007/ops}type') == 'noteref']
        self.assertEqual(len(refs), 4)
        for ref in refs:
            self.assertIn('#' + ref.get('id'), [e.get('href') for e in notes[ref.get('href')[1:]].iter('a')])

    def test_undefined_reference_fails(self):
        with self.assertRaisesRegex(ValueError, 'Undefined footnote'):
            MarkdownToXhtml('chapter', {}).render(['Missing [^1]'])

    def test_duplicate_definition_fails(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate footnote'):
            parse_footnotes(['[^1]: First', '[^1]: Second'])

    def test_markdown_link_escapes_once(self):
        tree = self.document(MarkdownToXhtml('chapter', {}).render_inline('[A & B](https://example.org/?a=1&b=2)'))
        self.assertEqual(tree.find('a').get('href'), 'https://example.org/?a=1&b=2')
        self.assertEqual(tree.find('a').text, 'A & B')

    def test_greek_and_blockquote_line_breaks_survive(self):
        tree = self.document(MarkdownToXhtml('chapter', {}).render(['> Ἐν δ’ ἔπεσ’', '> Ἕλκον νύκτα']))
        self.assertEqual(len(tree.findall('.//br')), 1)
        self.assertIn('Ἐν δ’ ἔπεσ’', ''.join(tree.itertext()))
        self.assertIn('Ἕλκον νύκτα', ''.join(tree.itertext()))

    def test_note_numbers_and_editorial_symbols(self):
        tree = self.document(MarkdownToXhtml('chapter', {'2': 'Poem', 'editorial': 'Source variant'}).render(['Text [^2] [^editorial]']))
        self.assertEqual(tree.find('.//li').get('value'), '2')
        self.assertIn('[†]', ''.join(tree.itertext()))
        self.assertEqual(tree.find('.//span').text, '†')


if __name__ == '__main__':
    unittest.main()
