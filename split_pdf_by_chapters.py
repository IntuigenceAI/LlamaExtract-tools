import os
import re
from PyPDF2 import PdfReader, PdfWriter
from typing import List, Tuple, Dict

def extract_text_from_pdf(pdf_path: str) -> Dict[int, str]:
    """
    Extract text from each page of the PDF.

    Args:
        pdf_path (str): Path to the input PDF file

    Returns:
        Dict[int, str]: Dictionary mapping page numbers to extracted text
    """
    reader = PdfReader(pdf_path)
    page_texts = {}

    for page_num, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
            page_texts[page_num] = text
        except Exception as e:
            print(f"Error extracting text from page {page_num + 1}: {e}")
            page_texts[page_num] = ""

    return page_texts

def detect_chapters(page_texts: Dict[int, str]) -> List[Tuple[int, str]]:
    """
    Detect chapter starts in the PDF text.

    Args:
        page_texts (Dict[int, str]): Dictionary of page numbers to text content

    Returns:
        List[Tuple[int, str]]: List of tuples containing (page_number, chapter_title)
    """
    chapters = []

    # Improved chapter patterns to reduce false positives
    chapter_patterns = [
        r'(?i)^\s*(Topic\s+[IVX]+:\s*[A-Z][A-Za-z\s:,&/()-]+)',  # "Topic I: Mass/Energy Balances"
        r'(?i)^\s*(\d+\.\s+[A-Z][A-Za-z\s:,&-]+)$',  # "1. Fluid Properties"
        r'(?i)^\s*chapter\s+(\d+\.?\s*[A-Z][^\n]+)',  # "Chapter 4. Fluid Dynamics"
        r'(?i)^\s*chapter\s+(\w+\.?\s*[A-Z][^\n]+)',  # "Chapter Four. Fluid Dynamics"
    ]

    for page_num, text in page_texts.items():
        if not text.strip():
            continue

        lines = text.split('\n')

        # Check first few lines of each page for chapter markers
        for i, line in enumerate(lines[:5]):  # Check first 5 lines only
            line = line.strip()
            if not line:
                continue

            for pattern in chapter_patterns:
                match = re.search(pattern, line)
                if match:
                    # Extract the full chapter title
                    chapter_title = match.group(1).strip()

                    # Clean up the title
                    chapter_title = re.sub(r'\s+', ' ', chapter_title)

                    # Filter out false positives
                    if (len(chapter_title) > 10 and  # Must be reasonably long
                        not re.search(r'^\d+\.?\d*\s*(psi|ft|m|cm|kg|lbm|hr|°F|°C|kPa|Btu)', chapter_title) and  # Not measurements
                        not re.search(r'^\d+\.?\d*\s+(mol|m3|ft3|L/s)', chapter_title) and  # Not units
                        'equation' not in chapter_title.lower() and  # Not equation references
                        chapter_title.count('.') <= 2):  # Not overly complex numbers

                        chapters.append((page_num, chapter_title))
                        print(f"Found chapter on page {page_num + 1}: {chapter_title}")
                        break

    # Remove duplicates and sort by page number
    chapters = list(set(chapters))
    chapters.sort(key=lambda x: x[0])

    return chapters

def create_chapter_filename(chapter_title: str, chapter_num: int) -> str:
    """
    Create a clean filename from chapter title.

    Args:
        chapter_title (str): The chapter title
        chapter_num (int): Chapter number for ordering

    Returns:
        str: Clean filename
    """
    # Remove problematic characters for filenames
    clean_title = re.sub(r'[^\w\s-]', '', chapter_title)
    clean_title = re.sub(r'\s+', '_', clean_title.strip())
    clean_title = clean_title[:50]  # Limit length

    return f"Chapter_{chapter_num:02d}_{clean_title}.pdf"

