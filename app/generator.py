import json
import os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from .latex_utils import escape_latex, compile_latex_to_pdf
from groq import Groq
load_dotenv()

SYSTEM_PROMPT = """You are an expert resume writer. Your job is to take raw user-provided 
career information and transform it into polished, ATS-friendly resume content.

Rules:
- Use strong action verbs to start every bullet point (Built, Reduced, Led, Designed, etc.)
- Quantify achievements wherever possible — if the user gives vague info, make a reasonable 
  inference but keep it believable
- Keep bullets concise — one line ideally, two lines max
- Never fabricate companies, degrees, or job titles — only improve the phrasing
- Return ONLY valid JSON, no explanation, no markdown code fences, nothing else

Return this exact JSON structure:
{
  "name": "string",
  "phone": "string",
  "email": "string",
  "linkedin": "string (just the display text like linkedin.com/in/username)",
  "linkedin_url": "string (full URL like https://linkedin.com/in/username)",
  "github": "string (just the display text like github.com/username)",
  "github_url": "string (full URL)",
  "education": [
    {
      "institution": "string",
      "location": "string",
      "degree": "string",
      "dates": "string"
    }
  ],
  "experience": [
    {
      "company": "string",
      "title": "string",
      "location": "string",
      "dates": "string",
      "bullets": ["string", "string"]
    }
  ],
  "projects": [
    {
      "name": "string",
      "tech_stack": "string",
      "dates": "string",
      "bullets": ["string", "string"]
    }
  ],
  "skills": {
    "languages": "string (comma separated)",
    "frameworks": "string (comma separated)",
    "tools": "string (comma separated)",
    "databases": "string (comma separated)"
  }
}"""

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def call_llm(raw_user_data: str) -> dict:
    """Sends raw user input to Groq, gets back structured JSON."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Here is my resume information. Clean it up and return the JSON:\n\n{raw_user_data}"}
            ],
            temperature=0.3,  # lower = more consistent JSON output
            max_tokens=2000,
        )

        print("=== GROQ RESPONSE ===")
        raw_response = response.choices[0].message.content
        print(raw_response)
        print("=== END RESPONSE ===")

        if raw_response.startswith("```"):
            raw_response = raw_response.split("```")[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]

        parsed = json.loads(raw_response.strip())
        print("=== JSON PARSED OK ===")
        return parsed

    except Exception as e:
        print(f"=== ERROR IN call_llm: {type(e).__name__}: {e} ===")
        raise


# everything below stays exactly the same as before
def build_template_context(data: dict) -> dict:
    def esc(text: str) -> str:
        return escape_latex(str(text))

    return {
        "name":         esc(data["name"]),
        "phone":        esc(data["phone"]),
        "email":        esc(data["email"]),
        "email_raw":    data["email"],
        "linkedin":     esc(data["linkedin"]),
        "linkedin_raw": data["linkedin_url"],
        "github":       esc(data["github"]),
        "github_raw":   data["github_url"],

        "education": [
            {
                "institution": esc(edu["institution"]),
                "location":    esc(edu["location"]),
                "degree":      esc(edu["degree"]),
                "dates":       esc(edu["dates"]),
            }
            for edu in data.get("education", [])
        ],

        "experience": [
            {
                "company":  esc(job["company"]),
                "title":    esc(job["title"]),
                "location": esc(job["location"]),
                "dates":    esc(job["dates"]),
                "bullets":  [esc(b) for b in job.get("bullets", [])],
            }
            for job in data.get("experience", [])
        ],

        "projects": [
            {
                "name":       esc(proj["name"]),
                "tech_stack": esc(proj["tech_stack"]),
                "dates":      esc(proj["dates"]),
                "bullets":    [esc(b) for b in proj.get("bullets", [])],
            }
            for proj in data.get("projects", [])
        ],

        "skills": {
            "languages":  esc(data["skills"]["languages"]),
            "frameworks": esc(data["skills"]["frameworks"]),
            "tools":      esc(data["skills"]["tools"]),
            "databases":  esc(data["skills"]["databases"]),
        }
    }


def generate_resume(raw_user_data: str) -> bytes:
    structured_data = call_llm(raw_user_data)
    context = build_template_context(structured_data)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(
        loader=FileSystemLoader(template_dir),
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
    )
    template = env.get_template("jakes_resume.tex")
    rendered_tex = template.render(**context)

    return compile_latex_to_pdf(rendered_tex)