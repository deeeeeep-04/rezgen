import subprocess
import tempfile 
import os 
import shutil

def escape_latex(text : str) -> str : 
    '''escapes special latexx chartacters in a string must be called on every user provided 
    string before injecting into the .tex template'''

    if not text:
        return ''
    
    text = text.replace("\\", r"\textbackslash{}")
    text = text.replace("&",  r"\&")
    text = text.replace("%",  r"\%")
    text = text.replace("#",  r"\#")
    text = text.replace("_",  r"\_")
    text = text.replace("$",  r"\$")
    text = text.replace("{",  r"\{")
    text = text.replace("}",  r"\}")
    text = text.replace("~",  r"\textasciitilde{}")
    text = text.replace("^",  r"\^{}")
    text = text.replace("<",  r"\textless{}")
    text = text.replace(">",  r"\textgreater{}")
    
    return text

def compile_latex_to_pdf(tex_content: str) -> bytes:
    tmpdir = tempfile.mkdtemp()

    try:
        tex_path = os.path.join(tmpdir, "resume.tex")
        pdf_path = os.path.join(tmpdir, "resume.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        for _ in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_path],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )

        # print everything so we can see what went wrong
        print("=== PDFLATEX STDOUT ===")
        print(result.stdout)
        print("=== PDFLATEX STDERR ===")
        print(result.stderr)
        print("=== END ===")

        if not os.path.exists(pdf_path):
            raise RuntimeError(
                f"LaTeX compilation failed.\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            )

        with open(pdf_path, "rb") as f:
            return f.read()

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)