import json
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

REVIEW_ANSWER = json.dumps({
    'checks': [
        {'name': 'Clarity and impact', 'score': 21, 'detail': 'Clear.'},
        {'name': 'Keywords for the role', 'score': 99, 'detail': 'Over the limit.'},
        {'name': 'Proof in projects and experience', 'score': 15, 'detail': 'Some proof.'},
        {'name': 'Structure and completeness', 'score': 12, 'detail': 'Fine.'},
    ],
    'fixes': ['Add a real result.'],
    'missing_skills': ['Docker', 'Python'],
    'projects': [{'index': 0, 'action_verbs': 20, 'google_xyz': 15, 'quantified_metrics': 5,
                  'tech_relevance': 10, 'architecture_scale': 5}],
})

BULLET = 'made a library app where students borrow books'


def make_body(**extra):
    body = {
        'role': 'python-backend',
        'resume': {
            'name': 'Asha Rao',
            'contact': {'email': 'asha@example.com', 'phone': '9999999999'},
            'summary': 'Student who builds websites with Python.',
            'skills': {'Languages': ['Python']},
            'projects': [{'title': 'Library App', 'tech_stack': 'Python, Django', 'bullets': [BULLET]}],
        },
    }
    body.update(extra)
    return json.dumps(body)


class ResumeAiReviewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse('api_ai_resume_review')

    def post(self, body):
        return self.client.post(self.url, body, content_type='application/json')

    def test_score_is_ai_and_equals_its_parts(self):
        with patch('requirements.ai_engine.call_groq_chat', return_value=REVIEW_ANSWER):
            data = self.post(make_body()).json()
        self.assertTrue(data['ai'])
        self.assertEqual(data['score'], 21 + 25 + 15 + 12)
        self.assertEqual(data['project_scores']['0']['score'], 55)
        self.assertEqual(data['missing_skills'], ['Docker'])

    def test_identity_never_reaches_the_ai(self):
        with patch('requirements.ai_engine.call_groq_chat', return_value=REVIEW_ANSWER) as call:
            self.post(make_body())
        sent = json.dumps(call.call_args.args[0])
        self.assertNotIn('Asha', sent)
        self.assertNotIn('asha@example.com', sent)
        self.assertNotIn('9999999999', sent)

    def test_same_text_is_scored_once(self):
        with patch('requirements.ai_engine.call_groq_chat', return_value=REVIEW_ANSWER) as call:
            first = self.post(make_body()).json()
            second = self.post(make_body()).json()
        self.assertEqual(first['score'], second['score'])
        self.assertEqual(call.call_count, 1)

    def test_rewrite_is_returned_and_scored(self):
        improved = 'Built a library app in Django so students can borrow books online.'
        answers = [json.dumps({'rewrites': [{'id': 'project-0-0', 'text': improved}]}), REVIEW_ANSWER]
        with patch('requirements.ai_engine.call_groq_chat', side_effect=answers) as call:
            data = self.post(make_body(enhance=[{'kind': 'project', 'index': 0, 'bullet': 0}])).json()
        self.assertEqual(data['rewrites'], [{'original': BULLET, 'improved': improved}])
        self.assertIn(improved, json.dumps(call.call_args_list[1].args[0]))

    def test_dishonest_rewrites_are_dropped(self):
        for bad in (
            'Built a library app serving 5000 students across campus every single day.',
            'Built a library app on Kubernetes so students can borrow books online.',
            'Built a robust library app so students can borrow books online.',
        ):
            cache.clear()
            answers = [json.dumps({'rewrites': [{'id': 'project-0-0', 'text': bad}]}), REVIEW_ANSWER]
            with patch('requirements.ai_engine.call_groq_chat', side_effect=answers):
                data = self.post(make_body(enhance=[{'kind': 'project', 'index': 0, 'bullet': 0}])).json()
            self.assertEqual(data['rewrites'], [], bad)

    def test_ai_failure_is_reported_as_basic_score(self):
        with patch('requirements.ai_engine.call_groq_chat', side_effect=RuntimeError('down')):
            data = self.post(make_body(enhance=[{'kind': 'summary'}])).json()
        self.assertFalse(data['ai'])
        self.assertEqual(data['rewrites'], [])
        self.assertIn('Basic', data['pass_rate'])

    def test_bad_input_and_size_are_refused(self):
        self.assertEqual(self.post('not json').status_code, 400)
        self.assertEqual(self.post(json.dumps({'resume': 'text'})).status_code, 400)
        self.assertEqual(self.post('x' * (97 * 1024)).status_code, 413)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_out_of_range_enhance_requests_are_ignored(self):
        with patch('requirements.ai_engine.call_groq_chat', return_value=REVIEW_ANSWER) as call:
            data = self.post(make_body(enhance=[{'kind': 'project', 'index': 9, 'bullet': 0}, {'kind': 'x'}])).json()
        self.assertEqual(data['rewrites'], [])
        self.assertEqual(call.call_count, 1)

    def test_rate_limit_stops_ai_calls(self):
        with patch('requirements.ai_engine.call_groq_chat', return_value=REVIEW_ANSWER) as call:
            for number in range(16):
                body = json.loads(make_body())
                body['resume']['summary'] = f'Student number {number} who builds websites with Python.'
                data = self.post(json.dumps(body)).json()
        self.assertEqual(call.call_count, 15)
        self.assertTrue(data['busy'])
        self.assertFalse(data['ai'])


class GroqModelRotationTests(TestCase):
    def setUp(self):
        from requirements import ai_engine
        ai_engine._groq_model_rest_until.clear()
        self.addCleanup(ai_engine._groq_model_rest_until.clear)

    def reply(self, status, text='ok'):
        response = Mock(status_code=status, headers={'retry-after': '30'}, text=text)
        response.json.return_value = {'choices': [{'message': {'content': text}}]}
        return response

    def test_busy_model_hands_over_and_then_rests(self):
        from requirements import ai_engine
        replies = [self.reply(429), self.reply(429), self.reply(200, 'done'), self.reply(200, 'next')]
        used = []

        def post(url, json, headers, timeout):
            used.append(json['model'])
            return replies.pop(0)

        with patch.dict('os.environ', {'GROQ_API_KEY': 'test', 'GROQ_MODEL': 'qwen/qwen3.8-27b'}), \
                patch('requirements.ai_engine.requests.post', side_effect=post):
            self.assertEqual(ai_engine.call_groq_chat([{'role': 'user', 'content': 'x'}]), 'done')
            ai_engine.call_groq_chat([{'role': 'user', 'content': 'x'}])
        self.assertEqual(used, ['qwen/qwen3.8-27b', 'openai/gpt-oss-20b', 'openai/gpt-oss-120b', 'openai/gpt-oss-120b'])
