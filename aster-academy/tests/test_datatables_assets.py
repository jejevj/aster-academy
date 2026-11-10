import unittest
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = PROJECT_ROOT / "templates"

class TestDataTablesAssets(unittest.TestCase):
    def test_vendor_assets_include_jquery_and_datatables(self):
        vendor = PROJECT_ROOT / "static" / "vendor" / "datatables"
        self.assertTrue((vendor / "jquery-3.7.1.min.js").is_file())
        self.assertTrue((vendor / "dataTables.min.js").is_file())
        self.assertTrue((vendor / "dataTables.dataTables.min.css").is_file())

    def test_datatables_templates_load_jquery_before_datatables(self):
        for name in [
            "admin_question_bank.html",
            "admin_question_list.html",
            "admin_question_categories.html",
        ]:
            content = (TEMPLATES / name).read_text()
            jquery_pos = content.index('/assets/vendor/datatables/jquery-3.7.1.min.js')
            datatables_pos = content.index("const DATA_TABLE_JS='/assets/vendor/datatables/dataTables.min.js'")
            self.assertLess(jquery_pos, datatables_pos, f"{name} harus memuat jQuery lebih dahulu.")

if __name__ == "__main__":
    unittest.main()
