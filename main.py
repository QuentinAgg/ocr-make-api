import pytesseract
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

from flask import Flask, request, jsonify
import cv2
import pytesseract
import numpy as np
import re

app = Flask(__name__)

def extract_text_data(image):
    """Run OCR on the image and return text with positional data."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    return data

def find_text_near_keyword(data, keyword):
    """Find text to the right of a specific keyword (like 'Price:')."""
    for i, word in enumerate(data['text']):
        if keyword.lower() in word.lower():
            for j in range(i + 1, min(i + 5, len(data['text']))):
                if re.search(r'\d', data['text'][j]):
                    return data['text'][j]
    return ""

def extract_price_from_relative_position(data, reference_y, direction='above'):
    """Get closest number above or below a given y-coordinate."""
    matches = []
    for i, word in enumerate(data['text']):
        if re.match(r'^\d+\.\d+$', word):
            y = data['top'][i]
            if (direction == 'above' and y < reference_y) or (direction == 'below' and y > reference_y):
                matches.append((y, word))
    if direction == 'above':
        matches.sort(reverse=True)
    else:
        matches.sort()
    return matches[0][1] if matches else ""

def extract_key_elements(data):
    pair = ""
    for word in data['text']:
        if re.fullmatch(r'[A-Z]{6,7}', word):
            pair = word
            break

    type_entree = ""
    for i in range(len(data['text']) - 1):
        if data['text'][i].lower() in ['buy', 'sell'] and data['text'][i+1].lower() in ['limit', 'stop']:
            type_entree = f"{data['text'][i]} {data['text'][i+1]}"
            break

    entry_price = find_text_near_keyword(data, "Price")

    orange_y = green_y = None
    for i, word in enumerate(data['text']):
        if word.startswith("1.129"):
            orange_y = data['top'][i]
        elif word.startswith("1.116"):
            green_y = data['top'][i]

    stop_loss = extract_price_from_relative_position(data, orange_y, 'above') if orange_y else ""
    take_profit = extract_price_from_relative_position(data, green_y, 'above') if green_y else ""

    return {
        "pair": pair,
        "type_entree": type_entree,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }

@app.route("/ocr", methods=["POST"])
def ocr():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files['image']
    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Failed to decode image"}), 400

    data = extract_text_data(img)
    extracted = extract_key_elements(data)
    return jsonify(extracted)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
