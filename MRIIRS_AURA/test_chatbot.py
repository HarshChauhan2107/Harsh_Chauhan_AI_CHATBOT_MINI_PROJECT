import unittest
import app as chatbot

class AuraTests(unittest.TestCase):
    def setUp(self):
        self.client = chatbot.app.test_client()

    def ask(self, question):
        response = self.client.post('/api/chat', json={'message': question})
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_homepage_brand(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MRIIRS AURA', response.data)
        self.assertIn(b'Artificial University Response Assistant', response.data)

    def test_health_reports_full_form_and_faq_count(self):
        data = self.client.get('/api/health').get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['brand'], 'MRIIRS AURA')
        self.assertEqual(data['full_form'], 'Artificial University Response Assistant')
        self.assertGreaterEqual(data['faq_count'], 50)

    def test_mca_bcom_eligibility_specific(self):
        data = self.ask('I completed B.Com. Can I apply for the two-year MCA?')
        self.assertIn('Mathematics', data['answer'])
        self.assertIn('50%', data['answer'])
        self.assertEqual(data['category'], 'Programmes')

    def test_mca_fee_is_not_general_fee_answer(self):
        data = self.ask('What is the MCA fee?')
        self.assertIn('2,18,100', data['answer'])
        self.assertIn('MCA', data['matched_question'])

    def test_admission_process_has_actual_steps(self):
        data = self.ask('How can I apply for admission?')
        self.assertIn('online', data['answer'].lower())
        self.assertIn('application/reference number', data['answer'].lower())

    def test_hostel_answer_has_specific_details(self):
        data = self.ask('Does MRIIRS have hostel accommodation?')
        self.assertIn('single, double and triple', data['answer'])

    def test_unrelated_query_uses_safe_fallback(self):
        data = self.ask('What is the current cricket score in Delhi?')
        self.assertIsNone(data['matched_question'])
        self.assertIn("don't have a verified answer", data['answer'])
        self.assertEqual(data['match'], 'none')

    def test_fee_question_with_programme_anchor(self):
        data = self.ask('Tell me the fee structure for MCA with installments')
        self.assertIn('2,18,100', data['answer'])
        self.assertEqual(data['category'], 'Programmes')

    def test_categories(self):
        categories = self.client.get('/api/categories').get_json()
        self.assertIn('Admissions', categories)
        self.assertIn('Programmes', categories)
        self.assertIn('Contact & Help', categories)

    def test_empty_question(self):
        self.assertEqual(self.client.post('/api/chat', json={'message': '  '}).status_code, 400)

    def test_long_question(self):
        self.assertEqual(self.client.post('/api/chat', json={'message': 'x' * 501}).status_code, 400)


    def test_mca_without_maths_gets_direct_eligibility_answer(self):
        data = self.ask('Can I apply for MCA without Mathematics?')
        self.assertIn('Mathematics', data['answer'])
        self.assertIn('10+2', data['answer'])
        self.assertEqual(data['category'], 'Programmes')

    def test_combined_mca_duration_and_fee(self):
        data = self.ask('What is the duration and fee of MCA?')
        self.assertIn('2 years', data['answer'])
        self.assertIn('2,18,100', data['answer'])
        self.assertIn('duration and fee', (data['matched_question'] or '').lower())

    def test_rechecking_query_routes_to_revaluation(self):
        data = self.ask('How can I request rechecking of my examination result?')
        self.assertIn('revaluation', (data['matched_question'] or '').lower())

    def test_class_timings_do_not_return_an_unrelated_answer(self):
        data = self.ask('What are the class timings for MCA?')
        self.assertIsNone(data['matched_question'])
        self.assertEqual(data['match'], 'none')

    def test_aura_identity_question(self):
        data = self.ask('What is MRIIRS AURA?')
        self.assertIn('Artificial University Response Assistant', data['answer'])

    def test_feedback(self):
        self.assertEqual(self.client.post('/api/feedback', json={'vote': 'up'}).status_code, 200)
        self.assertEqual(self.client.post('/api/feedback', json={'vote': 'wrong'}).status_code, 400)

if __name__ == '__main__':
    unittest.main(verbosity=2)
