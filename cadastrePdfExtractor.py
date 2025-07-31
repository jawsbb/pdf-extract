import pdfplumber
import pandas as pd
import os
import re
from pathlib import Path
import json


class CadastralPdfExtractor:
    """
    A class to extract information from cadastral PDF documents.
    It extracts year, department, commune as well as owners and properties informations.
    """

    def __init__(self):
        pass

    def extract_cadatral_info_from_pdf(self, pdf_path: Path) -> list:
        """
        Extracts cadastral information from a PDF file.

        Args:
            pdf_path (Path): The path to the PDF file.

        Returns:
            list: A list of dictionaries containing the extracted information about the properties.
            Each dictionary represents a row in the final DataFrame.
            If the PDF does not contain valid cadastral information, an empty list is returned.
        """
        file_name = os.path.basename(pdf_path.name)
        tables = self.extract_tables_from_pdf(pdf_path)
        if not tables:
            return []

        first_table = tables[0]
        year_departement_commune = self.extract_year_departement_commune(first_table)
        if (
            not year_departement_commune["year"]
            or not year_departement_commune["departement"]
        ):
            return []
        owners = self.extract_owners(first_table)
        properties = self.extract_properties_from_tables(tables[1:])
        self.build_id_for_properties(properties, year_departement_commune)

        return self.convert_result_into_final_display(
            year_departement_commune, owners, properties, file_name
        )

    def extract_tables_from_pdf(self, pdf_path: Path) -> list:
        """
        Extracts tables from a PDF file and returns them as a list of DataFrames.

        Args:
            pdf_path (Path): The path to the PDF file.

        Returns:
            list: A list of DataFrames, each representing a table extracted from the PDF.
        """
        tables: list = []

        if not os.path.exists(pdf_path) or not os.path.isfile(pdf_path):
            print(f"The file {pdf_path} does not exist.")
            return tables

        if not pdf_path.name.lower().endswith(".pdf"):
            print(f"The file {pdf_path} is not a valid PDF file.")
            return tables

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables_on_page = page.extract_tables()
                    for table in tables_on_page:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        tables.append(df)
        except Exception as e:
            print(f"An error occurred while processing the PDF: {e}")

        return tables

    def extract_year_departement_commune(self, first_table: pd.DataFrame) -> dict:
        """
        Extracts the year, department and commune of the document.

        Args:
            first_table (pd.DataFrame): The first table extracted from the PDF
            because it's the one that contains general informations about the document.

        Returns:
            dict: A dictionary containing 'year', 'departement' and 'commune'.
        """
        if first_table.empty:
            print("The document might not be a cadastral document!")
            return {"year": None, "departement": None, "commune": None}

        year_full_string = (
            first_table.columns[0] if not pd.isna(first_table.columns[0]) else None
        )
        year_match = (
            re.search(r"Année de référence : (\d{4})", year_full_string)
            if year_full_string
            else None
        )
        year = year_match.group(1) if year_match else None

        if year is None:
            print("Document year not found.")

        for column_index in range(1, 8):
            departement_full_string = (
                first_table.columns[column_index]
                if not pd.isna(first_table.columns[column_index])
                else None
            )
            departement_match = (
                re.search(r"Département : (\d+)", departement_full_string)
                if departement_full_string
                else None
            )
            departement = departement_match.group(1) if departement_match else None
            if departement is not None:
                break

        if departement is None:
            print("Document department not found.")

        for column_index in range(2, 9):
            commune_full_string = (
                first_table.columns[column_index]
                if not pd.isna(first_table.columns[column_index])
                else None
            )
            commune_match = (
                re.search(r"Commune : (\d+)", commune_full_string)
                if commune_full_string
                else None
            )
            commune = commune_match.group(1) if commune_match else None
            if commune is not None:
                break

        if commune is None:
            print("Document commune not found.")

        return {"year": year, "departement": departement, "commune": commune}

    def extract_physical_ower_info(self, rows: list) -> dict:
        """
        Extracts physical owner information from a set of rows.

        Args:
            rows (list): A list of rows from a table.

        Returns:
            dict: A dictionary containing the physical owner's information.
        """
        owner_info = {
            "name": None,
            "surname": None,
            "address": None,
            "city": None,
            "postal_code": None,
            "rights": None,
            "owner_number": None,
        }
        for row_index in range(1, len(rows[0])):
            if rows[0][row_index] is not None:
                owner_info["rights"] = rows[0][row_index]
                break
        if owner_info["rights"] is None:
            print("Owner rights not found.")
        found_owner_num_tag = False
        for row_index in range(len(rows[0])):
            if found_owner_num_tag and rows[0][row_index] is not None:
                owner_info["owner_number"] = rows[0][row_index]
                break
            if rows[0][row_index] == "Numéro propriétaire :":
                found_owner_num_tag = True
        if owner_info["owner_number"] is None:
            print("Owner number not found.")
        owner_name_address_string = rows[1][0] if len(rows) > 1 else None
        if owner_name_address_string:
            name_address_match = re.search(
                r"Nom\s*:\s*(.*)\s*Prénom\s*:\s*([^\n]*)\nAdresse\s*:\s*([^\n]*)\n[^\d]*\s*(\d+)\s*(.*)",
                owner_name_address_string,
            )
            if name_address_match:
                owner_info["name"] = name_address_match.group(1).strip()
                owner_info["surname"] = name_address_match.group(2).strip()
                owner_info["address"] = name_address_match.group(3).strip()
                owner_info["postal_code"] = name_address_match.group(4).strip()
                owner_info["city"] = name_address_match.group(5).strip()
            else:
                print("Owner name and address not found in the expected format.")
        else:
            print("Owner name and address string is empty or not found.")
        return owner_info

    def extract_moral_ower_info(self, rows: list) -> dict:
        """
        Extracts moral owner information from a set of rows.

        Args:
            rows (list): A list of rows from a table.

        Returns:
            dict: A dictionary containing the moral owner's information.
        """
        owner_info: dict = {
            "name": None,
            "address": None,
            "city": None,
            "postal_code": None,
            "rights": None,
            "owner_number": None,
        }
        for row_index in range(1, len(rows[0])):
            if rows[0][row_index] is not None:
                owner_info["rights"] = rows[0][row_index]
                break
        if owner_info["rights"] is None:
            print("Owner rights not found.")
        found_owner_num_tag: bool = False
        for row_index in range(len(rows[0])):
            if found_owner_num_tag and rows[0][row_index] is not None:
                owner_info["owner_number"] = rows[0][row_index]
                break
            if rows[0][row_index] == "Numéro propriétaire :":
                found_owner_num_tag = True
        if owner_info["owner_number"] is None:
            print("Owner number not found.")
        owner_name_address_string: str = rows[1][0] if len(rows) > 1 else None
        if owner_name_address_string:
            name_address_match = re.search(
                r"Dénomination\s*:\s*(.*)\nAdresse\s*:\s*([^\n]*)\n[^\d]*\s*(\d+) (.*)",
                owner_name_address_string,
            )
            if name_address_match:
                owner_info["name"] = name_address_match.group(1).strip()
                owner_info["address"] = name_address_match.group(2).strip()
                owner_info["postal_code"] = name_address_match.group(3).strip()
                owner_info["city"] = name_address_match.group(4).strip()
            else:
                print("Owner name and address not found in the expected format.")
        else:
            print("Owner name and address string is empty or not found.")
        return owner_info

    def extract_owners(self, first_table: pd.DataFrame) -> list:
        """
        Extracts the owners of the properties from the first table of the PDF.

        Args:
            first_table (pd.DataFrame): The first table extracted from the PDF.

        Returns:
            list: A list of owners.
        """
        owners: list = []
        first_table_list: list = first_table.values.tolist()
        for row_index in range(len(first_table_list)):
            if first_table_list[row_index][0] == "Droit réel :":
                if row_index + 1 < len(first_table_list) and first_table_list[
                    row_index + 1
                ][0].startswith("Dénomination"):
                    owner_info: dict = self.extract_moral_ower_info(
                        first_table_list[row_index : row_index + 2]
                    )
                    owners.append(owner_info)
                elif row_index + 1 < len(first_table_list) and first_table_list[
                    row_index + 1
                ][0].startswith("Nom"):
                    owner_info: dict = self.extract_physical_ower_info(
                        first_table_list[row_index : row_index + 2]
                    )
                    owners.append(owner_info)
        return owners

    def remove_nones_from_list(self, lst: list) -> list:
        """
        Removes None values from a list.

        Args:
            lst (list): The list from which to remove None values.

        Returns:
            list: A new list with None values removed.
        """
        return [item for item in lst if item is not None]

    def extract_property_info(self, row: list) -> dict:
        """
        Extracts property information from a row of the properties table.

        Args:
            row (list): A list representing a row of the properties table.

        Returns:
            dict: A dictionary containing the property information.
        """
        property_info: dict = {
            "section": None,
            "prefix": None,
            "plan_number": None,
            "name": None,
            "contenance_ha": None,
            "contenance_a": None,
            "contenance_ca": None,
        }
        row = self.remove_nones_from_list(row)
        full_section: str = row[1] if len(row) > 1 else None
        if full_section:
            # Extract section and prefix from the full section string
            section_match = re.match(r"(\d+) ([A-Z]+)", full_section)
            if section_match:
                property_info["prefix"] = section_match.group(1)
                property_info["section"] = section_match.group(2)
            else:
                # Extract only section if prefix is not present
                section_match = re.match(r"([A-Z]+)", full_section)
                if section_match:
                    property_info["section"] = section_match.group(1)
                else:
                    print(f"Section not found in {full_section}.")
        else:
            print("Full section string is empty or not found.")
        property_info["plan_number"] = row[2] if len(row) > 2 else None
        if property_info["plan_number"] is None:
            print("Plan number not found.")
        property_info["name"] = row[4] if len(row) > 4 else None
        if property_info["name"] is None:
            print("Property name not found.")
        property_info["contenance_ha"] = row[13] if len(row) > 13 else None
        if property_info["contenance_ha"] is None:
            print("Contenance ha not found.")
        property_info["contenance_a"] = row[14] if len(row) > 14 else None
        if property_info["contenance_a"] is None:
            print("Contenance a not found.")
        property_info["contenance_ca"] = row[15] if len(row) > 15 else None
        if property_info["contenance_ca"] is None:
            print("Contenance ca not found.")
        return property_info

    def extract_properties_from_tables(self, tables: list) -> list:
        """
        Extracts properties from a list of tables.

        Args:
            tables (list): A list of DataFrames representing the tables extracted from the PDF.

        Returns:
            list: A list of properties.
        """
        properties: list = []
        end_of_properties: bool = False
        for table in tables:
            if "Contenance totale" in table.columns:
                end_of_properties = True
                break
            rows = table.values.tolist()
            for row in rows:
                if row[0] == "Contenance totale":
                    end_of_properties = True
                    break
                if row[0] is not None:
                    try:
                        property_an = int(row[0])
                    except ValueError:
                        property_an = None
                    if property_an is not None:
                        property_info = self.extract_property_info(row)
                        properties.append(property_info)
            if end_of_properties:
                break
        return properties

    def build_id_for_properties(self, properties: list, year_departement_commune: dict):
        """
        Builds unique IDs for each property based on the departement, the commune the section and the plan number.
        Edit the properties list in place.

        Args:
            properties (list): A list of property dictionaries.
            year_departement_commune (dict): A dictionary containing 'year', 'departement' and 'commune' of the document.
        """
        for property_info in properties:
            section: str = property_info.get("section", "")
            if not section:
                print("Section is missing in property info.")
                continue
            prefix: str = (
                property_info.get("prefix", "") if property_info.get("prefix") else ""
            )
            plan_number: str = property_info.get("plan_number", "")
            if not plan_number:
                print("Plan number is missing in property info.")
                continue
            prefix_section = (prefix + section).rjust(5, "0")
            plan_number = plan_number.rjust(4, "0")
            departement: str = year_departement_commune.get("departement", "")
            if not departement:
                print("Departement is missing in year_departement_commune.")
                continue
            commune = year_departement_commune.get("commune", "")
            if not commune:
                print("Commune is missing in year_departement_commune.")
                continue
            id: str = departement + commune + prefix_section + plan_number
            property_info["id"] = id
        return properties

    def convert_result_into_final_display(
        self,
        year_departement_commune: dict,
        owners: list,
        properties: list,
        file_name: str,
    ) -> list:
        """
        Converts the extracted informations into a pandas DataFrame with one line per owners/properties.

        Args:
            year_departement_commune (dict): A dictionary containing 'year', 'departement' and 'commune'.
            owners (list): A list of owners.
            properties (list): A list of properties.
            file_name (str): The name of the PDF file.

        Returns:
            list: A list of dictionaries, each representing a row in the final DataFrame.
        """
        results = []
        for owner in owners:
            for property_info in properties:
                results.append(
                    {
                        "departement": year_departement_commune.get("departement"),
                        "commune": year_departement_commune.get("commune"),
                        "prefix": (
                            property_info.get("prefix", "")
                            if property_info.get("prefix")
                            else ""
                        ),
                        "section": property_info.get("section", ""),
                        "plan_number": property_info.get("plan_number", ""),
                        "contenance_ha": property_info.get("contenance_ha", ""),
                        "contenance_a": property_info.get("contenance_a", ""),
                        "contenance_ca": property_info.get("contenance_ca", ""),
                        "droit_reel": owner.get("rights", ""),
                        "designation_parcelle": property_info.get("name", ""),
                        "nom": owner.get("name", ""),
                        "prenom": owner.get("surname", ""),
                        "numero_majic": owner.get("owner_number", ""),
                        "voie": owner.get("address", ""),
                        "code_postal": owner.get("postal_code", ""),
                        "ville": owner.get("city", ""),
                        "id": property_info.get("id", ""),
                        "fichier_source": file_name,
                    }
                )
        return results