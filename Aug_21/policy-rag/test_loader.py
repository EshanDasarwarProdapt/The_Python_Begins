import logging
from llama_index.core import SimpleDirectoryReader
import os

logging.basicConfig(level=logging.INFO)
print("Loading PDFs...")
docs = SimpleDirectoryReader(input_dir="data/raw", required_exts=[".pdf"]).load_data()
for doc in docs:
    print(f"File: {doc.metadata.get('file_name')}")
    print(f"Text snippet: {doc.text[:100]}...")
    print("-" * 20)
