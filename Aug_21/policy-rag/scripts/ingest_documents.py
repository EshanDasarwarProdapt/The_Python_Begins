#!/usr/bin/env python
"""
ingest_documents.py - CLI script to run the ingestion pipeline.
"""
import sys
import os
import logging
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.ingest import run_ingestion_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("============================================================")
    print("  Enterprise Policy RAG - Ingestion Pipeline                ")
    print("============================================================")
    report = run_ingestion_pipeline()
    print("\n[Ingestion Report]")
    print(json.dumps(report, indent=2))
    print("============================================================")
