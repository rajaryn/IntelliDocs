# IntelliDocs: AI-Powered Document Manager

IntelliDocs is a web application designed to help you manage and understand your PDF documents. Simply upload a document, and the application will automatically store it securely, extract its content, and generate a concise summary and relevant tags using a locally-run AI model.

## About The Project

In an age of information overload, finding key insights within large documents can be a challenge. This project was built to solve that problem by leveraging the power of Large Language Models (LLMs) to automate the analysis of PDF files. It provides a clean interface to upload, view, and manage your documents, with AI-generated metadata making them easier to understand and organize at a glance.

## Features

* **Secure Document Upload:** Upload your PDF files through a simple web interface.
* **Cloud Storage:** All documents are securely stored using Cloudinary for reliable access.
* **Automatic Text Extraction:** The application automatically parses and extracts text content from your PDFs upon upload.
* **AI-Powered Summarization:** Using a local LLM via Ollama, a concise summary is generated for every document.
* **AI-Powered Tagging:** Key topics and themes are identified and extracted as searchable tags.
* **Document Management:** A dashboard to view, manage, and delete your uploaded documents.

### Work in Progress
* **Semantic Search:** We are currently working on a powerful semantic search feature that will allow you to find documents based on the *meaning* of your query, not just keywords.

## Technology Stack

This project is built with a modern and robust set of technologies:

* **Backend:** Python 3, Flask
* **Database:** MySQL
* **AI / ML:** Ollama for local Large Language Model inference
* **File Storage:** Cloudinary
* **Frontend:** HTML, CSS, JavaScript with Jinja2 for templating
* **Environment:** Python Virtual Environment (`venv`), `python-dotenv` for secret management

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

You will need the following software installed on your machine:
* [Python 3.10+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads/)
* [MySQL Server](https://dev.mysql.com/downloads/mysql/)
* [Ollama](https://ollama.com/) (with a model pulled, e.g., `ollama run qwen2.5:1.5b`)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your_username/your_project_repository.git](https://github.com/your_username/your_project_repository.git)
    cd your_project_repository
    ```

2.  **Create and activate a virtual environment:**
    * On Windows (Git Bash):
        ```bash
        python -m venv venv
        source venv/Scripts/activate
        ```
    * On macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You can generate this file with `pip freeze > requirements.txt`)*

4.  **Set up your environment variables:**
    * Create a copy of the example environment file:
        ```bash
        cp .env.example .env
        ```
    * Open the `.env` file and fill in your specific credentials for the database, Cloudinary, and Flask secret key.

    **`.env.example` should look like this:**
    ```ini
    # Flask Configuration
    SECRET_KEY='your_super_secret_key_here'

    # Database Configuration
    DB_HOST='localhost'
    DB_USER='your_db_user'
    DB_PASSWORD='your_db_password'
    DB_NAME='your_db_name'

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME='your_cloud_name'
    CLOUDINARY_API_KEY='your_api_key'
    CLOUDINARY_API_SECRET='your_api_secret'
    ```

5.  **Set up the database:**
    * Ensure your MySQL server is running.
    * Connect to MySQL and create the database specified in your `.env` file.
    * Run the initial database migration/schema setup script (e.g., `flask db upgrade` or `python setup_database.py` - *you will need to create this script*).

### Usage

Once the setup is complete, you can run the Flask development server:

```bash
flask run
```
Open your web browser and navigate to `http://127.0.0.1:5000` to start using the application.

## Roadmap

See the [open issues](https://github.com/your_username/your_project_repository/issues) for a full list of proposed features and known issues. In addition to the semantic search feature, future plans include:
* Expanding support for other document types (e.g., `.docx`, `.txt`).
* Batch uploading capabilities.
* Enhanced user management and sharing features.