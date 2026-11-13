import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_profile import e, summarize, telemetry, language_svg, activity_svg


class ProfileTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 13, tzinfo=timezone.utc)
        self.data = {"user": {"followers": 8}, "repositories": [
            {"name": "source-app", "fork": False, "language": "Python", "pushed_at": "2026-11-12T00:00:00Z", "stargazers_count": 3, "forks_count": 1, "description": "A < & tool"},
            {"name": "old-project", "fork": False, "language": "Python", "pushed_at": "2025-01-01T00:00:00Z", "stargazers_count": 2, "forks_count": 0, "description": "Older"},
            {"name": "forked", "fork": True, "language": "R", "pushed_at": "2026-11-12T00:00:00Z", "stargazers_count": 0, "forks_count": 1, "description": "Fork"},
        ]}

    def test_escape(self):
        self.assertEqual(e('<a b="x">'), '&lt;a b=&quot;x&quot;&gt;')

    def test_summary_counts_distinguish_forks(self):
        s = summarize(self.data, self.now)
        self.assertEqual((s['repos'], s['stars'], s['followers'], s['active_90d']), (3, 5, 8, 1))
        self.assertEqual(s['languages'], Counter({"Python": 2}))
        self.assertEqual([r['name'] for r in s['recent']], ['source-app', 'old-project'])

    def test_svg_markup_escapes_repo_description(self):
        s = summarize(self.data, self.now)
        self.assertIn('A &lt; &amp; tool', activity_svg(s, 'dark'))
        self.assertIn('STARS EARNED', telemetry(s, 'light'))
        self.assertIn('Python', language_svg(s, 'dark'))

    def test_placeholders_do_not_fabricate_numbers(self):
        self.assertIn('Automatic figures appear', telemetry(None, 'dark'))
        self.assertNotIn('37 repositories', telemetry(None, 'dark'))


if __name__ == '__main__':
    unittest.main()
