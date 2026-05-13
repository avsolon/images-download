import os
import time
import requests
import pandas as pd

from io import BytesIO
from PIL import Image
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# =====================================================
# LOAD ENV
# =====================================================

load_dotenv()

API_KEY = os.getenv("PIXABAY_API_KEY")

if not API_KEY:
    raise Exception("PIXABAY_API_KEY not found in .env")

# =====================================================
# SETTINGS
# =====================================================

CSV_FILE = "input.csv"
OUTPUT_DIR = "images"

IMAGE_WIDTH = 400
IMAGE_HEIGHT = 300

# =====================================================
# CREATE OUTPUT FOLDER
# =====================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =====================================================
# LOAD CSV
# =====================================================

try:
    df = pd.read_csv(
        CSV_FILE,
        encoding="utf-8-sig",
        on_bad_lines="skip",
        engine="python"
    )
except Exception as e:
    print(f"CSV read error: {e}")
    exit(1)

print("\nCSV Columns:")
print(df.columns)
print()

# =====================================================
# AUTO DETECT COLUMNS
# =====================================================

QUESTION_COLUMNS = [
    "Вопрос",
    "Question",
    "question",
]

ANSWER_COLUMNS = [
    "Правильный",
    "Correct",
    "correct",
]

IMAGE_COLUMNS = [
    "Картинка",
    "Image",
    "image",
    "filename",
]

question_col = None
answer_col = None
image_col = None

for c in QUESTION_COLUMNS:
    if c in df.columns:
        question_col = c
        break

for c in ANSWER_COLUMNS:
    if c in df.columns:
        answer_col = c
        break

for c in IMAGE_COLUMNS:
    if c in df.columns:
        image_col = c
        break

if not answer_col:
    raise Exception("Correct answer column not found")

if not image_col:
    raise Exception("Image filename column not found")

print(f"Using answer column: {answer_col}")
print(f"Using image column: {image_col}")

# =====================================================
# TRANSLATE
# =====================================================

def translate_text(text):

    try:
        translated = GoogleTranslator(
            source='auto',
            target='en'
        ).translate(text)

        return translated

    except Exception as e:

        print(f"Translation error: {e}")

        return text

# =====================================================
# BUILD SEARCH QUERY
# =====================================================

def build_query(question, answer):

    # combine question + answer
    text = f"{question} {answer}"

    # translate to english
    translated = translate_text(text)

    query = translated

    lower = translated.lower()

    # =====================================================
    # SPACE / ASTRONOMY
    # =====================================================

    if any(word in lower for word in [
        "planet",
        "solar system",
        "star",
        "galaxy",
        "moon",
        "sun",
        "mars",
        "venus",
        "mercury",
        "jupiter",
        "saturn",
        "neptune",
        "uranus",
        "proxima",
        "sirius",
        "betelgeuse"
    ]):

        query += " space astronomy"

    # =====================================================
    # GEOGRAPHY
    # =====================================================

    elif any(word in lower for word in [
        "ocean",
        "lake",
        "river",
        "mountain",
        "desert",
        "country",
        "capital",
        "forest"
    ]):

        query += " nature landscape"

    # =====================================================
    # ANIMALS
    # =====================================================

    elif any(word in lower for word in [
        "animal",
        "tiger",
        "lion",
        "elephant",
        "bird",
        "fish",
        "dog",
        "cat"
    ]):

        query += " wildlife"

    # =====================================================
    # SCIENCE
    # =====================================================

    elif any(word in lower for word in [
        "physics",
        "chemistry",
        "atom",
        "molecule",
        "electricity"
    ]):

        query += " science illustration"

    # =====================================================
    # HISTORY
    # =====================================================

    elif any(word in lower for word in [
        "war",
        "king",
        "empire",
        "ancient",
        "history"
    ]):

        query += " historical illustration"

    # =====================================================
    # DEFAULT
    # =====================================================

    else:

        query += " high quality"

    return query

# =====================================================
# SEARCH PIXABAY
# =====================================================

def search_image(query):

    url = "https://pixabay.com/api/"

    params = {
        "key": API_KEY,
        "q": query,
        "image_type": "photo",
        "per_page": 10,
        "safesearch": "true",
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    data = response.json()

    hits = data.get("hits", [])

    if not hits:
        return None

    return hits[0]["largeImageURL"]

# =====================================================
# SAVE IMAGE
# =====================================================

def save_image(image_url, filepath):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        image_url,
        headers=headers,
        timeout=30
    )

    image = Image.open(BytesIO(response.content)).convert("RGB")

    image.thumbnail((IMAGE_WIDTH, IMAGE_HEIGHT))

    background = Image.new(
        "RGB",
        (IMAGE_WIDTH, IMAGE_HEIGHT),
        (255, 255, 255)
    )

    x = (IMAGE_WIDTH - image.width) // 2
    y = (IMAGE_HEIGHT - image.height) // 2

    background.paste(image, (x, y))

    background.save(filepath, "JPEG", quality=90)

# =====================================================
# MAIN
# =====================================================

total = len(df)

print(f"\nFound {total} rows\n")

for index, row in df.iterrows():

    try:

        question = str(row[question_col]).strip()
        answer = str(row[answer_col]).strip()

        filename = str(row[image_col]).strip()

        filepath = os.path.join(OUTPUT_DIR, filename)

        # skip existing files
        if os.path.exists(filepath):

            print(f"[SKIP] {filename}")

            continue

        # build improved search query
        query = build_query(question, answer)

        print(f"\n[{index+1}/{total}]")
        print(f"Question: {question}")
        print(f"Answer: {answer}")
        print(f"Search: {query}")

        image_url = search_image(query)

        if not image_url:

            print("[FAILED] No image found")

            continue

        print("Downloading image...")

        save_image(image_url, filepath)

        print(f"[OK] Saved: {filepath}")

    except Exception as e:

        print(f"[ERROR] {e}")

    time.sleep(1)

print("\nDONE")