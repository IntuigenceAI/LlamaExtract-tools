#!/usr/bin/env python3

import os
import json
import time
from llama_cloud_services import LlamaExtract
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv("general.env")
api_key = os.getenv("LLAMA_CLOUD_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = api_key

# Define extraction schema for Q&A pairs with images
class MultipleChoiceOptions(BaseModel):
    A: str = Field(description="Option A text with units")
    B: str = Field(description="Option B text with units")
    C: str = Field(description="Option C text with units")
    D: str = Field(description="Option D text with units")

class SolutionImage(BaseModel):
    description: str = Field(description="Description of what the image shows (diagram, chart, graph, etc.)")
    image_data: Optional[str] = Field(description="Base64 encoded image data if available")

class Solution(BaseModel):
    method: str = Field(description="Step-by-step solution method")
    calculations: str = Field(description="Mathematical calculations")
    final_answer: str = Field(description="Final answer with units")
    images: List[SolutionImage] = Field(description="Any diagrams, charts, or figures used in the solution", default=[])

class QuestionAnswer(BaseModel):
    question_number: str = Field(description="Question number")
    question_text: str = Field(description="Full question text")
    question_images: List[SolutionImage] = Field(description="Any diagrams or figures shown with the question", default=[])
    multiple_choice_options: MultipleChoiceOptions
    correct_answer: str = Field(description="Correct answer: A, B, C, or D")
    customary_us_solution: Solution = Field(description="US imperial units solution with any relevant images")
    si_solution: Solution = Field(description="SI metric units solution with any relevant images")

class ChapterQA(BaseModel):
    questions: List[QuestionAnswer] = Field(description="All questions and answers in chapter with images")

def main():
    # Initialize LlamaExtract
    llama_extract = LlamaExtract()

    # Create extraction agent with unique name
    print("Creating extraction agent with image support...")
    agent_name = f"engineering-qa-images-{int(time.time())}"
    agent = llama_extract.create_agent(name=agent_name, data_schema=ChapterQA)
    print("Agent created!")

    # Directory paths
    chapter_pdfs_dir = "/Users/dijanajanjetovic/IntuigenceAI/Dijana_work/chapter_pdfs"
    output_dir = "/Users/dijanajanjetovic/IntuigenceAI/Dijana_work/extracted_qa_with_images"

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Get all PDF files
    pdf_files = [f for f in os.listdir(chapter_pdfs_dir) if f.endswith('.pdf')]
    pdf_files.sort()

    print(f"Found {len(pdf_files)} PDFs to process")

    # Process each PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(chapter_pdfs_dir, pdf_file)
        output_file = os.path.join(output_dir, f"{pdf_file[:-4]}.json")

        # Skip if already processed
        if os.path.exists(output_file):
            print(f"[{i}/{len(pdf_files)}] Skipping: {pdf_file} (already processed)")
            continue

        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file}")

        try:
            # Extract Q&A data with images
            result = agent.extract(pdf_path)
            extracted_data = result.data

            # Save to JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Saved: {output_file}")
            print(f"   Found {len(extracted_data.get('questions', []))} questions")

        except Exception as e:
            print(f"❌ Error processing {pdf_file}: {e}")
            continue

    print("🎉 Extraction with images complete!")

if __name__ == "__main__":
    main()