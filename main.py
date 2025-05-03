from flask import Flask, request, jsonify
import cv2
import numpy as np
import pytesseract

app = Flask(__name__)

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Image decoding failed"}), 400

    # Traitement image pour OCR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)

    text = pytesseract.image_to_string(thresh)

    # Extraction simple depuis le texte brut
    result = {
        "lot_size": extract_number_from_text(text, keywords=["lot"]),
        "entry_price": extract_number_from_text(text, keywords=["entry"]),
        "stop_loss": extract_number_from_text(text, keywords=["sl", "stop"]),
        "take_profit": extract_number_from_text(text, keywords=["tp", "profit"]),
        "spread": "",  # à compléter ou automatiser plus tard
        "slippage": "",  # à compléter
        "commission": "",  # à compléter
        "type_entree": extract_entry_type(text),
        "pair": extract_pair(text)
    }

    return jsonify(result)

def extract_number_from_text(text, keywords):
    lines = text.lower().split('\n')
    for line in lines:
        if any(k in line for k in keywords):
            parts = line.split()
            numbers = [p for p in parts if any(c.isdigit() for c in p)]
            if numbers:
                return numbers[-1]
    return ""

def extract_entry_type(text):
    text = text.lower()
    for entry in ["buy stop", "sell stop", "buy limit", "sell limit"]:
        if entry in text:
            return entry
    return ""

def extract_pair(text):
    import re
    match = re.search(r'\b[A-Z]{6}\b', text.upper())
    return match.group(0) if match else ""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
