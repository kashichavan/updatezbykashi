from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from requirements import ai_engine
from requirements.job_text import description_blocks


class DescriptionBlockTests(SimpleTestCase):
    def test_flat_description_gets_headings_and_list_items(self):
        text = (
            'Job Description Acme is hiring a developer to join a small team building payment tools for shops '
            'across the country and looking after the systems that keep them running every single day of the week. '
            'Responsibilities: Own a major component of the product Design new applications Improve performance'
        )
        blocks = description_blocks(text)
        self.assertEqual(blocks[0], {'kind': 'heading', 'text': 'Job Description'})
        self.assertEqual(blocks[-1]['kind'], 'list')
        self.assertEqual(blocks[-1]['lines'][1], 'Design new applications')

    def test_existing_line_breaks_and_bullets_are_kept(self):
        blocks = description_blocks('Skills:\n• Python\n• SQL\nWe reply within a week.')
        self.assertEqual(blocks[1], {'kind': 'list', 'lines': ['Python', 'SQL']})
        self.assertEqual(blocks[2]['text'], 'We reply within a week.')

    def test_literal_backslash_n_and_empty_text(self):
        self.assertEqual(len(description_blocks('First line.\\nSecond line.')), 2)
        self.assertEqual(description_blocks(''), [])

    def test_company_abbreviation_does_not_split_a_sentence(self):
        sentence = 'Join Acme Pvt. Ltd. as an intern.'
        self.assertEqual(description_blocks(sentence), [{'kind': 'text', 'text': sentence}])


def _reply(status, content=''):
    response = MagicMock(status_code=status, headers={}, text='error')
    response.json.return_value = {'choices': [{'message': {'content': content}}]}
    return response


class ProviderFallbackTests(SimpleTestCase):
    @patch.dict('os.environ', {'GROQ_API_KEY': 'g', 'NVIDIA_API_KEY': 'n'})
    @patch('requirements.ai_engine.requests.post')
    def test_rejected_groq_key_moves_to_nvidia(self, post):
        post.side_effect = [_reply(401), _reply(200, '<think>x</think>{"ok": true}')]
        self.assertEqual(ai_engine.call_groq_chat([{'role': 'user', 'content': 'hi'}]), '{"ok": true}')
        self.assertEqual(post.call_args.args[0], ai_engine.NVIDIA_ENDPOINT)

    @patch.dict('os.environ', {'GROQ_API_KEY': 'g', 'NVIDIA_API_KEY': ''})
    @override_settings(NVIDIA_API_KEY='')
    @patch('requirements.ai_engine.requests.post')
    def test_without_nvidia_the_groq_error_is_raised(self, post):
        post.return_value = _reply(401)
        with self.assertRaises(RuntimeError):
            ai_engine.call_groq_chat([{'role': 'user', 'content': 'hi'}])
