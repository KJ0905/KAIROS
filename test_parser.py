
from pathlib import Path

from backend.resume_parser import read_pdf, parse_resume

resume_path = Path("backend") / "my_resume.pdf"

text = read_pdf(resume_path)

print("Extracted text length:", len(text))
print("\nFirst 500 characters:\n")
print(text[:500])

resume = parse_resume(text)

print("\nStructured resume:\n")
print(resume.model_dump_json(indent=2))
