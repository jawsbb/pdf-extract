import unittest
import json
import os
from pathlib import Path
from cadastrePdfExtractor import CadastralPdfExtractor

TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), "test-data.json")
TEST_INPUT_DIR = os.path.join(os.path.dirname(__file__), "tests_examples")

expected_data = {}
process_output = {}

extractor = CadastralPdfExtractor()
test_data_json = json.load(open(TEST_DATA_FILE))
test_data_list = test_data_json["tests_cases"]
for test_case in test_data_list:
    filename = test_case["file_path"]
    expected_output = test_case["expected_results"]
    expected_data[filename] = expected_output
    file_full_path = Path(os.path.join(TEST_INPUT_DIR, filename))
    output = extractor.extract_cadatral_info_from_pdf(file_full_path)
    process_output[filename] = output


class TestCadastrePdfExtractor(unittest.TestCase):

    def run_test_result_length(self, filename):
        """Check if the output length matches the expected length."""
        expected_length = len(expected_data[filename])
        output_length = len(process_output[filename])
        self.assertEqual(
            expected_length, output_length, f"Length mismatch for {filename}"
        )

    def run_test_result_format(self, filename):
        """Check if the output format matches the expected format."""
        for key in expected_data[filename]:
            with self.subTest(key=key, filename=filename):
                self.assertIn(
                    key,
                    process_output[filename],
                    f"Key {key} not found in output for {filename}",
                )

    def run_test_correct_departement(self, filename):
        """Check if the department code is correct."""
        expected_departement = expected_data[filename][0].get("departement")
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                output_departement = process_output[filename][line].get("departement")
                self.assertIsNotNone(
                    output_departement,
                    f"Departement not found in output data for {filename}",
                )
                self.assertEqual(
                    expected_departement,
                    output_departement,
                    f"Departement mismatch for {filename}",
                )

    def run_test_correct_commune(self, filename):
        """Check if the commune code is correct."""
        expected_commune = expected_data[filename][0].get("commune")
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                output_commune = process_output[filename][line].get("commune")
                self.assertIsNotNone(
                    output_commune, f"Commune not found in output data for {filename}"
                )
                self.assertEqual(
                    expected_commune, output_commune, f"Commune mismatch for {filename}"
                )

    def run_test_correct_prefix(self, filename):
        """Check if the prefix is correct."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_prefix = expected_data[filename][line].get("prefix")
                output_prefix = process_output[filename][line].get("prefix")
                self.assertEqual(
                    expected_prefix, output_prefix, f"Prefix mismatch for {filename}"
                )

    def run_test_correct_section(self, filename):
        """Check if the section is correct."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_section = expected_data[filename][line].get("section")
                output_section = process_output[filename][line].get("section")
                self.assertIsNotNone(
                    output_section, f"Section not found in output data for {filename}"
                )
                self.assertEqual(
                    expected_section, output_section, f"Section mismatch for {filename}"
                )

    def run_test_correct_number(self, filename):
        """Check if the plan number is correct."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_number = expected_data[filename][line].get("plan_number")
                output_number = process_output[filename][line].get("plan_number")
                self.assertIsNotNone(
                    output_number,
                    f"Plan number not found in output data for {filename}",
                )
                self.assertEqual(
                    expected_number,
                    output_number,
                    f"Plan number mismatch for {filename}",
                )

    def run_test_correct_contenance_ha(self, filename):
        """Check if the contenance in hectares is correct."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_contenance = expected_data[filename][line].get("contenance_ha")
                output_contenance = process_output[filename][line].get("contenance_ha")
                self.assertEqual(
                    expected_contenance,
                    output_contenance,
                    f"Contenance ha mismatch for {filename}",
                )

    def run_test_correct_contenance_a(self, filename):
        """Check if the contenance in ares is correct."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_contenance = expected_data[filename][line].get("contenance_a")
                output_contenance = process_output[filename][line].get("contenance_a")
                self.assertEqual(
                    expected_contenance,
                    output_contenance,
                    f"Contenance a mismatch for {filename}",
                )

    def run_test_correct_contenance_ca(self, filename):
        """Check if the contenance in centiares is correct."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_contenance = expected_data[filename][line].get("contenance_ca")
                output_contenance = process_output[filename][line].get("contenance_ca")
                self.assertEqual(
                    expected_contenance,
                    output_contenance,
                    f"Contenance ca mismatch for {filename}",
                )

    def run_test_owner_rights(self, filename):
        """Check if the owner rights are correctly identified."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_rights = expected_data[filename][line].get("droit_reel")
                output_rights = process_output[filename][line].get("droit_reel")
                self.assertIsNotNone(
                    output_rights, f"Droit réel not found in output data for {filename}"
                )
                self.assertEqual(
                    expected_rights,
                    output_rights,
                    f"Droit réel rights mismatch for {filename}",
                )

    def run_test_designation_parcelle(self, filename):
        """Check if the designation of the parcel is correct."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_designation = expected_data[filename][line].get(
                    "designation_parcelle"
                )
                output_designation = process_output[filename][line].get(
                    "designation_parcelle"
                )
                self.assertIsNotNone(
                    output_designation,
                    f"Designation not found in output data for {filename}",
                )
                self.assertEqual(
                    expected_designation,
                    output_designation,
                    f"Designation mismatch for {filename}",
                )

    def run_test_correct_nom(self, filename):
        """Check if the name is correctly extracted."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_name = expected_data[filename][line].get("nom")
                output_name = process_output[filename][line].get("nom")
                self.assertIsNotNone(
                    output_name, f"Nom not found in output data for {filename}"
                )
                self.assertEqual(
                    expected_name, output_name, f"Nom mismatch for {filename}"
                )

    def run_test_correct_prenom(self, filename):
        """Check if the first name is correctly extracted."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_first_name = expected_data[filename][line].get("prenom")
                output_first_name = process_output[filename][line].get("prenom")
                self.assertEqual(
                    expected_first_name,
                    output_first_name,
                    f"Prénom mismatch for {filename}",
                )

    def run_test_correct_numero_majic(self, filename):
        """Check if the numéro majic is correctly extracted."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_numero_majic = expected_data[filename][line].get(
                    "numero_majic"
                )
                output_numero_majic = process_output[filename][line].get("numero_majic")
                self.assertIsNotNone(
                    output_numero_majic,
                    f"Numéro majic not found in output data for {filename}",
                )
                self.assertEqual(
                    expected_numero_majic,
                    output_numero_majic,
                    f"Numéro majic mismatch for {filename}",
                )

    def run_test_correct_voie(self, filename):
        """Check if the street name is correctly extracted."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_voie = expected_data[filename][line].get("voie")
                output_voie = process_output[filename][line].get("voie")
                self.assertEqual(
                    expected_voie, output_voie, f"Voie mismatch for {filename}"
                )

    def run_test_correct_code_postal(self, filename):
        """Check if the postal code is correctly extracted."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_code_postal = expected_data[filename][line].get("code_postal")
                output_code_postal = process_output[filename][line].get("code_postal")
                self.assertIsNotNone(
                    output_code_postal,
                    f"Code postal not found in output data for {filename}",
                )
                self.assertEqual(
                    expected_code_postal,
                    output_code_postal,
                    f"Code postal mismatch for {filename}",
                )

    def run_test_correct_ville(self, filename):
        """Check if the city name is correctly extracted."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_ville = expected_data[filename][line].get("ville")
                output_ville = process_output[filename][line].get("ville")
                self.assertIsNotNone(
                    output_ville, f"Ville not found in output data for {filename}"
                )
                self.assertEqual(
                    expected_ville, output_ville, f"Ville mismatch for {filename}"
                )

    def run_test_correct_id(self, filename):
        """Check if the ID is correctly extracted."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_id = expected_data[filename][line].get("id")
                output_id = process_output[filename][line].get("id")
                self.assertIsNotNone(
                    output_id, f"ID not found in output data for {filename}"
                )
                self.assertEqual(expected_id, output_id, f"ID mismatch for {filename}")

    def run_test_fichier_source(self, filename):
        """Check if the source file is correctly identified."""
        for line in range(len(expected_data[filename])):
            with self.subTest(line=line, filename=filename):
                expected_source = expected_data[filename][line].get("fichier_source")
                output_source = process_output[filename][line].get("fichier_source")
                self.assertIsNotNone(
                    output_source,
                    f"Fichier source not found in output data for {filename}",
                )
                self.assertEqual(
                    expected_source,
                    output_source,
                    f"Fichier source mismatch for {filename}",
                )


def _create_test_method_result_length(filename):
    def test_method(self):
        self.run_test_result_length(filename)

    return test_method


def _create_test_method_result_format(filename):
    def test_method(self):
        self.run_test_result_format(filename)

    return test_method


def _create_test_method_correct_departement(filename):
    def test_method(self):
        self.run_test_correct_departement(filename)

    return test_method


def _create_test_method_correct_commune(filename):
    def test_method(self):
        self.run_test_correct_commune(filename)

    return test_method


def _create_test_method_correct_prefix(filename):
    def test_method(self):
        self.run_test_correct_prefix(filename)

    return test_method


def _create_test_method_correct_section(filename):
    def test_method(self):
        self.run_test_correct_section(filename)

    return test_method


def _create_test_method_correct_number(filename):
    def test_method(self):
        self.run_test_correct_number(filename)

    return test_method


def _create_test_method_correct_contenance_ha(filename):
    def test_method(self):
        self.run_test_correct_contenance_ha(filename)

    return test_method


def _create_test_method_correct_contenance_a(filename):
    def test_method(self):
        self.run_test_correct_contenance_a(filename)

    return test_method


def _create_test_method_correct_contenance_ca(filename):
    def test_method(self):
        self.run_test_correct_contenance_ca(filename)

    return test_method


def _create_test_method_owner_rights(filename):
    def test_method(self):
        self.run_test_owner_rights(filename)

    return test_method


def _create_test_method_designation_parcelle(filename):
    def test_method(self):
        self.run_test_designation_parcelle(filename)

    return test_method


def _create_test_method_correct_nom(filename):
    def test_method(self):
        self.run_test_correct_nom(filename)

    return test_method


def _create_test_method_correct_prenom(filename):
    def test_method(self):
        self.run_test_correct_prenom(filename)

    return test_method


def _create_test_method_correct_numero_majic(filename):
    def test_method(self):
        self.run_test_correct_numero_majic(filename)

    return test_method


def _create_test_method_correct_voie(filename):
    def test_method(self):
        self.run_test_correct_voie(filename)

    return test_method


def _create_test_method_correct_code_postal(filename):
    def test_method(self):
        self.run_test_correct_code_postal(filename)

    return test_method


def _create_test_method_correct_ville(filename):
    def test_method(self):
        self.run_test_correct_ville(filename)

    return test_method


def _create_test_method_correct_id(filename):
    def test_method(self):
        self.run_test_correct_id(filename)

    return test_method


def _create_test_method_fichier_source(filename):
    def test_method(self):
        self.run_test_fichier_source(filename)

    return test_method


for filename in os.listdir(TEST_INPUT_DIR):
    if filename.endswith(".pdf"):
        method_name = (
            f'test_result_length_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_result_length(filename),
        )
        method_name = (
            f'test_result_format_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_result_format(filename),
        )
        method_name = (
            f'test_correct_departement_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_departement(filename),
        )
        method_name = (
            f'test_correct_commune_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_commune(filename),
        )
        method_name = (
            f'test_correct_prefix_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_prefix(filename),
        )
        method_name = (
            f'test_correct_section_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_section(filename),
        )
        method_name = (
            f'test_correct_number_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_number(filename),
        )
        method_name = (
            f'test_correct_contenance_ha_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_contenance_ha(filename),
        )
        method_name = (
            f'test_correct_contenance_a_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_contenance_a(filename),
        )
        method_name = (
            f'test_correct_contenance_ca_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_contenance_ca(filename),
        )
        method_name = (
            f'test_owner_rights_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_owner_rights(filename),
        )
        method_name = (
            f'test_designation_parcelle_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_designation_parcelle(filename),
        )
        method_name = f'test_correct_nom_{filename.replace(".", "_").replace(" ", "_")}'
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_nom(filename),
        )
        method_name = (
            f'test_correct_prenom_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_prenom(filename),
        )
        method_name = (
            f'test_correct_numero_majic_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_numero_majic(filename),
        )
        method_name = (
            f'test_correct_voie_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_voie(filename),
        )
        method_name = (
            f'test_correct_code_postal_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_code_postal(filename),
        )
        method_name = (
            f'test_correct_ville_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_ville(filename),
        )
        method_name = f'test_correct_id_{filename.replace(".", "_").replace(" ", "_")}'
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_correct_id(filename),
        )
        method_name = (
            f'test_fichier_source_{filename.replace(".", "_").replace(" ", "_")}'
        )
        setattr(
            TestCadastrePdfExtractor,
            method_name,
            _create_test_method_fichier_source(filename),
        )

if __name__ == "__main__":
    unittest.main()
