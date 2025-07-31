import unittest
import json
import os
from pathlib import Path
from cadastrePdfExtractor import CadastralPdfExtractor

TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), "test-data.json")
TEST_INPUT_DIR = os.path.join(os.path.dirname(__file__), "tests_examples")


class TestCadastrePdfExtractor(unittest.TestCase):
    expected_data = {}
    process_output = {}

    @classmethod
    def setUpClass(cls):
        """Load test data and perform extraction setup."""
        extractor = CadastralPdfExtractor()
        test_data_json = json.load(open(TEST_DATA_FILE))
        test_data_list = test_data_json["tests_cases"]
        for test_case in test_data_list:
            filename = test_case["file_path"]
            expected_output = test_case["expected_results"]
            cls.expected_data[filename] = expected_output
            file_full_path = Path(os.path.join(TEST_INPUT_DIR, filename))
            output = extractor.extract_cadatral_info_from_pdf(file_full_path)
            cls.process_output[filename] = output

    def tests_result_length(self, filename):
        """Check if the output length matches the expected length."""
        expected_length = len(self.expected_data[filename])
        output_length = len(self.process_output[filename])
        self.assertEqual(expected_length, output_length, f"Length mismatch for {filename}")

    def test_result_format(self, filename):
        """Check if the output format matches the expected format."""
        for key in self.expected_data[filename]:
            with self.subTest(key=key, filename=filename):
                self.assertIn(key, self.process_output[filename], f"Key {key} not found in output for {filename}")
    def test_correct_departement(self, filename):
        """Check if the department code is correct."""
        expected_departement = self.expected_data[filename][0].get("departement")
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                output_departement = self.process_output[filename][line].get("departement")
                self.assertIsNotNone(output_departement, f"Departement not found in output data for {filename}")
                self.assertEqual(expected_departement, output_departement, f"Departement mismatch for {filename}")
    def test_correct_commune(self, filename):
        """Check if the commune code is correct."""
        expected_commune = self.expected_data[filename][0].get("commune")
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                output_commune = self.process_output[filename][line].get("commune")
                self.assertIsNotNone(output_commune, f"Commune not found in output data for {filename}")
                self.assertEqual(expected_commune, output_commune, f"Commune mismatch for {filename}")
    def test_correct_prefix(self, filename):
        """Check if the prefix is correct."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_prefix = self.expected_data[filename][line].get("prefix")
                output_prefix = self.process_output[filename][line].get("prefix")
                self.assertEqual(expected_prefix, output_prefix, f"Prefix mismatch for {filename}")
    def test_correct_section(self, filename):
        """Check if the section is correct."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_section = self.expected_data[filename][line].get("section")
                output_section = self.process_output[filename][line].get("section")
                self.assertIsNotNone(output_section, f"Section not found in output data for {filename}")
                self.assertEqual(expected_section, output_section, f"Section mismatch for {filename}")
    def test_correct_number(self, filename):
        """Check if the plan number is correct."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_number = self.expected_data[filename][line].get("plan_number")
                output_number = self.process_output[filename][line].get("number")
                self.assertIsNotNone(output_number, f"Plan number not found in output data for {filename}")
                self.assertEqual(expected_number, output_number, f"Plan number mismatch for {filename}")
    def test_correct_contenance_ha(self, filename):
        """Check if the contenance in hectares is correct."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_contenance = self.expected_data[filename][line].get("contenance_ha")
                output_contenance = self.process_output[filename][line].get("contenance_ha")
                self.assertEqual(expected_contenance, output_contenance, f"Contenance ha mismatch for {filename}")
    def test_correct_contenance_a(self, filename):
        """Check if the contenance in ares is correct."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_contenance = self.expected_data[filename][line].get("contenance_a")
                output_contenance = self.process_output[filename][line].get("contenance_a")
                self.assertEqual(expected_contenance, output_contenance, f"Contenance a mismatch for {filename}")
    def test_correct_contenance_ca(self, filename):
        """Check if the contenance in centiares is correct."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_contenance = self.expected_data[filename][line].get("contenance_ca")
                output_contenance = self.process_output[filename][line].get("contenance_ca")
                self.assertEqual(expected_contenance, output_contenance, f"Contenance ca mismatch for {filename}")
    def test_owner_rights(self, filename):
        """Check if the owner rights are correctly identified."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_rights = self.expected_data[filename][line].get("droit_reel")
                output_rights = self.process_output[filename][line].get("droit_reel")
                self.assertIsNotNone(output_rights, f"Droit réel not found in output data for {filename}")
                self.assertEqual(expected_rights, output_rights, f"Droit réel rights mismatch for {filename}")
    def test_designation_parcelle(self, filename):
        """Check if the designation of the parcel is correct."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_designation = self.expected_data[filename][line].get("designation_parcelle")
                output_designation = self.process_output[filename][line].get("designation_parcelle")
                self.assertIsNotNone(output_designation, f"Designation not found in output data for {filename}")
                self.assertEqual(expected_designation, output_designation, f"Designation mismatch for {filename}")
    def test_correct_nom(self, filename):
        """Check if the name is correctly extracted."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_name = self.expected_data[filename][line].get("nom")
                output_name = self.process_output[filename][line].get("nom")
                self.assertIsNotNone(output_name, f"Nom not found in output data for {filename}")
                self.assertEqual(expected_name, output_name, f"Nom mismatch for {filename}")
    def test_correct_prenom(self, filename):
        """Check if the first name is correctly extracted."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_first_name = self.expected_data[filename][line].get("prenom")
                output_first_name = self.process_output[filename][line].get("prenom")
                self.assertEqual(expected_first_name, output_first_name, f"Prénom mismatch for {filename}")
    def test_correct_numero_majic(self, filename):
        """Check if the numéro majic is correctly extracted."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_numero_majic = self.expected_data[filename][line].get("numero_majic")
                output_numero_majic = self.process_output[filename][line].get("numero_majic")
                self.assertIsNotNone(output_numero_majic, f"Numéro majic not found in output data for {filename}")
                self.assertEqual(expected_numero_majic, output_numero_majic, f"Numéro majic mismatch for {filename}")
    def test_correct_voie(self, filename):
        """Check if the street name is correctly extracted."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_voie = self.expected_data[filename][line].get("voie")
                output_voie = self.process_output[filename][line].get("voie")
                self.assertEqual(expected_voie, output_voie, f"Voie mismatch for {filename}")
    def test_correct_code_postal(self, filename):
        """Check if the postal code is correctly extracted."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_code_postal = self.expected_data[filename][line].get("code_postal")
                output_code_postal = self.process_output[filename][line].get("code_postal")
                self.assertIsNotNone(output_code_postal, f"Code postal not found in output data for {filename}")
                self.assertEqual(expected_code_postal, output_code_postal, f"Code postal mismatch for {filename}")
    def test_correct_ville(self, filename):
        """Check if the city name is correctly extracted."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_ville = self.expected_data[filename][line].get("ville")
                output_ville = self.process_output[filename][line].get("ville")
                self.assertIsNotNone(output_ville, f"Ville not found in output data for {filename}")
                self.assertEqual(expected_ville, output_ville, f"Ville mismatch for {filename}")
    def test_correct_id(self, filename):
        """Check if the ID is correctly extracted."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_id = self.expected_data[filename][line].get("id")
                output_id = self.process_output[filename][line].get("id")
                self.assertIsNotNone(output_id, f"ID not found in output data for {filename}")
                self.assertEqual(expected_id, output_id, f"ID mismatch for {filename}")
    def test_fichier_source(self, filename):
        """Check if the source file is correctly identified."""
        for line in range(len(self.expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_source = self.expected_data[filename][line].get("fichier_source")
                output_source = self.process_output[filename][line].get("fichier_source")
                self.assertIsNotNone(output_source, f"Fichier source not found in output data for {filename}")
                self.assertEqual(expected_source, output_source, f"Fichier source mismatch for {filename}")

# Génération dynamique des tests
def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for filename in os.listdir(TEST_INPUT_DIR):
        if filename.endswith(".pdf"):
            for function_name in dir(TestCadastrePdfExtractor):
                if function_name.startswith("test_"):
                    # Create a test method for each PDF file
                    test_method = getattr(TestCadastrePdfExtractor, function_name)
                    test_func = lambda self, fn=filename: test_method(self, fn)
                    test_name = f"{function_name}_{filename.replace('.', '_')}"
                    setattr(TestCadastrePdfExtractor, test_name, test_func)
                    suite.addTest(TestCadastrePdfExtractor(test_name))
    return suite

if __name__ == "__main__":
    unittest.main()