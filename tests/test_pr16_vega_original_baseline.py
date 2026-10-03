"""原作専用reader・181件identity・Wiki表の境界。既受入officialは再実行しない。"""
import csv
import io
import struct
import unittest

from tools.pr16_vega_original_baseline import (
    ROM_BASE, OriginalRom, SourceError, index_records, join_roster,
    page_url, parse_tables,
)


class WikiTests(unittest.TestCase):
    def test_index_join_links_and_dex(self):
        raw = ('<h2>ポケモン図鑑V</h2><table><tr><th>No.</th><th>名前</th></tr>'
               '<tr><td>001</td><td><a href="/altair1/pages/100.html">リープン</a></td></tr></table>').encode()
        self.assertEqual(index_records(parse_tables(raw)), [
            {'dex_no': 1, 'name_ja': 'リープン', 'url': 'https://w.atwiki.jp/altair1/pages/100.html'}])

    def test_span_and_order_preserved(self):
        result = parse_tables(b'<h3>Level</h3><table><tr><td rowspan="2">1</td><td>a<br>b</td></tr></table>')
        self.assertEqual(result[0]['heading'], 'Level')
        self.assertEqual(result[0]['rows'][0][0]['rowspan'], '2')
        self.assertEqual(result[0]['rows'][0][1]['text'], 'a\nb')

    def test_foreign_url_rejected(self):
        for url in ('https://evil.test/a', 'http://w.atwiki.jp/altair1/pages/19.html',
                    'https://w.atwiki.jp/altair1/pages/19.html?x=1', '/altair1/pages/../a'):
            with self.subTest(url=url), self.assertRaises(SourceError):
                page_url(url)

    def test_missing_table_rejected(self):
        with self.assertRaises(SourceError):
            index_records(parse_tables(b'<p>No.</p>'))

    def test_unclosed_table_rejected(self):
        with self.assertRaises(SourceError):
            parse_tables(b'<table><tr><td>a</td></tr>')

    def test_duplicate_index_rejected(self):
        raw = b'<table><tr><th>No.</th><th>Name</th></tr>' + b'<tr><td>1</td><td><a href="/altair1/pages/10.html">a</a></td></tr>' * 2 + b'</table>'
        with self.assertRaises(SourceError):
            index_records(parse_tables(raw))


class RomTests(unittest.TestCase):
    def test_packed_level_order_and_duplicates_preserved(self):
        raw = struct.pack('<HHHH', 10 | (1 << 9), 10 | (1 << 9), 20 | (8 << 9), 65535)
        rows = OriginalRom(raw).levels(ROM_BASE)
        self.assertEqual([(r['move_id'], r['level'], r['order']) for r in rows], [(10, 1, 0), (10, 1, 1), (20, 8, 2)])
        self.assertEqual(rows[2]['source_offset'], 4)

    def test_empty_level_is_explicit(self):
        self.assertEqual(OriginalRom(b'\xff\xff').levels(ROM_BASE), [])

    def test_missing_level_terminator_rejected(self):
        with self.assertRaises(SourceError):
            OriginalRom(struct.pack('<H', 1) * 256).levels(ROM_BASE)

    def test_outside_pointer_rejected(self):
        for address, length in ((ROM_BASE - 1, 1), (ROM_BASE, 5), (ROM_BASE, -1)):
            with self.subTest(address=address, length=length), self.assertRaises(SourceError):
                OriginalRom(b'0000').read(address, length)

    def test_level_zero_move_and_level_over_100_rejected(self):
        for value in (0, 1 | (101 << 9)):
            with self.subTest(value=value), self.assertRaises(SourceError):
                OriginalRom(struct.pack('<HH', value, 65535)).levels(ROM_BASE)

    def test_egg_sequence_and_explicit_empty(self):
        raw = struct.pack('<HHHHH', 20001, 10, 10, 20002, 65535)
        rows = OriginalRom(raw).eggs(ROM_BASE)
        self.assertEqual([r['move_id'] for r in rows[1]], [10, 10])
        self.assertEqual(rows[2], [])

    def test_duplicate_egg_header_rejected(self):
        with self.assertRaises(SourceError):
            OriginalRom(struct.pack('<HHH', 20001, 20001, 65535)).eggs(ROM_BASE)

    def test_egg_without_species_rejected(self):
        with self.assertRaises(SourceError):
            OriginalRom(struct.pack('<HH', 10, 65535)).eggs(ROM_BASE)

    def test_egg_species_outside_frozen_prefix_rejected(self):
        with self.assertRaises(SourceError):
            OriginalRom(struct.pack('<HH', 20412, 65535)).eggs(ROM_BASE)


class RosterTests(unittest.TestCase):
    def fixture(self):
        fields = ['species_key', 'id', 'vega_id', 'classification', 'is_official', 'form_key', 'canonical_national_dex', 'display_name']
        stream = io.StringIO(); writer = csv.DictWriter(stream, fields); writer.writeheader()
        pending, index = [], []
        for sid in range(1, 182):
            key, name = f'KEY_{sid}', f'名前{sid}'
            writer.writerow(dict(species_key=key, id=sid, vega_id=sid, classification='VEGA_ORIGINAL', is_official='false', form_key='', canonical_national_dex=0, display_name=name))
            pending.append(dict(species_key=key, species_id=sid, vega_id=sid))
            index.append(dict(name_ja=name, dex_no=200 + sid, url=f'https://w.atwiki.jp/altair1/pages/{sid}.html'))
        return stream.getvalue().encode(), {'records': pending, 'imported_from_preservation_rows': 0}, index

    def test_all_181_dex_is_not_species_id(self):
        rows = join_roster(*self.fixture())
        self.assertEqual(len(rows), 181)
        self.assertEqual(rows[0]['species_id'], 1)
        self.assertEqual(rows[0]['dex_no'], 201)

    def test_id_collision_rejected(self):
        raw, pending, index = self.fixture(); pending['records'][0]['species_id'] = 2
        with self.assertRaises(SourceError):
            join_roster(raw, pending, index)

    def test_missing_name_not_guessed(self):
        raw, pending, index = self.fixture(); index[0]['name_ja'] = '未確定'
        with self.assertRaises(SourceError):
            join_roster(raw, pending, index)

    def test_preservation_rows_not_used(self):
        raw, pending, index = self.fixture(); pending['imported_from_preservation_rows'] = 1
        with self.assertRaises(SourceError):
            join_roster(raw, pending, index)


if __name__ == '__main__':
    unittest.main()
