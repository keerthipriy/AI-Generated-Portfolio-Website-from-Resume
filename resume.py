import streamlit as st
from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
import os
import zipfile
from io import BytesIO
from PyPDF2 import PdfReader
import docx2txt
import streamlit.components.v1 as components
import re

# -------------------- Setup --------------------
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="AI Portfolio Generator", page_icon="💼", layout="wide")
st.title("AI-Powered Portfolio Website Builder 🚀")

# -------------------- Helper Functions --------------------
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file):
    return docx2txt.process(file)

def generate_website_code(resume_text):
    """Use Gemini LLM to generate HTML, CSS, JS code"""
    # LLM #1: Extract structured info
    prompt_structure = f"""
    Extract the following details from this resume:
    - Name
    - Skills
    - Experience
    - Projects
    - Achievements
    - Education
    - Design Style preference
    Resume:
    {resume_text}
    """
    model = GoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.7)
    structured_info = model.invoke([{"role": "user", "content": prompt_structure}])

    # LLM #2: Generate website code
    prompt_website = f"""
    Using this structured info, generate a full professional portfolio website.
    The output should be strictly in this format:

    --html--
    [html code]
    --html--

    --css--
    [css code]
    --css--

    --js--
    [js code]
    --js--

    Structured info: {structured_info}
    """
    website_code = model.invoke([{"role": "user", "content": prompt_website}])
    
    # Extract individual code blocks
    def extract_code_block(text, block):
        pattern = rf"--{block}--\s*(.*?)\s*--{block}--"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    html_code = extract_code_block(website_code, "html")
    css_code = extract_code_block(website_code, "css")
    js_code = extract_code_block(website_code, "js")

    return {"html": html_code, "css": css_code, "js": js_code}

def create_zip(code_dict):
    """Create in-memory ZIP file with HTML/CSS/JS"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("index.html", code_dict["html"])
        zf.writestr("style.css", code_dict["css"])
        zf.writestr("script.js", code_dict["js"])
    zip_buffer.seek(0)
    return zip_buffer

# -------------------- Upload Resume --------------------
st.subheader("Step 1: Upload Your Resume 📄")
uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = extract_text_from_docx(uploaded_file)

    st.success("Resume uploaded successfully! ✅")

    # -------------------- Generate Website --------------------
    if st.button("Generate Portfolio Website"):
        st.info("Generating website code... This may take a few seconds.")
        website_code = generate_website_code(resume_text)

        # -------------------- Preview Website --------------------
        st.subheader("Website Preview 👀")
        components.html(website_code["html"], height=600)

        # -------------------- Download ZIP --------------------
        zip_file = create_zip(website_code)
        st.download_button(
            label="Download Portfolio ZIP",
            data=zip_file,
            file_name="portfolio_website.zip",
            mime="application/zip"
        )
        st.success("Portfolio website generated successfully! 🎉")
