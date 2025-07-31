# Cadastre PDF Extractor

This a Python script that extracts informations from PDF files, specifically designed to handle the structure of cadastre documents.
The interface is built using streamlit, allowing users to upload PDF files and view the extracted informations.

## Installation

To run this script locally, you need to have Python installed on your machine.
It is recommended to use a virtual environment.

### Follow these steps to set up the environment

1. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command in your terminal:

```bash
streamlit run streamlit_app.py
```

This will start a local server, and you can access the application in your web browser at `http://localhost:8501`.

## Testing

You can run the tests using pytest:

```bash
pytest tests/tests_all_examples.py
```
