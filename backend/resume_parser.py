import json
import re
from pathlib import Path
from urllib.parse import urlparse

from groq import Groq
from pypdf import PdfReader

from backend.config import GROQ_API_KEY, GROQ_MODEL
from backend.schemas import ProfileLinks, Resume


client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


URL_PATTERN = re.compile(
    r"https?://[^\s<>\"']+|"
    r"(?<![@\w])(?:www\.)?"
    r"(?:linkedin\.com|github\.com|"
    r"codeforces\.com|codechef\.com|"
    r"atcoder\.jp|leetcode\.com|"
    r"gitlab\.com|kaggle\.com)"
    r"/[^\s<>\"']+",
    re.IGNORECASE
)


def normalize_url(url: str) -> str:
    url = url.strip().rstrip(".,;:!?)\]}")

    if url.lower().startswith("www."):
        url = "https://" + url

    elif not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    return url


def extract_urls_from_text(text: str) -> list[str]:
    urls = [
        normalize_url(match.group(0))
        for match in URL_PATTERN.finditer(text)
    ]

    return list(dict.fromkeys(urls))


def extract_pdf_links(pdf_path: Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    links = []

    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()

            if annotation.get("/Subtype") != "/Link":
                continue

            action = annotation.get("/A")

            if not action:
                continue

            action = action.get_object()
            uri = action.get("/URI")

            if uri and str(uri).startswith(("https://", "http://")):
                links.append(str(uri))

    return list(dict.fromkeys(links))


def categorize_urls(urls: list[str]) -> ProfileLinks:
    links = {
        "linkedin": None,
        "github": None,
        "codeforces": None,
        "codechef": None,
        "atcoder": None,
        "portfolio": None,
        "other_links": []
    }

    for url in urls:
        try:
            host = (urlparse(url).hostname or "").lower()
        except ValueError:
            links["other_links"].append(url)
            continue

        if host == "linkedin.com" or host.endswith(".linkedin.com"):
            links["linkedin"] = links["linkedin"] or url

        elif host == "github.com" or host.endswith(".github.com"):
            links["github"] = links["github"] or url

        elif host == "codeforces.com" or host.endswith(".codeforces.com"):
            links["codeforces"] = links["codeforces"] or url

        elif host == "codechef.com" or host.endswith(".codechef.com"):
            links["codechef"] = links["codechef"] or url

        elif host == "atcoder.jp" or host.endswith(".atcoder.jp"):
            links["atcoder"] = links["atcoder"] or url

        elif host in {
            "leetcode.com",
            "gitlab.com",
            "kaggle.com"
        } or host.endswith((".gitlab.com", ".kaggle.com")):
            links["other_links"].append(url)

        else:
            links["portfolio"] = links["portfolio"] or url

    return ProfileLinks.model_validate(links)


def read_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            pages.append(page_text)

    return "\n".join(pages).strip()


def parse_resume(resume_text: str,pdf_links: list[str] | None = None,) -> Resume:
    if not client:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    if not resume_text.strip():
        raise ValueError(
            "No readable text was found in the PDF resume."
        )

    visible_urls = extract_urls_from_text(resume_text)

    all_urls = list(dict.fromkeys(
        visible_urls + (pdf_links or [])
    ))

    resume_schema = Resume.model_json_schema()

    system_prompt = f"""
You are an expert resume parser.

Extract information based on the meaning of the resume,
not only exact section headings.

For example, work experience may appear under:
- Experience
- Professional Experience
- Work History
- Employment
- Internships

Extract skills mentioned throughout the resume, including
skills used in projects and work experience.

Return only valid JSON matching this schema:

{json.dumps(resume_schema)}

Rules:
1. Never invent information.
2. Use null for missing scalar values.
3. Use empty lists for missing list values.
4. Include internships in experiences.
5. Keep project and achievement descriptions faithful to the resume.
6. Extract personal profile links into profile_links.
7. Extract each project into projects.
8. For every project, extract its name and associate its
   GitHub repository URL with github in project_links.
9. Associate a live deployment URL with demo in project_links.
10. Include all project URLs, not just the first one.
11. If a URL cannot be confidently associated with a project,
    preserve it in other_links rather than guessing.
12. Never use the personal GitHub profile URL as a project repository URL.
13. Return valid JSON matching the provided schema only.
"""

    user_prompt = f"""
Parse the following resume.

URLs found in the resume, including embedded PDF hyperlinks:
{json.dumps(all_urls)}

Resume text:
{resume_text[:45000]}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    raw_output = response.choices[0].message.content

    if not raw_output:
        raise ValueError("The AI returned an empty response.")

    data = json.loads(raw_output)

    # Validate the AI-generated resume.
    resume = Resume.model_validate(data)

    # Merge visible URLs with links extracted from PDF annotations.
    # The caller can merge the annotation URLs after reading the PDF.
    extracted_links = categorize_urls(all_urls)

    existing_links = resume.profile_links.model_dump()

    for field in (
        "linkedin",
        "github",
        "codeforces",
        "codechef",
        "atcoder",
        "portfolio"
    ):
        if not existing_links.get(field):
            existing_links[field] = getattr(extracted_links, field)

    existing_links["other_links"] = list(dict.fromkeys(
        existing_links.get("other_links", [])
        + extracted_links.other_links
    ))

    resume.profile_links = ProfileLinks.model_validate(existing_links)
    print("\n--- PROJECTS EXTRACTED BY AI ---")
    print(json.dumps(
        [p.model_dump() for p in resume.project_links],
        indent=2
    ))
    print("\n--- PROFILE LINKS ---")
    print(resume.profile_links.model_dump_json(indent=2))
    return resume

