# RAG Document Indexer

A robust Python pipeline designed to ingest, chunk, embed, and index documents (PDF & DOCX) into a PostgreSQL vector database. This tool is built to support **Retrieval-Augmented Generation (RAG)** applications by leveraging Google's Gemini API for embeddings and Supabase/PostgreSQL for vector storage.

## 🚀 Features

* **Multi-Format Support**: Automatically detects and parses text from `.pdf` and `.docx` files.
* **Smart Chunking**: Implements a **Fixed-size with Overlap** strategy to ensure context retention across chunk boundaries.
* **AI Embeddings**: Generates high-quality vector embeddings using Google's **Gemini `text-embedding-004` model**.
* **Rate Limit Protection**: Built-in mechanisms to handle API rate limits gracefully.
* **Vector Storage**: efficiently stores text chunks and their vector representations in PostgreSQL using `pgvector`.

## 🛠️ Prerequisites

Before running the script, ensure you have the following:

* **Python 3.8+** installed.
* A **Google Cloud API Key** with access to the Gemini API.
* A **PostgreSQL Database** (e.g., Supabase, Neon) with the `pgvector` extension enabled.

## 📦 Installation

1.  **Clone the repository:**

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Setup:**
    Create a `.env` file in the root directory of the project and add your credentials:
    ```env
    GEMINI_API_KEY=your_google_api_key_here
    POSTGRES_URL=postgresql://user:password@host:port/database
    ```

## 🗄️ Database Setup

You must create the required table in your PostgreSQL database before running the script. Run the following SQL command in your database's SQL Editor:

```sql
-- Enable the vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    chunk_text TEXT NOT NULL,
    embedding FLOAT8[],
    filename TEXT NOT NULL,
    split_strategy TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
💻 Usage
Run the script from the command line by providing the path to the document you wish to index.

Syntax:

Bash

python index_documents.py <path_to_file>
Example:

Bash

python index_documents.py "./documents/employee_handbook.pdf"
Expected Output
Plaintext

Recieved input file: ./documents/employee_handbook.pdf
Starting Process for: ./documents/employee_handbook.pdf 
Reading file: ./documents/employee_handbook.pdf...
Split text into 12 paragraphs.
Saving 12 chunks to DB
Successfully saved 12 chunks to the database.
🧩 Code Structure
The project is structured around the DocumentIndexer class, which handles the entire pipeline:

extract_text(file_path): Determines file type (PDF/DOCX) and extracts raw text using pypdf or python-docx.

chunk_text(text): Splits the raw text into manageable pieces using a sliding window approach (default: 1000 characters with 100 overlap).

get_embedding(text): Sends the chunk to Google Gemini API and retrieves the vector embedding.

save_to_db(...): Connects to PostgreSQL and safely inserts the text, embedding, and metadata.