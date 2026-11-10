import pathlib
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestTryoutAutosaveContract(unittest.TestCase):
    def test_player_sends_debounced_autosave_for_answer_changes(self):
        template = (PROJECT_ROOT / "templates" / "tryout_player.html").read_text()
        self.assertIn("data-autosave", template)
        self.assertIn("autosave", template)
        self.assertIn("answerChange", template)

    def test_answer_endpoint_preserves_current_question_for_autosave(self):
        controller = (PROJECT_ROOT / "controllers" / "http_controller.py").read_text()
        self.assertIn("form.get('autosave') == '1'", controller)
        self.assertIn("self.send_json({'saved': bool(qid in valid_ids", controller)


if __name__ == "__main__":
    unittest.main()
