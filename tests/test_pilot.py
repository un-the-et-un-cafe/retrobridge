import json
import unittest
from unittest.mock import patch
import retrobridge as r


class PilotTests(unittest.TestCase):
    def test_age_boundary(self):
        self.assertTrue(r.eligible({'introduced':'1996-10-29'}))
        self.assertFalse(r.eligible({'introduced':'1996-10-30'}))

    def test_catalog(self):
        self.assertEqual(len(r.catalog()['devices']), 3)
        self.assertTrue(all(r.eligible(p) for p in r.catalog()['devices']))

    def test_rss(self):
        self.assertEqual(len(r.rss_items((r.ROOT/'fixtures/news.xml').read_bytes())), 2)

    def test_forbidden_xml(self):
        for data in [b'<!DOCTYPE rss [<!ENTITY x "bad">]><rss/>',
                     '<!DOCTYPE rss><rss/>'.encode('utf-16'), b'x'*65537]:
            with self.assertRaises((ValueError, UnicodeError)):
                r.rss_items(data)

    def test_wrong_feed(self):
        with self.assertRaises(ValueError): r.rss_items(b'<html/>')

    def test_transcript_is_inert(self):
        output = r.transcript(['hello\r\nPRIVMSG #x :bad\x01', '/exec rm -rf /'])
        self.assertEqual(len(output.splitlines()), 2)
        self.assertNotIn('\x01', output)
        self.assertTrue(all(s.startswith('[retro-news] ') for s in output.splitlines()))

    def test_escaping(self):
        data = {'devices':[{'name':'<script>x</script>', 'introduced':'1985-01-01', 'capabilities':['&']}], 'adapters':[]}
        with patch.object(r, 'catalog', return_value=data):
            self.assertNotIn('<script>', r.render())
            self.assertIn('&lt;script&gt;', r.render())

    def test_themes_no_forms_scripts(self):
        for theme in r.THEMES:
            result = r.render(theme).lower()
            for forbidden in ['<script', '<form', '<iframe', 'javascript:', '<link', '<style']:
                self.assertNotIn(forbidden, result)

    def test_explicit_consent(self):
        valid = {'email':'sample@example.invalid', 'newsletter_opt_in':True, 'consent_text_version':'pilot-v1'}
        self.assertTrue(r.validate_signup(valid))
        for changed in [{**valid, 'newsletter_opt_in':False}, {**valid, 'newsletter_opt_in':1},
                        {**valid, 'religion':'anything'}, {**valid, 'device':[]}, {**valid, 'interests':'text'}]:
            with self.assertRaises(ValueError): r.validate_signup(changed)

    def test_optional_fields(self):
        self.assertTrue(r.validate_signup({'email':'sample@example.invalid', 'newsletter_opt_in':True,
            'consent_text_version':'pilot-v1', 'device':'synthetic', 'interests':['plain text']}))

    def test_roles(self):
        with self.assertRaises(PermissionError): r.suggest('guest', 'test')
        suggestion = r.suggest('contributor', '/execute something')
        self.assertEqual(suggestion['status'], 'pending-review')
        with self.assertRaises(PermissionError): r.review('contributor', suggestion, 'accepted')
        self.assertFalse(r.review('reviewer', suggestion, 'accepted')['executable'])

    def test_schemas_parse(self):
        for path in (r.ROOT/'schemas').glob('*.json'):
            self.assertIsInstance(json.loads(path.read_text()), dict)

if __name__ == '__main__': unittest.main()
