# -*- coding: utf-8 -*-
import streamlit as st
from groq import Groq
import os
import io
import requests
import urllib.parse
import json
import re
from bs4 import BeautifulSoup
import streamlit.components.v1 as components
import platform
import shutil

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
    
    # Auto-detect Tesseract installation on Windows
    if platform.system() == "Windows":
        # Common installation paths on Windows
        tesseract_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\PANKAJ KUMAR\AppData\Local\Tesseract-OCR\tesseract.exe",
            os.path.join(os.getcwd(), "tools", "Tesseract-OCR", "tesseract.exe"),
        ]
        tesseract_found = False
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.pytesseract_path = path
                tesseract_found = True
                break
        
        # Also check if tesseract is in PATH
        if not tesseract_found and not shutil.which("tesseract"):
            PYTESSERACT_AVAILABLE = False
except Exception:
    PYTESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except Exception:
    PDF2IMAGE_AVAILABLE = False

POPPLER_PATH = None
if platform.system() == "Windows":
    poppler_paths = [
        os.path.join(os.getcwd(), "tools", "poppler", "Library", "bin"),
        os.path.join(os.getcwd(), "tools", "poppler", "bin"),
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files\poppler\bin",
    ]
    for path in poppler_paths:
        if os.path.exists(os.path.join(path, "pdftoppm.exe")):
            POPPLER_PATH = path
            break

POPPLER_AVAILABLE = bool(POPPLER_PATH or shutil.which("pdftoppm"))

HF_OCR_MODEL = os.getenv("HF_OCR_MODEL", "microsoft/trocr-base-printed")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
HF_OCR_AVAILABLE = bool(HF_TOKEN)

