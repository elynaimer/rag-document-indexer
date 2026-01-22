import os
import sys
import datetime
from typing import List
import google.generativeai as genai
import psycopg2
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document
import time

#Grt safely stored keys from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
POSTGRES_URL = os.getenv("POSTGRES_URL")

#initializing the AI with the API key 
genai.configure(api_key=GEMINI_API_KEY)

class DocumentIndexer:
    def __init__(self, db_url):
        self.db_url = db_url

    def extract_text(self, file_path: str) -> str:
        #Extracting actual text from PDF or DOCX files

        # Get the file extension 
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
    
        try:
            print(f"Reading file: {file_path}...")

            #for PDFs
            if ext == '.pdf':
                reader = PdfReader(file_path)
                # Get the text
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        
            # for Docs
            elif ext == '.docx':
                doc = Document(file_path)
                # Join all paragraphs into one big text with newlines
                text = "\n".join([para.text for para in doc.paragraphs])
        
            # unsupported files
            else:
                print(f"Unsupported format: {ext}")
                return None
        
            # Clean up whitespace
            clean_text = text.strip()
            return clean_text

        except Exception as e:
            print(f"Error reading file: {e}")
            return None

    def chunk_text(self, text: str,chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        #Separating the text to chunks by a fixed size and overlap
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            
            # Slice the text
            chunk = text[start:end]

            #if text not empty save it
            if chunk.strip():
                chunks.append(chunk)    

            start += (chunk_size - overlap)



        #Return the chunking strategy name
        split_strategy = f'FIxed size with overlap({chunk_size},{overlap})'
            
        return chunks, split_strategy
    
    def get_embedding(self, text: str) -> List[float]:
        #getting an embedding for a specific chunk
         
        try:
            # Using embeddings model 
            result = genai.embed_content(
                model="models/text-embedding-004", 
                content=text,
                task_type="retrieval_document"
            )
            
            #one second sleep in order to prevent rate limit problems 
            time.sleep(1)
            return result['embedding']
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None


    def save_to_db(self, filename: str, chunks: List[str], strategy_name: str):
        #processing the chunks, embedding them and then saving to db 

        conn = None
        try:
            # Connect to the database
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # The SQL Query
            query = """
                INSERT INTO document_chunks 
                (chunk_text, embedding, filename, split_strategy, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            success_count = 0
            print(f"Saving {len(chunks)} chunks to DB")
            
            # Loop through chunks generate embedding and save
            for chunk in chunks:
                embedding = self.get_embedding(chunk)
                
                if embedding:
                    cur.execute(query, (
                        chunk, 
                        embedding, 
                        filename, 
                        strategy_name, 
                        datetime.datetime.now()
                    ))
                    success_count += 1
            
            #Save changes
            conn.commit()
            print(f"Successfully saved {success_count} chunks to the database.")
            
        except Exception as e:
            print(f"Database Error: {e}")
        finally:
            if conn:
                conn.close()

    def process_file(self, file_path):
        #Manage the Extract -> Split -> Embed -> Save process 
        
        print(f"Starting Process for: {file_path} ")
        
        # Extract 
        text = self.extract_text(file_path)
        if not text:
            print("Aborting: No text found in file.")
            return

        #Split
        chunks, strategy_name = self.chunk_text(text)
        print(f"Split text into {len(chunks)} paragraphs.")

        # Embed and Save
        if chunks:
            self.save_to_db(os.path.basename(file_path), chunks, strategy_name)
        else:
            print("Warning: Text was empty after splitting.")









# --- Main Execution Block ---
# This part only runs when you execute the script from the terminal
if __name__ == "__main__":
    # 1. Initialize our Indexer with the DB URL
    indexer = DocumentIndexer(POSTGRES_URL)
    
    # 2. Handle the "Input" 
    # sys.argv[0] is always the name of the script ("index_documents.py")
    # sys.argv[1] is the first argument you pass ("myfile.pdf")
    
    if len(sys.argv) > 1:
        # If the user provided a file path in the terminal, use it
        input_file = sys.argv[1]
        
        if os.path.exists(input_file):
            # This is where we will call the main process function later
            print(f"Recieved input file: {input_file}")
            indexer.process_file(input_file) 
        else:
            print(f"Error: The file '{input_file}' was not found.")
    else:
        # If no input was provided, show instructions
        print("Please provide a file path as input.")
        print("Usage: python index_documents.py <path_to_file>")
