import pdfplumber
import os
import re
import json
from pathlib import Path

class ConstitutionParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.current_chapter = None
        self.current_part = None
        self.current_article = None
        self.current_chunk_text = ""
        self.final_chunks = []

    def process_document(self):
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Stripping the first 12 pages
                pages_to_process = pdf.pages[12:]
                # Cropping the page to remove the headers and footers
                for i, page in enumerate(pages_to_process):
                    cropped_page = page.crop(bbox = (0, page.height*0.17, page.width, page.height*0.90))
                    text = cropped_page.extract_text(x_tolerance=2, y_tolerance=3)
                    # Removing the incomplete line breaks
                    cleaned_text = self._clean_and_merge_text(text or "")
                    tables = cropped_page.extract_tables()
                    images = cropped_page.images
                    page_data = {
                        "page_number": i + 13,  # Adjusting for the stripped pages
                        "text": cleaned_text, 
                        "tables": tables,
                        "images": images
                    }
                    self.final_chunks.append(page_data)

            return self.final_chunks
                                
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return []        
    
    def _clean_and_merge_text(self, text):
        # Remove line breaks that are not followed by a new paragraph 
        cleaned_text = re.sub(r'-\s*\n\s*', '', text)
        return cleaned_text

def create_article_chunks(page_chunks):
    print("Merging pages and generating Article chunks...")
    
    # Merging all pages text
    full_text = "\n".join([page["text"] for page in page_chunks if page["text"]])
    lines = full_text.split('\n')
    
    semantic_chunks = []
    
    # Tracking current chapter, part and article
    current_chapter = None
    current_part = None
    current_article = None
    current_chunk_text = ""

    # Iterating line by line
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # Identifying chapters, parts and articles
        if re.match(r"^CHAPTER\s+[A-Z]+", line_stripped):
            current_chapter = line_stripped
            current_part = None 
            continue
            
        if re.match(r"^PART\s+[A-Z0-9]+", line_stripped):
            current_part = line_stripped
            continue
            
        # Articles (e.g., "14. (1)")
        if re.match(r"^\d+\.\s", line_stripped):
            
            # Saving the article chunk
            if current_chunk_text.strip() and current_article:
                semantic_chunks.append({
                    "chapter": current_chapter,
                    "part": current_part,
                    "article": current_article,
                    "text": current_chunk_text.strip()
                })

            # Tracking the current article
            current_article = line_stripped
            current_chunk_text = line + "\n"
        else:
            current_chunk_text += line + "\n"
            
    # Saving the last article
    if current_chunk_text.strip() and current_article:
        semantic_chunks.append({
            "chapter": current_chapter,
            "part": current_part,
            "article": current_article,
            "text": current_chunk_text.strip()
        })
        
    print(f"Successfully generated {len(semantic_chunks)} article chunks!")
    return semantic_chunks



class CaseLawParser:
    def __init__ (self, pdf_path, court, year, month,case_name):
        self.pdf_path = pdf_path
        self.court = court
        self.year = year
        self.month = month
        self.case_name = case_name
        self.final_chunks = []
    
    def process_document(self):
        replacements = {
            "\ue000": "ff",   # affadavit
            "\ue001": "fi",   # finding
            "\ue002": "fl",   # conflict
            "\ue003": "ffi",  # office
            "\ue004": "ffl",  # waffle
            "’": "'",         # Normalize curly quotes
            "“": '"',         # Normalize curly double quotes
            "”": '"'
        }
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    # Cropping the page to remove the headers and footers
                    if i == 0:
                        cropped_page = page.crop((0, 138, page.width, page.height-65))
                    else:
                        cropped_page = page.crop((0,0, page.width, page.height-65))
                    text = cropped_page.extract_text(x_tolerance=2, y_tolerance=3)
                    
                    if text:
                        # Removing the bad parsing characters
                        for bad_char, good_char in replacements.items():
                            text = text.replace(bad_char, good_char)
                        text = re.sub(r'-\s*\n\s*', '', text)
                        self.final_chunks.append({
                            "court": self.court,
                            "year": self.year,
                            "month": self.month,
                            "case_name": self.case_name,
                            "page": i +1,
                            "text": text.strip()
                        })
                       
        except Exception as e:
            print(f"Error processing document: {e}")
        return self.final_chunks

    
def case_laws(base_directory):
    print("Processing case law documents...")
    base_path = Path(base_directory)
    all_case_laws_chunks = []

    for pdf_file in base_path.rglob("*.pdf"):
        # Extracting metadata from the file path
        parts = pdf_file.parts
        case_name = pdf_file.stem
        month = parts[-2]
        year = parts[-3]
        court = parts[-4]

        print(f"Processing [{court} | {year} | {month}] -> {case_name}")
        parser2 = CaseLawParser(str(pdf_file), court, year, month, case_name)
        document_chunks = parser2.process_document()
        all_case_laws_chunks.extend(document_chunks)
    return all_case_laws_chunks
    

        
# --- ENTRY POINT ---
if __name__ == "__main__":
    print("Processing the Constitution of Kenya...")
    parser = ConstitutionParser(pdf_path=r"Datasets\Raw_data\constitution\TheConstitutionOfKenya.pdf")
    parsed_data = parser.process_document()
    article_chunks = create_article_chunks(parsed_data)
    # Saving the payload to a JSON file
    output_filename = "Datasets/Processed_data/constitution_chunks.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(article_chunks, f, ensure_ascii=False, indent=4)
    print(f"Payload saved to {output_filename}")
    
    # Case laws processing entry point
    base_directory = r"Datasets\Raw_data\case_laws"
    case_laws_data = case_laws(base_directory)
    output_filename = r"Datasets/Processed_data/caselaws_chunks.json"
    Path(output_filename).parent.mkdir(parents=True, exist_ok=True) 
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(case_laws_data, f, ensure_ascii=False, indent=4)
    print(f"Case laws saved to {output_filename}")