def split_pdf_by_chapters(input_pdf_path: str, output_dir: str, chapters: List[Tuple[int, str]]) -> List[str]:
    """
    Split the PDF into separate files based on detected chapters.

    Args:
        input_pdf_path (str): Path to the input PDF file
        output_dir (str): Directory where chapter PDFs will be saved
        chapters (List[Tuple[int, str]]): List of chapter start pages and titles

    Returns:
        List[str]: List of created chapter file paths
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    created_files = []

    for i, (start_page, chapter_title) in enumerate(chapters):
        # Determine end page (start of next chapter - 1, or last page)
        if i + 1 < len(chapters):
            end_page = chapters[i + 1][0] - 1
        else:
            end_page = total_pages - 1

        # Create new PDF for this chapter
        writer = PdfWriter()

        for page_num in range(start_page, end_page + 1):
            if page_num < total_pages:
                writer.add_page(reader.pages[page_num])

        # Create filename and save
        filename = create_chapter_filename(chapter_title, i + 1)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "wb") as f:
            writer.write(f)

        created_files.append(filepath)
        page_range = f"{start_page + 1}-{end_page + 1}" if start_page != end_page else str(start_page + 1)
        print(f"Created: {filename} (pages {page_range})")

    return created_files

def manual_chapter_input() -> List[Tuple[int, str]]:
    """
    Allow user to manually input chapter information if automatic detection fails.

    Returns:
        List[Tuple[int, str]]: List of manually entered chapters
    """
    chapters = []
    print("\nAutomatic chapter detection completed.")
    print("You can manually add or modify chapters if needed.")
    print("Enter chapter information (or press Enter to finish):")

    while True:
        try:
            page_input = input("\nEnter page number (1-based) for chapter start (or Enter to finish): ")
            if not page_input.strip():
                break

            page_num = int(page_input) - 1  # Convert to 0-based
            if page_num < 0:
                print("Page number must be positive")
                continue

            title = input("Enter chapter title: ").strip()
            if not title:
                print("Chapter title cannot be empty")
                continue

            chapters.append((page_num, title))
            print(f"Added: Page {page_num + 1} - {title}")

        except ValueError:
            print("Please enter a valid page number")
        except KeyboardInterrupt:
            print("\nExiting manual input...")
            break

    chapters.sort(key=lambda x: x[0])
    return chapters

def main():
    """
    Main function to orchestrate the PDF splitting process.
    """
    # Configuration
    input_pdf = "/Users/dijanajanjetovic/IntuigenceAI/Dijana_work/scrapper-poc/output2/Six-Minute Solutions for Chemical PE Exam Problems/auto/Six-Minute Solutions for Chemical PE Exam Problems_origin.pdf"
    output_dir = "/Users/dijanajanjetovic/IntuigenceAI/Dijana_work/topic_pdfs"

    print(f"Processing PDF: {input_pdf}")
    print(f"Output directory: {output_dir}")

    # Check if input file exists
    if not os.path.exists(input_pdf):
        print(f"Error: Input file not found: {input_pdf}")
        return

    try:
        # Step 1: Extract text from all pages
        print("\n1. Extracting text from PDF pages...")
        page_texts = extract_text_from_pdf(input_pdf)
        print(f"Successfully extracted text from {len(page_texts)} pages")

        # Step 2: Detect chapters automatically
        print("\n2. Detecting chapters...")
        detected_chapters = detect_chapters(page_texts)

        if not detected_chapters:
            print("No chapters detected automatically.")
            print("The script will attempt to split by major sections if any patterns are found.")
            return
        else:
            print(f"\nDetected {len(detected_chapters)} chapters:")
            for page_num, title in detected_chapters:
                print(f"  Page {page_num + 1}: {title}")

            chapters = detected_chapters

        if not chapters:
            print("No chapters to process. Exiting.")
            return

        # Step 3: Split PDF by chapters
        print(f"\n3. Splitting PDF into {len(chapters)} chapters...")
        created_files = split_pdf_by_chapters(input_pdf, output_dir, chapters)

        # Step 4: Summary
        print(f"\n✅ Successfully created {len(created_files)} chapter files:")
        for filepath in created_files:
            filename = os.path.basename(filepath)
            print(f"  - {filename}")

        print(f"\nAll files saved to: {output_dir}")

    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()