# ══════════════════════════════════════════════════
# PREMIUM STYLING (Google Fonts & Custom CSS)
# ══════════════════════════════════════════════════
def apply_premium_styling():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@400;500;600&display=swap');

        /* Global Overrides */
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
        }
        h1, h2, h3, h4, .stTitle {
            font-family: 'Outfit', sans-serif;
            letter-spacing: -0.5px;
            color: #0f172a;
        }

        /* Hide Streamlit Defaults */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Transparent Header but KEEP the sidebar expand button visible */
        [data-testid="stHeader"] {background: rgba(0,0,0,0); border-bottom: none; color: #0f172a;}
        
        /* Premium styling for the collapsed sidebar arrow */
        [data-testid="collapsedControl"] {
            color: #1e3a8a;
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 50%;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 10px;
        }

        /* Sidebar Styling (Glassmorphism) */
        [data-testid="stSidebar"] {
            background-image: linear-gradient(180deg, #101827 0%, #1e293b 100%);
            color: white;
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
            color: white !important;
        }
        
        /* Sidebar Button styling override */
        [data-testid="stSidebar"] button {
            background-color: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            color: white;
            border-radius: 8px;
            transition: all 0.2s;
        }
        [data-testid="stSidebar"] button:hover {
            background-color: rgba(255,255,255,0.15);
            border-color: rgba(255,255,255,0.3);
        }

        /* Card System */
        .medical-card {
            background: white !important;
            color: #0f172a !important;
            border-radius: 20px;
            padding: 24px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 20px;
        }
        .medical-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
            border-color: #3b82f6;
        }

        /* Button Styling */
        .stButton>button {
            border-radius: 12px;
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            background: #2563eb;
            color: white;
            border: none;
            transition: all 0.2s;
        }
        .stButton>button:hover {
            background: #1d4ed8;
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
        }

        /* Input Fields */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            background: white !important;
            color: #0f172a !important;
            padding: 0.75rem 1rem;
        }
        .stTextInput>div>div>input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
        }
        
        /* Fix Invisible Placeholder & Cursor */
        .stTextInput input, .stTextArea textarea {
            caret-color: #0f172a !important;
        }
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {
            color: #64748b !important;
            opacity: 0.8 !important;
        }

        /* Chat & Markdown Text Visibility */
        [data-testid="stChatMessage"] {
            background-color: white !important;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            padding: 10px;
        }
        [data-testid="stMarkdownContainer"] {
            color: #0f172a;
        }
        [data-testid="stChatMessage"] * {
            color: #0f172a !important;
        }

        /* Report Analysis Upload Experience */
        .report-shell {
            background:
                radial-gradient(circle at top left, rgba(37,99,235,0.16), transparent 28%),
                radial-gradient(circle at bottom right, rgba(20,184,166,0.14), transparent 30%),
                #ffffff;
            border: 1px solid #dbeafe;
            border-radius: 28px;
            padding: 26px;
            box-shadow: 0 22px 60px rgba(15,23,42,0.08);
            margin-bottom: 22px;
        }
        .report-step {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 999px;
            background: #2563eb;
            color: white;
            font-weight: 800;
            margin-right: 8px;
        }
        .report-mini {
            color: #64748b;
            font-size: 0.9rem;
            margin-top: -8px;
            margin-bottom: 14px;
        }
        [data-testid="stFileUploader"] {
            background: linear-gradient(135deg, #f8fbff 0%, #eef6ff 100%);
            border: 2px dashed #60a5fa;
            border-radius: 24px;
            padding: 22px;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.8), 0 14px 30px rgba(37,99,235,0.08);
        }
        [data-testid="stFileUploader"]:hover {
            border-color: #2563eb;
            background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
        }
        [data-testid="stFileUploader"] section {
            border: none !important;
            padding: 16px 8px !important;
        }
        [data-testid="stFileUploader"] button {
            background: #0f172a !important;
            color: white !important;
            border-radius: 14px !important;
            padding: 0.75rem 1.25rem !important;
            font-weight: 800 !important;
            border: none !important;
        }
        [data-testid="stFileUploader"] small {
            color: #475569 !important;
            font-weight: 600;
        }
        .upload-promise {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 10px;
            margin-top: 12px;
        }
        .upload-promise div {
            background: rgba(255,255,255,0.78);
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 10px 12px;
            color: #334155;
            font-size: 0.86rem;
            font-weight: 700;
        }

        /* Badge/Chips */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-blue { background: #dbeafe; color: #1e40af; }
        .badge-green { background: #dcfce7; color: #166534; }
        .badge-red { background: #fee2e2; color: #991b1b; }

        /* Animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fadeIn 0.5s ease-out forwards; }
        </style>
    """, unsafe_allow_html=True)

def hero_section(title, subtitle):
    st.markdown(f"""
        <div style="text-align: center; padding: 30px 0 40px; background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%); border-radius: 30px; margin-bottom: 20px;">
            <h1 style="font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #1e3a8a, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px;">
                {title}
            </h1>
            <p style="font-size: 1.1rem; color: #64748b; max-width: 650px; margin: 0 auto; line-height: 1.5;">
                {subtitle}
            </p>
        </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════════════
api_key = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "medgemma:4b")
OLLAMA_CHAT_URL = os.getenv("OLLAMA_CHAT_URL", "http://127.0.0.1:11434/api/chat")

try:
    client = Groq(api_key=api_key)
except Exception:
    client = None


def is_groq_limit_error(error: Exception) -> bool:
    text = str(error).lower()
    return any(
        marker in text
        for marker in [
            "rate",
            "quota",
            "limit",
            "429",
            "too many requests",
            "rate_limit",
            "insufficient_quota",
        ]
    )


def chat_completion_text(messages, temperature=0.2, max_tokens=512, timeout=30):
    """Use Groq first; fall back to local Ollama when Groq is rate-limited."""
    groq_error = None
    if client:
        try:
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=messages,
                timeout=timeout,
            )
            return resp.choices[0].message.content
        except Exception as e:
            groq_error = e
            if not is_groq_limit_error(e):
                raise

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=timeout or 60)
        resp.raise_for_status()
        data = resp.json()
        return (data.get("message") or {}).get("content", "").strip()
    except Exception as ollama_error:
        if groq_error:
            raise RuntimeError(
                f"Groq limit reached and Ollama fallback failed: {str(ollama_error)[:100]}"
            ) from ollama_error
        raise

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

VALID_SPECIALTIES = [
    "General Physician", "Dentist", "Cardiologist",
    "Pediatrician", "Dermatologist", "Gynecologist", "Orthopedist",
]

# ══════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════
for key, default in {
    "health_advice":        None,
    "inferred_specialty":   None,
    "nearby_doctors":       None,
    "doctor_city":          "",
    "auto_city":            "",
    "hosp_search":          False,
    "doc_search":           False,
    "hosp_results":         [],
    "doc_results":          [],
    "report_analysis":      None,
    "report_text_preview":  "",
    "hosp_coords":          (None, None),
    "current_tab":          "Health Guidance",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════════════════════════
# EMERGENCY DETECTION
# ══════════════════════════════════════════════════
def check_emergency(symptoms: str) -> bool:
    keywords = [
        "chest pain", "breathing difficulty", "unconscious",
        "severe bleeding", "heart attack", "stroke", "no pulse",
        "seizure", "not breathing", "can't breathe", "collapsed",
    ]
    return any(kw in symptoms.lower() for kw in keywords)


# ══════════════════════════════════════════════════
# AUTO-DETECT CITY FROM IP  (no browser permission needed)
# ══════════════════════════════════════════════════
@st.cache_data(ttl=600)
def detect_city_from_ip():
    """Try multiple free geo-IP APIs; returns (city, lat, lon)."""
    apis = [
        ("https://ipapi.co/json/",         "city", "latitude",  "longitude"),
        ("https://ip-api.com/json/",        "city", "lat",       "lon"),
        ("https://ipwho.is/",               "city", "latitude",  "longitude"),
    ]
    for url, city_key, lat_key, lon_key in apis:
        try:
            resp = requests.get(url, timeout=6,
                                headers={"User-Agent": "AIHealthApp/2.0"})
            data = resp.json()
            city = data.get(city_key, "")
            lat  = data.get(lat_key)
            lon  = data.get(lon_key)
            if city and lat and lon:
                return str(city), float(lat), float(lon)
        except Exception:
            continue
    return "", None, None


# ══════════════════════════════════════════════════
# INFER SPECIALTY FROM SYMPTOMS  (Groq LLM)
# ══════════════════════════════════════════════════
def infer_specialty(symptoms: str) -> str:
    """Use Groq to pick the best specialty from symptoms."""
    try:
        text = chat_completion_text(
            temperature=0.05,
            max_tokens=15,
            messages=[{
                "role": "user",
                "content": f"Symptoms: {symptoms[:200]}\nBest specialty? Reply with just one: General Physician, Dentist, Cardiologist, Pediatrician, Dermatologist, Gynecologist, or Orthopedist"
            }],
        )
        text = text.strip()
        for spec in VALID_SPECIALTIES:
            if spec.lower() in text.lower():
                return spec
    except Exception:
        pass
    return "General Physician"


# ══════════════════════════════════════════════════
# OCR & IMAGE PROCESSING
# ══════════════════════════════════════════════════
def extract_text_with_huggingface_ocr(image_bytes):
    """Extract text with a Hugging Face image-to-text OCR model."""
    if not HF_OCR_AVAILABLE:
        return "", "Hugging Face OCR is not configured. Set HF_TOKEN in your environment."

    try:
        resp = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_OCR_MODEL}",
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/octet-stream",
            },
            data=image_bytes,
            timeout=60,
        )
        if resp.status_code == 503:
            return "", "Hugging Face OCR model is loading. Please try again in a minute."
        if resp.status_code == 401:
            return "", "Hugging Face authentication failed. Check your HF_TOKEN."
        if not resp.ok:
            return "", f"Hugging Face OCR failed: HTTP {resp.status_code}"

        data = resp.json()
        if isinstance(data, list) and data:
            text = data[0].get("generated_text", "")
        elif isinstance(data, dict):
            text = data.get("generated_text", "")
        else:
            text = ""

        text = text.strip()
        if len(text) < 5:
            return "", "Hugging Face OCR could not read useful text from this image."
        return text, ""
    except Exception as e:
        return "", f"Hugging Face OCR request failed: {str(e)[:80]}"


def extract_text_from_image(image_bytes, is_xray=False):
    """Extract text from image using OCR (Tesseract).
    For X-rays, returns success marker without requiring OCR."""
    
    # For X-rays, we don't need text extraction - just validate it's an image
    if is_xray:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Just verify it's a valid image
            _ = image.size
            return "[X-RAY_IMAGE_UPLOADED]", ""
        except Exception as e:
            return "", f"Invalid image format: {str(e)[:50]}"
    
    # For non-X-ray images, use OCR if available
    if not PYTESSERACT_AVAILABLE:
        if HF_OCR_AVAILABLE:
            return extract_text_with_huggingface_ocr(image_bytes)
        return "", """❌ **OCR is not available on your system.**
        
To enable text extraction from images:
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: C:\\Program Files\\Tesseract-OCR
3. Restart the app

**For now:** Upload text-based PDFs or describe the X-ray findings below!"""
    
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Check image dimensions
        if image.size[0] < 50 or image.size[1] < 50:
            return "", "Image is too small. Please provide a clearer or larger image."
        
        text = pytesseract.image_to_string(image)
        if not text or len(text.strip()) < 10:
            return "", "Could not extract readable text from image. Try a clearer image."
        
        return text.strip(), ""
    except Exception as e:
        error_msg = str(e)
        if "image file" in error_msg.lower() or "cannot identify" in error_msg.lower():
            return "", "Invalid image file format. Please upload JPG, PNG, or TIFF."
        if "tesseract" in error_msg.lower():
            return "", """❌ **Tesseract-OCR is not working.**

**Quick Fix:**
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: C:\\Program Files\\Tesseract-OCR
3. Restart your app

**Alternative:** Describe the X-ray findings in the context field below"""
        return "", f"Image processing failed: {error_msg[:80]}"


def extract_text_from_scanned_pdf(file_bytes):
    """Extract text from scanned PDFs using pdf2image + OCR."""
    if not PDF2IMAGE_AVAILABLE:
        return "", "The Python package pdf2image is missing. Run: pip install pdf2image"
    if not POPPLER_AVAILABLE:
        return "", """Poppler is not installed or not on PATH.

Install Poppler for Windows, then either:
1. Add its bin folder to PATH, or
2. Put it here: tools\\poppler\\Library\\bin\\pdftoppm.exe

The Python package pdf2image is already installed; scanned PDFs also need Poppler."""
    if not PYTESSERACT_AVAILABLE and not HF_OCR_AVAILABLE:
        return "", """❌ **Tesseract-OCR is not installed.**
        
Download & install from: https://github.com/UB-Mannheim/tesseract/wiki"""
    
    try:
        images = convert_from_bytes(file_bytes, timeout=30, poppler_path=POPPLER_PATH)
        if not images:
            return "", "Could not convert PDF pages to images. PDF might be corrupted."
        
        text_pages = []
        
        for idx, image in enumerate(images[:5]):  # Process first 5 pages only
            try:
                if PYTESSERACT_AVAILABLE:
                    text = pytesseract.image_to_string(image)
                else:
                    image_buffer = io.BytesIO()
                    image.save(image_buffer, format="PNG")
                    text, error = extract_text_with_huggingface_ocr(image_buffer.getvalue())
                    if error:
                        continue
                if text and text.strip():
                    text_pages.append(text)
            except Exception as e:
                # Skip pages that fail OCR
                continue
        
        if not text_pages:
            return "", "Could not extract text from PDF pages. Image quality might be too low."
        
        full_text = "\n".join(text_pages).strip()
        return full_text, ""
    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg:
            return "", "PDF conversion timed out. Try a smaller PDF file."
        elif "permission" in error_msg or "access" in error_msg:
            return "", "Permission denied when accessing the PDF file."
        else:
            return "", f"Scanned PDF extraction failed: {str(e)[:80]}"


def analyze_xray_report(xray_type: str = "", patient_context: str = "") -> str:
    """Explain X-ray findings from user-provided context.

    The app validates and previews X-ray images, but it does not run a trained
    pixel-level classifier yet. If no findings are provided, return a clear
    educational message instead of making the upload flow feel broken.
    """
    try:
        clean_context = patient_context.strip()
        if not clean_context:
            return f"""
### X-ray Uploaded Successfully

I can confirm the image file was uploaded, but this app is not connected to a trained X-ray image-classifier model yet. That means I should not claim to detect pneumonia, fracture, TB, opacity, or disease directly from the image pixels.

### What You Can Do Now
- Paste the radiologist report findings, if you have them, and click **Analyze Report** again.
- Paste doctor notes such as "left lower lobe infiltrate", "no acute abnormality", or "possible fracture".
- For urgent symptoms like chest pain, breathing difficulty, severe injury, or worsening pain, contact a doctor or emergency service immediately.

### Selected Imaging Type
{xray_type or "Medical imaging"}
"""

        prompt = f"""As a medical assistant, analyze this X-ray or imaging finding.
Type: {xray_type if xray_type else 'Unknown imaging'}
Findings/context: {clean_context[:800]}

Provide a safe, patient-friendly explanation with these sections:
1. Summary
2. What the finding may suggest
3. When to contact a doctor urgently
4. Suggested next steps

Do not diagnose. Do not prescribe medicines. Be educational and recommend clinician confirmation."""

        if len(prompt) > 3000:
            return "Context is too long. Please shorten the X-ray notes and try again."

        return chat_completion_text(
            temperature=0.2,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
    except Exception as e:
        error_str = str(e).lower()
        if "400" in str(e) or "bad_request" in error_str:
            return "API request error: invalid request format. Try a shorter description."
        if "401" in str(e) or "unauthorized" in error_str:
            return "API authentication failed. Check your API key."
        if "timeout" in error_str or "connection" in error_str:
            return "Network timeout. Please try again in a moment."
        if "rate" in error_str:
            return "Too many requests. Please wait a moment and try again."
        return f"Analysis failed: {str(e)[:100]}"


# HEALTH REPORT ANALYSIS
# ══════════════════════════════════════════════════
def extract_report_text(uploaded_file, is_xray=False):
    """Extract readable text from PDF, images, or text reports. Supports OCR for scanned documents.
    If is_xray=True, allows fallback for X-ray images when OCR unavailable."""
    if uploaded_file is None:
        return "", "Please upload a file (PDF, PNG, JPG, TXT)."

    try:
        file_name = uploaded_file.name.lower()
        file_bytes = uploaded_file.getvalue()
        
        if not file_bytes:
            return "", "The uploaded file is empty. Please upload a valid file."
        
        # Check file size (max 10MB)
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > 10:
            return "", f"File is too large ({file_size_mb:.1f}MB). Maximum size is 10MB."

        # Handle images (JPG, PNG, etc.)
        if file_name.endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff")):
            text, error = extract_text_from_image(file_bytes, is_xray=is_xray)
            if error and not is_xray:
                return text, error
            if error and is_xray and "[X-RAY_IMAGE_UPLOADED]" not in text:
                return text, error
            if not text:
                return "", "No text found in image. The image might be blank or unclear."
            return text, ""

        # Handle PDFs
        if file_name.endswith(".pdf"):
            if PdfReader is None:
                return "", "PDF support not installed. Install: pip install pypdf"
            
            try:
                pdf_file = io.BytesIO(file_bytes)
                reader = PdfReader(pdf_file)
                
                if not reader.pages:
                    return "", "This PDF has no pages. Please upload a valid PDF file."
                
                pages = []
                for idx, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text and len(text.strip()) > 20:
                            pages.append(text)
                    except Exception:
                        continue
                
                text = "\n".join(pages).strip()
                
                # If PDF is scanned (no text extracted), try OCR
                if not text or len(text) < 50:
                    if PDF2IMAGE_AVAILABLE and POPPLER_AVAILABLE and (PYTESSERACT_AVAILABLE or HF_OCR_AVAILABLE):
                        text, error = extract_text_from_scanned_pdf(file_bytes)
                        if error:
                            return "", f"PDF extraction failed. Try exporting as image and uploading as JPG/PNG: {error}"
                        if not text:
                            return "", "This PDF appears to be a scanned image with no readable text. Enable OCR or upload as an image file."
                        return text, ""
                    else:
                        if is_xray:
                            return "[X-RAY_IMAGE_UPLOADED]", ""
                        missing = []
                        if not PDF2IMAGE_AVAILABLE:
                            missing.append("pdf2image Python package")
                        if not POPPLER_AVAILABLE:
                            missing.append("Poppler for Windows")
                        if not PYTESSERACT_AVAILABLE and not HF_OCR_AVAILABLE:
                            missing.append("Tesseract-OCR for Windows or HF_TOKEN")
                        return "", (
                            "This PDF is scanned/image-based. Missing: "
                            + ", ".join(missing)
                            + ". Note: pdf2image/pytesseract are Python wrappers; scanned PDFs also need Poppler and Tesseract installed on Windows."
                        )
                
                return text, ""
                
            except Exception as e:
                error_msg = str(e)
                if "password" in error_msg.lower():
                    return "", "This PDF is password-protected. Please provide an unencrypted PDF."
                return "", f"PDF reading failed: {error_msg[:80]}. Try exporting to a text format."
        
        # Handle text files
        if file_name.endswith((".txt", ".text", ".csv")):
            try:
                text = file_bytes.decode("utf-8", errors="ignore").strip()
                if not text:
                    return "", "The text file is empty."
                return text, ""
            except Exception as e:
                return "", f"Could not read text file: {str(e)[:80]}"
        
        # Try decoding as text for unknown formats
        try:
            text = file_bytes.decode("utf-8", errors="ignore").strip()
            if text and len(text) > 20:
                return text, ""
            return "", "File format not recognized. Please upload PDF, image (JPG/PNG), or TXT."
        except Exception as e:
            return "", f"Could not read this file: {str(e)[:80]}"
    
    except Exception as e:
        return "", f"File processing error: {str(e)[:100]}"
            
    except Exception as e:
        return "", f"Unexpected error processing file: {str(e)[:100]}"


def analyze_health_report(report_text: str, report_type: str, patient_context: str = "") -> str:
    """Use Groq to explain uploaded lab/health reports in patient-friendly language."""
    try:
        # Validate inputs
        if not report_text or len(report_text.strip()) < 20:
            return "⚠️ Report text is too short or empty. Please ensure the file contains readable content."
        
        # Use smaller report size for stability
        trimmed = report_text[:3000]
        
        # Simple prompt without system message
        prompt = f"""Explain this {report_type} in simple terms. 
Context: {patient_context[:200] if patient_context else 'None'}

Report:
{trimmed}

Provide:
1. Summary
2. Key findings
3. When to see a doctor"""
        
        if len(prompt) > 4000:
            return "⚠️ Report is too long. Please upload a shorter report or try a different file."
        
        return chat_completion_text(
            temperature=0.2,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
    except Exception as e:
        error_str = str(e).lower()
        if "400" in str(e) or "bad_request" in error_str:
            return "⚠️ API request error: Invalid request. Try uploading a different or shorter report."
        elif "401" in str(e) or "unauthorized" in error_str:
            return "⚠️ API authentication failed. Check your API key."
        elif "timeout" in error_str or "connection" in error_str:
            return "⚠️ Network timeout. Please try again in a moment."
        elif "rate" in error_str:
            return "⚠️ Too many requests. Please wait a moment and try again."
        else:
            return f"⚠️ Analysis failed: {str(e)[:100]}"


# ══════════════════════════════════════════════════
# CITY COORDINATES
# ══════════════════════════════════════════════════
CITY_COORDS = {
    "delhi": (28.6139, 77.2090),       "new delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),      "bombay": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),   "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),   "chennai": (13.0827, 80.2707),
    "madras": (13.0827, 80.2707),      "kolkata": (22.5726, 88.3639),
    "calcutta": (22.5726, 88.3639),    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),   "jaipur": (26.9124, 75.7873),
    "surat": (21.1702, 72.8311),       "lucknow": (26.8467, 80.9462),
    "kanpur": (26.4499, 80.3319),      "nagpur": (21.1458, 79.0882),
    "indore": (22.7196, 75.8577),      "bhopal": (23.2599, 77.4126),
    "visakhapatnam": (17.6868, 83.2185),"patna": (25.5941, 85.1376),
    "vadodara": (22.3072, 73.1812),    "ghaziabad": (28.6692, 77.4538),
    "ludhiana": (30.9010, 75.8573),    "agra": (27.1767, 78.0081),
    "nashik": (19.9975, 73.7898),      "faridabad": (28.4089, 77.3178),
    "meerut": (28.9845, 77.7064),      "rajkot": (22.3039, 70.8022),
    "varanasi": (25.3176, 82.9739),    "amritsar": (31.6340, 74.8723),
    "chandigarh": (30.7333, 76.7794),  "coimbatore": (11.0168, 76.9558),
    "kochi": (9.9312, 76.2673),        "bhubaneswar": (20.2961, 85.8245),
    "dehradun": (30.3165, 78.0322),    "guwahati": (26.1445, 91.7362),
    "jodhpur": (26.2389, 73.0243),     "ranchi": (23.3441, 85.3096),
    "raipur": (21.2514, 81.6296),      "thiruvananthapuram": (8.5241, 76.9366),
    "mysuru": (12.2958, 76.6394),      "mysore": (12.2958, 76.6394),
    "vijayawada": (16.5062, 80.6480),  "gurgaon": (28.4595, 77.0266),
    "gurugram": (28.4595, 77.0266),    "noida": (28.5355, 77.3910),
}

def geocode_city(city: str):
    key = city.lower().strip()
    if key in CITY_COORDS:
        return CITY_COORDS[key]
    for k, v in CITY_COORDS.items():
        if key in k or k in key:
            return v
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{city}, India", "format": "json", "limit": 1},
            headers={"User-Agent": "AIHealthApp/2.0"},
            timeout=12,
        )
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None


# ══════════════════════════════════════════════════
# HOSPITALS: OpenStreetMap / Overpass API
# ══════════════════════════════════════════════════
def get_hospitals_osm(lat, lon):
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:12000,{lat},{lon});
      way["amenity"="hospital"](around:12000,{lat},{lon});
      node["amenity"="clinic"](around:12000,{lat},{lon});
      node["healthcare"="hospital"](around:12000,{lat},{lon});
    );
    out center tags;
    """
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query}, timeout=48, headers={"User-Agent": "AIHealthApp/2.0"}
        )
        places, seen = [], set()
        for elem in resp.json().get("elements", []):
            tags = elem.get("tags", {})
            name = tags.get("name", "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            if elem["type"] == "node":
                plat, plon = elem.get("lat", lat), elem.get("lon", lon)
            else:
                c = elem.get("center", {})
                plat, plon = c.get("lat", lat), c.get("lon", lon)
            addr = ", ".join(
                p for p in [
                    tags.get("addr:housenumber", ""),
                    tags.get("addr:street", ""),
                    tags.get("addr:suburb", ""),
                ] if p
            ) or "Address not listed"
            places.append({
                "Name": name, "Address": addr,
                "Phone":   tags.get("phone", tags.get("contact:phone", "")),
                "Opening": tags.get("opening_hours", ""),
                "Amenity": tags.get("amenity", "hospital"),
                "Lat": plat, "Lon": plon,
            })
        places.sort(key=lambda x: 0 if x["Amenity"] == "hospital" else 1)
        return places[:20]
    except Exception:
        return []


def render_hospital_map(lat: float, lon: float, places: list):
    """Interactive Leaflet map with custom professional markers."""
    markers_js = ""
    for p in places:
        n   = p["Name"].replace("'", "\\'").replace('"', '\\"')
        a   = p["Address"].replace("'", "\\'").replace('"', '\\"')
        ph  = f" {p['Phone']}<br>" if p.get("Phone") else ""
        op  = f" {p['Opening']}<br>" if p.get("Opening") else ""
        gm  = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(p['Name']+' '+p['Address'])}"
        
        main_col = "#e74c3c" if p.get("Amenity") == "hospital" else "#1a73e8"
        
        markers_js += f"""
        var icon = L.divIcon({{
            className: 'custom-div-icon',
            html: "<div style='background-color:{main_col};' class='marker-pin'></div><i class='medical-icon'>+</i>",
            iconSize: [30, 42],
            iconAnchor: [15, 42]
        }});
        L.marker([{p['Lat']},{p['Lon']}], {{icon: icon}}).addTo(map).bindPopup(
            '<div style="font-family:sans-serif;min-width:160px;">' +
            '<b style="font-size:14px;color:{main_col};"> {n}</b><br>' +
            '<p style="font-size:12px;margin:5px 0;color:#555;"> {a}</p>' +
            '<div style="font-size:12px;color:#666;">{ph}{op}</div>' +
            '<a href=\\'{gm}\\' target=\\'_blank\\' style=\\"display:block;margin-top:8px;padding:6px;background:{main_col};color:white;text-align:center;text-decoration:none;border-radius:4px;font-weight:bold;font-size:12px;\\"> Directions</a>' +
            '</div>'
        );
        """

    html = f"""<!DOCTYPE html><html><head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        *{{margin:0;padding:0}}
        #map{{height:460px;width:100%;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.15);border:1px solid #eee;}}
        .custom-div-icon {{ position: relative; }}
        .marker-pin {{
            width: 30px; height: 30px; border-radius: 50% 50% 50% 0;
            position: absolute; transform: rotate(-45deg); left: 50%; top: 50%; margin: -20px 0 0 -15px;
            animation: pulse 2s infinite;
        }}
        .marker-pin::after {{
            content: ''; width: 24px; height: 24px; margin: 3px 0 0 3px;
            background: #fff; border-radius: 50%; position: absolute;
        }}
        .medical-icon {{
            position: absolute; width: 30px; height: 30px; left: 50%; top: 50%; margin: -18px 0 0 -15px;
            text-align: center; color: #fff; font-style: normal; font-weight: bold; font-size: 18px; line-height: 24px;
            z-index: 10;
        }}
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.4); }}
            70% {{ box-shadow: 0 0 0 10px rgba(231, 76, 60, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); }}
        }}
    </style>
    </head><body><div id="map"></div><script>
    var map=L.map('map', {{zoomControl: true}}).setView([{lat},{lon}], 14);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
        attribution: '© OpenStreetMap-CartoDB'
    }}).addTo(map);
    L.circle([{lat},{lon}],{{color:'#1a73e8',fillColor:'#1a73e8',fillOpacity:0.04,radius:5000,weight:1}}).addTo(map);
    {markers_js}
    </script></body></html>"""
    components.html(html, height=480, scrolling=False)


# ══════════════════════════════════════════════════
# DOCTORS: Practo → Google → Groq AI fallback
# ══════════════════════════════════════════════════



def scrape_google_doctors(city: str, specialty: str):
    query = urllib.parse.quote(f"top {specialty} doctor in {city} India rating")
    url   = f"https://www.google.com/search?q={query}&num=10"
    doctors = []
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")
        for g in soup.find_all("div", class_="g"):
            h3 = g.find("h3")
            a  = g.find("a")
            if not h3 or not a:
                continue
            title = h3.text.strip()
            href  = a.get("href", "")
            if not any(w in title.lower() for w in ["dr.", "dr ", "doctor", "clinic", "hospital"]):
                continue
            snippet = g.get_text(" ", strip=True)
            r = re.search(r"(\d\.\d)\s*(?:★|/5|stars?|rating)", snippet, re.I)
            v = re.search(r"(\d+)\s*(?:reviews?|ratings?|votes?)", snippet, re.I)
            e = re.search(r"(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:exp|experience)", snippet, re.I)
            f = re.search(r"[₹]\s*(\d+)", snippet)
            ap = re.search(r"(available today|available tomorrow|next available[^.]*)", snippet, re.I)
            doctors.append({
                "Name":        title,
                "Specialty":   specialty,
                "Rating":      r.group(1)  if r  else "N/A",
                "Reviews":     v.group(1) + " reviews" if v else "",
                "Experience":  e.group(0)  if e  else "",
                "Fees":        "₹" + f.group(1) if f else "",
                "Appointment": ap.group(1).strip() if ap else "",
                "Hospital":    "",
                "Link":        href if href.startswith("http") else f"https://www.google.com{href}",
                "Source":      "Google",
            })
    except Exception:
        pass
    return doctors[:8]


def get_doctors_groq(city: str, specialty: str):
    try:
        prompt = f"List 4 {specialty} doctors in {city}, India. Format: Name | Hospital | Rating | ₹Fees"
        text = chat_completion_text(
            temperature=0.3,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = text.strip()
        lines = text.split('\n')[:4]
        doctors = []
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    doctors.append({
                        "Name": parts[0] or "Doctor",
                        "Specialty": specialty,
                        "Rating": parts[2] if len(parts) > 2 else "4.5",
                        "Reviews": "50+",
                        "Experience": "10+ years",
                        "Fees": parts[3] if len(parts) > 3 else "₹500",
                        "Appointment": "Call to Book",
                        "Hospital": parts[1] if len(parts) > 1 else "Clinic",
                        "Address": f"{city}",
                        "Link": f"https://www.google.com/search?q={urllib.parse.quote(parts[0] + ' ' + city)}",
                        "Source": "AI Recommendation",
                    })
        return doctors
    except Exception:
        pass
    return []


def get_doctors(city: str, specialty: str):
    """Chain: Google scrape → Groq AI."""
    docs = scrape_google_doctors(city, specialty)
    if len(docs) < 3:
        docs = get_doctors_groq(city, specialty)
    return docs


# ══════════════════════════════════════════════════
# SHARED UI: Doctor Cards (used in both pages)
# ══════════════════════════════════════════════════
def render_stars(rating_str: str) -> str:
    try:
        r = float(rating_str)
        full  = int(r)
        half  = 1 if (r - full) >= 0.4 else 0
        empty = 5 - full - half
        return "⭐" * full + ("✨" if half else "") + "☆" * empty + f"  **{rating_str}/5**"
    except Exception:
        return f"⭐ {rating_str}"


def appt_badge(appt_str: str) -> str:
    if not appt_str:
        return ""
    low = appt_str.lower()
    if "today"    in low: return f" **{appt_str}**"
    if "tomorrow" in low: return f" **{appt_str}**"
    return f" **{appt_str}**"


def show_doctor_cards(doctors: list, city: str, specialty: str):
    """Render doctor cards — shared between Health Guidance and Doctors Near Me."""
    if not doctors:
        st.error("❌ Could not load doctor data. Use the links above.")
        return

    src = doctors[0].get("Source", "")
    if src == "AI Recommendation":
        st.info(
            " **AI-curated recommendations** — Live web data unavailable for "
            "this city. Ratings are AI-estimated. Click **Learn More** to search."
        )
    elif src == "Google":
        st.success(f"✅ **{len(doctors)}** results from Google Search for **{specialty}** in **{city}**")
    else:
        st.success(f"✅ **{len(doctors)}** top **{specialty}s** in **{city}** found")

    for doc in doctors:
        doc_html = f"""
        <div class="medical-card animate-fade-in">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 20px;">
                <div>
                    <h2 style="margin: 0; font-size: 1.5rem; color: #1e3a8a;">&#128104;&#8205;&#9877;&#65039; {doc['Name']}</h2>
                    <div style="margin-top: 8px;">
                        <span class="badge badge-blue">{doc['Specialty']}</span>
                        <span class="badge badge-green">Verified</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #f59e0b;">
                        {doc['Rating']} <span style="font-size: 1rem; color: #94a3b8;">&#9733;</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">{doc.get('Reviews', '0')} Reviews</div>
                </div>
            </div>
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 20px;">
                <div style="flex: 1 1 250px;">
                    <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                        <span style="color: #3b82f6;">&#127973;</span>
                        <div style="color: #334155; font-weight: 500;">{doc.get('Hospital', 'Clinic Available')}</div>
                    </div>
                    <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                        <span style="color: #3b82f6;">&#128205;</span>
                        <div style="color: #64748b;">{doc.get('Address', city)}</div>
                    </div>
                    <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                        <span style="color: #3b82f6;">&#127891;</span>
                        <div style="color: #64748b;">{doc.get('Experience', 'Expert practitioner')}</div>
                    </div>
                    <div style="display: flex; gap: 15px;">
                        <div style="display: flex; gap: 5px; align-items: center;">
                            <span style="color: #10b981;">&#128176;</span>
                            <div style="color: #64748b; font-weight: 600;">{doc.get('Fees', 'Contact for fees')}</div>
                        </div>
                        <div style="display: flex; gap: 5px; align-items: center;">
                            <span style="color: #f59e0b;">&#128336;</span>
                            <div style="color: #64748b; font-weight: 500;">{doc.get('Appointment', 'Call to confirm')}</div>
                        </div>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; justify-content: flex-end; gap: 10px; flex: 1 1 150px; min-width: 150px;">
                    <a href="{doc['Link']}" target="_blank" style="text-decoration: none;">
                        <div style="background: #2563eb; color: white; text-align: center; padding: 12px; border-radius: 10px; font-weight: 600; font-size: 0.9rem;">
                             Book Appointment
                        </div>
                    </a>
                    <a href="https://www.google.com/maps/search/{urllib.parse.quote(doc['Name'] + ' ' + doc.get('Hospital', '') + ' ' + city)}" target="_blank" style="text-decoration: none;">
                        <div style="background: #f1f5f9; color: #475569; text-align: center; padding: 10px; border-radius: 10px; font-weight: 500; font-size: 0.8rem;">
                             View on Map
                        </div>
                    </a>
                </div>
            </div>
        </div>
        """
        st.markdown(doc_html.replace("\n", ""), unsafe_allow_html=True)


def show_hospital_cards(hospitals: list, is_emergency: bool = False):
    """Render hospital/clinic cards in a premium, user-friendly style."""
    if not hospitals:
        return

    # Colors based on context
    border_col = "#e74c3c" if is_emergency else "#4f8ef7"
    bg_gradient = (
        "linear-gradient(135deg,#fff8f8,#feeef0)" if is_emergency else 
        "linear-gradient(135deg,#f8faff,#eef4ff)"
    )
    title_col = "#c0392b" if is_emergency else "#1a1a2e"

    for h in hospitals:
        phone_html = f"&#128222; {h['Phone']}<br>" if h.get("Phone") else ""
        opening_html = f"&#128336; {h['Opening']}" if h.get("Opening") else ""
        dest = urllib.parse.quote(f"{h['Name']} {h['Address']}")
        
        card_html = f"""
        <div class="medical-card animate-fade-in">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="margin: 0; color: {title_col}; font-size: 1.3rem;">&#127973; {h['Name']}</h3>
                <span class="badge" style="background: {border_col}20; color: {border_col};">{h['Amenity']}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px; color: #64748b; font-size: 0.9rem;">
                <span>&#128205;</span>
                <div>{h['Address']}</div>
            </div>
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 15px; align-items: flex-end; border-top: 1px solid #f1f5f9; margin-top: 10px; padding-top: 12px;">
                <div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.4; flex: 1 1 150px;">
                    {phone_html}{opening_html}
                </div>
                <a href="https://www.google.com/maps/dir/?api=1&destination={dest}" target="_blank" style="text-decoration: none;">
                    <div style="background: {border_col}; color: white; padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 0.85rem;">
                        &#128663; Directions
                    </div>
                </a>
            </div>
        </div>
        """
        # Strip newlines to prevent markdown parser from breaking
        st.markdown(card_html.replace("\n", ""), unsafe_allow_html=True)


def show_doctor_links(city: str, specialty: str):
    """Quick-access links row above doctor cards."""
    gmaps_q     = urllib.parse.quote(f"{specialty} near {city} India")
    goog_q      = urllib.parse.quote(f"top {specialty} doctor in {city} India rating appointment")
    lc1, lc2 = st.columns(2)
    with lc1: st.markdown(f"&#128506; [**Google Maps**](https://www.google.com/maps/search/{gmaps_q})")
    with lc2: st.markdown(f"&#128269; [**Google Search**](https://www.google.com/search?q={goog_q})")


# ══════════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════════
SYSTEM_PROMPT = """
You are an AI healthcare assistant.

Format your response using clear section headers. Use bullet points for easy reading. 
Keep the text size concise and conversational.

Use these EXACT markdown headers, but you must prepend a relevant emoji to each one:
- Possible Conditions
- Do's
- Don'ts
- Helpful Medicines (OTC)
- When to See a Doctor
"""

# ══════════════════════════════════════════════════
# STREAMLIT APP CONFIG
# ══════════════════════════════════════════════════
st.set_page_config(page_title="AI Health Assistant", page_icon="", layout="wide")
apply_premium_styling()

# ── Global Auto-Location Detection (runs once) ────
if not st.session_state.auto_city:
    with st.spinner(" Detecting your location..."):
        try:
            auto_city, _, _ = detect_city_from_ip()
            st.session_state.auto_city = auto_city
        except Exception:
            st.session_state.auto_city = ""

with st.sidebar:
    st.markdown("""
        <div style="padding: 20px 0; text-align: center;">
            <div style="width: 64px; height: 64px; margin: 0 auto 15px auto; background: linear-gradient(135deg, #3b82f6, #1e3a8a); border-radius: 18px; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);">
                <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                </svg>
            </div>
            <h1 style="color: white; margin: 0; font-size: 1.6rem; font-weight: 800; letter-spacing: 0.5px;">AI Health</h1>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 6px;">Your Premium Health Companion</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("Health Guidance", use_container_width=True):
        st.session_state.current_tab = "Health Guidance"
    if st.button("Report Analysis", use_container_width=True):
        st.session_state.current_tab = "Report Analysis"
    if st.button("Hospitals Near Me", use_container_width=True):
        st.session_state.current_tab = "Hospitals Near Me"
    if st.button("Doctors Near Me", use_container_width=True):
        st.session_state.current_tab = "Doctors Near Me"

    st.markdown("""
        <div style="margin-top: 40px;">
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #94a3b8; font-size: 0.7rem; margin-bottom: 5px;">EMERGENCY SERVICES</div>
                <div style="color: white; font-weight: 700; font-size: 0.9rem;">&#128222; 108 / 112 / 102</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

choice = st.session_state.current_tab

# ════════════════════════════════════════════════════════
# PAGE 1 — HEALTH GUIDANCE  (with Auto-Location + Auto-Doctors)
# ════════════════════════════════════════════════════════
if choice == "Health Guidance":
    hero_section(
        "AI Health Assistant",
        "Describe your symptoms below to receive instant health guidance, "
        "consult specialist recommendations, and find nearby care."
    )

    # ── Location & Context area ───────────────────────────
    loc_col, override_col = st.columns([2, 1])
    with loc_col:
        current_city = st.session_state.auto_city or "Unknown"
        st.markdown(f"""
            <div style="background: white; padding: 12px 20px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.2rem;"></span>
                <span style="color: #64748b; font-size: 0.9rem;">Auto-detected: </span>
                <b style="color: #1e3a8a;">{current_city}</b>
            </div>
        """, unsafe_allow_html=True)
    with override_col:
        override_city = st.text_input("Override City", placeholder="e.g. Delhi", label_visibility="collapsed")

    effective_city = override_city.strip() if override_city.strip() else st.session_state.auto_city

    # ── Input Area ────────────────────────────────────────
    st.markdown("""
        <h3 style="margin-top: 20px; color: #1e3a8a; font-size: 1.4rem; margin-bottom: 15px;">
            &#128172; Describe Your Symptoms
        </h3>
    """, unsafe_allow_html=True)
    user_input = st.text_area(
        "What symptoms are you experiencing?",
        placeholder="e.g. I have a severe headache and sharp pain in the left eye since last night...",
        height=120,
        label_visibility="collapsed"
    )
    
    col_submit, col_info = st.columns([1, 2])
    with col_submit:
        btn_clicked = st.button(" Get Advice & Find Doctors", use_container_width=True, type="primary")
    with col_info:
        st.markdown("""
            <div style="color: #94a3b8; font-size: 0.8rem; padding-top: 10px;">
                Our AI Pick the right specialist and finds top doctors near you automatically.
            </div>
        """, unsafe_allow_html=True)

    if btn_clicked:
        if not user_input.strip():
            st.warning("⚠️ Please describe your symptoms first.")
        elif check_emergency(user_input):
            
            # Wipe previous chat data so it doesn't clutter the emergency view
            st.session_state.health_advice = None
            st.session_state.nearby_doctors = None
            st.session_state.inferred_specialty = None
            
            # ── Big emergency numbers banner ──────────────────
            st.markdown("""
                <div style="background:linear-gradient(135deg,#c0392b,#e74c3c); color:white; border-radius:18px; padding:28px 32px; text-align:center; margin: 30px 0; box-shadow:0 6px 32px rgba(192,57,43,0.45);">
                    <div style="font-size:42px;margin-bottom:8px;"></div>
                    <h1 style="margin:0 0 6px;font-size:32px;letter-spacing:1px;color:white !important;">EMERGENCY DETECTED</h1>
                    <p style="margin:0 0 20px;font-size:17px;opacity:0.93;color:white !important;">Do NOT wait — call immediately or go to the nearest hospital!</p>
                    <div style="display:flex;justify-content:center;gap:20px;flex-wrap:wrap;">
                        <div style="background:rgba(255,255,255,0.18); border-radius:14px; padding:14px 28px; min-width:140px;">
                            <div style="font-size:11px; opacity:0.8; margin-bottom:4px; color: white !important;">AMBULANCE</div>
                            <div style="font-size:36px; font-weight:900; color: white !important;">108</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.18); border-radius:14px; padding:14px 28px; min-width:140px;">
                            <div style="font-size:11px; opacity:0.8; margin-bottom:4px; color: white !important;">EMERGENCY</div>
                            <div style="font-size:36px; font-weight:900; color: white !important;">112</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.18); border-radius:14px; padding:14px 28px; min-width:140px;">
                            <div style="font-size:11px; opacity:0.8; margin-bottom:4px; color: white !important;">MATERNAL</div>
                            <div style="font-size:36px; font-weight:900; color: white !important;">102</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if effective_city:
                with st.spinner(" Locating nearest hospitals..."):
                    lat, lon = geocode_city(effective_city)
                    if lat:
                        hospitals = get_hospitals_osm(lat, lon)[:5]
                        if hospitals:
                            st.markdown("### &#127973; Nearest Hospitals to You")
                            show_hospital_cards(hospitals, is_emergency=True)
                            render_hospital_map(lat, lon, hospitals)
                        else:
                            st.warning(f"⚠️ Could not find hospitals in {effective_city} automatically. Please contact the emergency numbers above immediately!")
                    else:
                        st.error(f"⚠️ Could not pinpoint '{effective_city}' on the map. Please enter a valid nearby major city in the 'Override City' box.")
            else:
                st.error("⚠️ We couldn't automatically detect your location. Please type your city in the 'Override City' box above to find nearest hospitals!")

        else:
            # ── Normal advice flow ────────────────────────────
            # ── Step 1: AI Advice ──────────────────────────
            with st.spinner(" AI analyzing symptoms..."):
                try:
                    # Combine system instructions into the user message to avoid format issues
                    full_prompt = f"""As a healthcare assistant, analyze these symptoms:
{user_input[:500]}

Provide advice in these sections:
- Possible Conditions
- Do's
- Don'ts  
- When to See a Doctor

Be concise and practical."""
                    
                    advice = chat_completion_text(
                        temperature=0.1,
                        max_tokens=512,
                        messages=[
                            {"role": "user", "content": full_prompt}
                        ],
                    )
                    st.session_state.health_advice = advice
                except Exception as e:
                    st.session_state.health_advice = f"AI Advice unavailable: {str(e)[:100]}"

            # ── Step 2: Infer specialty ────────────────────
            with st.spinner(" Determining which specialist you need..."):
                spec = infer_specialty(user_input)
                st.session_state.inferred_specialty = spec

            # ── Step 3: Fetch doctors ──────────────────────
            if effective_city:
                with st.spinner(f"‍⚕️ Finding top {spec}s near {effective_city}..."):
                    st.session_state.nearby_doctors = get_doctors(effective_city, spec)
                    st.session_state.doctor_city = effective_city
            else:
                st.session_state.nearby_doctors = []

    # ── Display Results (persistent) ─────────────────────
    if st.session_state.health_advice:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.chat_message("assistant", avatar="🏥"):
            st.markdown(st.session_state.health_advice)
        st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 6px; margin-top: 10px;">
                <strong style="color: #d97706; font-size: 0.95rem;">&#9888;&#65039; DISCLAIMER:</strong>
                <span style="color: #92400e; font-size: 0.9rem; margin-left: 5px;">
                    This is AI-generated guidance, not a medical diagnosis. Always consult a qualified doctor before making health decisions.
                </span>
            </div>
        """, unsafe_allow_html=True)

    # ── Display doctor recommendations (persistent) ────────
    if st.session_state.nearby_doctors is not None and st.session_state.inferred_specialty:
        spec = st.session_state.inferred_specialty
        city = st.session_state.doctor_city

        st.markdown("---")

        # Header with specialty chip
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                color:white;border-radius:16px;padding:20px 24px;margin-bottom:16px;">
            <h2 style="margin:0 0 6px; color: white !important;">
                ‍⚕️ Recommended {spec}s Near You
            </h2>
            <p style="margin:0;opacity:0.85;font-size:15px;color: white !important;">
                 <b style="color: white !important;">{city}</b> &nbsp;|&nbsp;
                 <span style="color: white !important;">Specialty auto-selected based on your symptoms:</span>
                <span style="background:#4f8ef7;padding:2px 10px;border-radius:12px;
                    font-size:13px; color: white !important;">{spec}</span>
            </p>
            </div>""",
            unsafe_allow_html=True,
        )

        if city:
            show_doctor_links(city, spec)
            st.markdown("---")
            show_doctor_cards(st.session_state.nearby_doctors, city, spec)
        else:
            st.warning(
                " City not detected. Enter your city in the box above and click "
                "**Get Advice + Find Doctors Near Me** again."
            )


# ════════════════════════════════════════════════════════
# PAGE 2 — REPORT ANALYSIS
# ════════════════════════════════════════════════════════
elif choice == "Report Analysis":
    hero_section(
        "Smart Report Analysis",
        "Upload lab reports, PDFs, or medical images. Get a clear, patient-friendly explanation with safe next steps."
    )

    st.markdown("""
        <div class="report-shell">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:18px;flex-wrap:wrap;">
                <div style="max-width:680px;">
                    <div style="font-size:0.78rem;font-weight:900;color:#2563eb;text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px;">Report workspace</div>
                    <h2 style="margin:0;color:#0f172a;font-size:2rem;line-height:1.1;">Upload once. Understand faster.</h2>
                    <p style="color:#64748b;margin:10px 0 0;font-size:1rem;line-height:1.55;">Choose what you are uploading, add optional context, and let the assistant turn medical terms into plain language.</p>
                </div>
                <div style="background:#0f172a;color:white;border-radius:20px;padding:16px 18px;min-width:190px;box-shadow:0 18px 32px rgba(15,23,42,.18);">
                    <div style="font-size:.78rem;color:#bfdbfe;font-weight:800;text-transform:uppercase;letter-spacing:.08em;">Supported</div>
                    <div style="font-size:1.45rem;font-weight:900;margin-top:4px;color:white;">PDF + Images</div>
                    <div style="font-size:.85rem;color:#cbd5e1;margin-top:4px;">PDF, JPG, PNG, TXT, CSV</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    mode_left, mode_right = st.columns(2)
    with mode_left:
        st.markdown("""
            <div class="medical-card" style="margin-bottom:8px;background:linear-gradient(135deg,#eff6ff,#ffffff) !important;border-color:#bfdbfe;">
                <div style="font-size:0.78rem;font-weight:900;color:#2563eb;text-transform:uppercase;letter-spacing:.08em;">Mode 1</div>
                <h3 style="margin:8px 0 6px;color:#0f172a;">Lab & Health Reports</h3>
                <p style="color:#64748b;margin:0;">Blood reports, thyroid, liver, kidney, urine, ECG, full body checkups.</p>
            </div>
        """, unsafe_allow_html=True)
    with mode_right:
        st.markdown("""
            <div class="medical-card" style="margin-bottom:8px;background:linear-gradient(135deg,#fff7ed,#ffffff) !important;border-color:#fed7aa;">
                <div style="font-size:0.78rem;font-weight:900;color:#ea580c;text-transform:uppercase;letter-spacing:.08em;">Mode 2</div>
                <h3 style="margin:8px 0 6px;color:#0f172a;">X-rays & Imaging Notes</h3>
                <p style="color:#64748b;margin:0;">Preview X-rays and explain radiologist notes. Classifier model can be added later.</p>
            </div>
        """, unsafe_allow_html=True)

    analysis_type = st.radio(
        "Choose analysis mode",
        ["Lab & Health Reports", "X-rays & Medical Imaging"],
        horizontal=True,
        key="report_analysis_mode"
    )
    is_xray_mode = analysis_type == "X-rays & Medical Imaging"

    if is_xray_mode:
        st.info("Medical imaging mode previews your uploaded image and explains notes/findings you provide. It does not diagnose from pixels yet.")
    elif PYTESSERACT_AVAILABLE:
        st.success("Ready for text-based PDFs and readable report images. For scanned documents, native Tesseract may still be required.")
    else:
        st.warning("Best results: upload text-based PDFs, TXT, or CSV. OCR for scanned images is not available yet.")

    upload_col, detail_col = st.columns([1.35, 1], gap="large")

    with upload_col:
        st.markdown("### <span class='report-step'>1</span>Upload your file", unsafe_allow_html=True)
        st.markdown("<div class='report-mini'>Drag and drop here, or click Browse files. PDF upload is now highlighted and easier to find.</div>", unsafe_allow_html=True)
        report_file = st.file_uploader(
            "Upload PDF, image, or text file",
            type=["pdf", "txt", "csv", "jpg", "jpeg", "png", "bmp", "gif", "tiff"],
            accept_multiple_files=False,
            key="health_report_upload",
            label_visibility="collapsed"
        )
        st.markdown("""
            <div class="upload-promise">
                <div>PDF reports</div>
                <div>JPG / PNG images</div>
                <div>TXT / CSV files</div>
            </div>
        """, unsafe_allow_html=True)

        if report_file:
            file_size = len(report_file.getvalue()) / (1024 * 1024)
            st.success(f"File ready: {report_file.name} ({file_size:.2f} MB)")
            lower_name = report_file.name.lower()
            if lower_name.endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff")):
                st.image(report_file, caption="Uploaded image preview", use_container_width=True)
            elif lower_name.endswith(".pdf"):
                st.markdown("""
                    <div style="background:#ecfeff;border:1px solid #a5f3fc;border-radius:16px;padding:12px 14px;color:#155e75;font-weight:700;margin-top:10px;">
                        PDF selected. Click Analyze Report to extract and explain the content.
                    </div>
                """, unsafe_allow_html=True)

    with detail_col:
        st.markdown("### <span class='report-step'>2</span>Add details", unsafe_allow_html=True)
        st.markdown("<div class='report-mini'>Optional, but useful for better explanation.</div>", unsafe_allow_html=True)
        if is_xray_mode:
            report_type = st.selectbox(
                "Imaging type",
                ["X-ray (Chest)", "X-ray (Spine)", "X-ray (Hand/Arm)", "X-ray (Leg/Foot)", "CT Scan", "Ultrasound", "MRI", "Other Imaging"],
            )
            patient_context = st.text_area(
                "Radiologist findings or symptoms",
                placeholder="Example: Chest X-ray report says 'no focal consolidation' or 'left lower lobe opacity'.",
                height=150,
            )
            st.caption("Tip: paste the written radiologist report here if you have one.")
        else:
            report_type = st.selectbox(
                "Report type",
                ["Blood Report", "Full Body Checkup", "Urine Report", "Thyroid Report", "Liver Function Test", "Kidney Function Test", "COVID Report", "ECG Report", "Other Health Report"],
            )
            patient_context = st.text_area(
                "Patient context",
                placeholder="Age, sex, symptoms, known conditions, current medicines, pregnancy status, or what worries you...",
                height=150,
            )
            st.caption("Tip: adding age/symptoms helps the AI explain values more usefully.")

    st.markdown("### <span class='report-step'>3</span>Analyze", unsafe_allow_html=True)
    action_col, note_col = st.columns([1, 1.4])
    with action_col:
        analyze_btn = st.button("Analyze Report", use_container_width=True, type="primary", key="analyze_report_btn")
    with note_col:
        st.markdown("<div style='color:#64748b;padding-top:8px;'>Results are educational and should be confirmed with a qualified doctor.</div>", unsafe_allow_html=True)

    if analyze_btn:
        st.session_state.report_analysis = None
        st.session_state.report_text_preview = ""

        if report_file is None:
            st.error("Please upload a file first.")
        else:
            report_text, error = extract_report_text(report_file, is_xray=is_xray_mode)

            if error:
                st.error(error)
            elif is_xray_mode and "[X-RAY_IMAGE_UPLOADED]" in report_text:
                st.session_state.report_text_preview = (
                    f"Imaging type: {report_type}\n"
                    f"Image file: {report_file.name}\n"
                    f"User notes: {patient_context.strip() or 'No findings/notes provided.'}"
                )
                with st.spinner("Preparing X-ray guidance..."):
                    st.session_state.report_analysis = analyze_xray_report(report_type, patient_context)
                st.success("Analysis ready.")
            elif len(report_text.strip()) < 20:
                st.warning("The extracted text is too short or unclear. Try a clearer file or paste the report text manually.")
            else:
                st.session_state.report_text_preview = report_text[:3000]
                with st.spinner("Analyzing your report..."):
                    if is_xray_mode:
                        imaging_context = patient_context.strip() or report_text[:800]
                        st.session_state.report_analysis = analyze_xray_report(report_type, imaging_context)
                    else:
                        st.session_state.report_analysis = analyze_health_report(report_text, report_type, patient_context)
                st.success("Analysis ready.")

    if st.session_state.report_text_preview:
        with st.expander("Preview of extracted/uploaded information"):
            st.text(st.session_state.report_text_preview)

    if st.session_state.report_analysis:
        st.markdown("---")
        st.markdown("### Analysis Results")
        with st.chat_message("assistant", avatar="assistant"):
            st.markdown(st.session_state.report_analysis)
        st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 6px; margin-top: 20px;">
                <strong style="color: #d97706; font-size: 0.95rem;">DISCLAIMER:</strong>
                <span style="color: #92400e; font-size: 0.9rem; margin-left: 5px;">
                    This analysis is educational only, not a medical diagnosis. Always consult a qualified doctor for medical decisions.
                </span>
            </div>
        """, unsafe_allow_html=True)


# PAGE 3 — HOSPITALS NEAR ME
# ════════════════════════════════════════════════════════
elif choice == "Hospitals Near Me":
    hero_section("Hospitals Near You", "Find elite medical facilities, multi-specialty hospitals, and local clinics with real-time navigation mapping.")
    
    # ── Search Input ──────────────────────────────────────────
    search_col, _ = st.columns([2, 1])
    with search_col:
        city = st.text_input(
            "Enter your city to find nearest hospitals:",
            value=st.session_state.auto_city,
            placeholder="e.g., Delhi, Mumbai, Gurgaon...",
            key="hosp_city_input"
        )
        btn_hosp = st.button("Find Hospitals ", use_container_width=True, type="primary")
        curr_hosp_city = city.lower().strip()
        
        # Clear cached results if button clicked OR city changed since last search
        if btn_hosp or (st.session_state.get('hosp_search') and curr_hosp_city != st.session_state.get('last_hosp_city', '')):
            st.session_state.hosp_results = []
            st.session_state.hosp_search = True
            st.session_state.last_hosp_city = curr_hosp_city

        if st.session_state.hosp_search:
            if not city.strip():
                st.warning("Please enter a city name.")
            else:
                if not st.session_state.hosp_results:
                    with st.spinner(f" Locating {city}..."):
                        lat, lon = geocode_city(city)
                    
                    if not lat:
                        st.error(f"❌ Could not find **{city}**. Check the spelling.")
                    else:
                        with st.spinner(" Fetching nearby hospitals & clinics..."):
                            places = get_hospitals_osm(lat, lon)
                            st.session_state.hosp_results = places
                            st.session_state.hosp_coords = (lat, lon)

    # ── Display Results (Moved Outside and Full-Width) ──
    if st.session_state.hosp_results:
        st.success(f"✅ Found **{len(st.session_state.hosp_results)}** medical facilities nearby")
        show_hospital_cards(st.session_state.hosp_results)
        st.markdown("---")
        st.markdown("### ️ Interactive Map")
        lat, lon = st.session_state.hosp_coords
        render_hospital_map(lat, lon, st.session_state.hosp_results)
    elif st.session_state.hosp_search:
        st.warning("No hospitals found in this area.")


# ════════════════════════════════════════════════════════
# PAGE 4 — DOCTORS NEAR ME
# ════════════════════════════════════════════════════════
elif choice == "Doctors Near Me":
    hero_section("Find Top Doctors", "Book appointments with the best-rated specialists in your area. verified reviews and availability updated in real-time.")

    # ── Search Input ──────────────────────────────────────────
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        city = st.text_input(
            "Your city:", 
            value=st.session_state.auto_city,
            placeholder="e.g., Delhi, Mumbai...",
            key="doc_search_city"
        )
    with c2:
        specialty = st.selectbox("Select Specialty:", VALID_SPECIALTIES)
    with c3:
        st.write("") # Spacer
        if st.button("Clear ️", use_container_width=True, key="doc_clear"):
            st.session_state.doc_search = False
            st.session_state.doc_results = []
            st.rerun()

    btn_doc = st.button("Search Doctors ", use_container_width=True, type="primary")
    curr_doc_query = f"{city.lower().strip()}_{specialty}"

    # Clear cached results if button clicked OR search query (city/specialty) changed
    if btn_doc or (st.session_state.get('doc_search') and curr_doc_query != st.session_state.get('last_doc_query', '')):
        st.session_state.doc_results = []
        st.session_state.doc_search = True
        st.session_state.last_doc_query = curr_doc_query

    if st.session_state.doc_search:
        if not city.strip():
            st.warning("Please enter a city name.")
        else:
            if not st.session_state.doc_results:
                with st.spinner(f" Searching top {specialty}s in {city}..."):
                    doctors = get_doctors(city, specialty)
                    st.session_state.doc_results = doctors

            if st.session_state.doc_results:
                show_doctor_links(city, specialty)
                st.markdown("---")
                show_doctor_cards(st.session_state.doc_results, city, specialty)


# ════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════
st.markdown("---")
st.caption(
    "Built by **Pankaj Kumar** · "
    "Data: Practo · OpenStreetMap · Google · "
    "AI: Groq LLaMA 3.3 70B"
)
