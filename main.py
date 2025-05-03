from flask import Flask, request, jsonify
import cv2
import numpy as np
import pytesseract

app = Flask(__name__)

# Configuration de Tesseract (optionnel)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # chemin par défaut sur Render

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files['image']
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)

    raw_text = pytesseract.image_to_string(thresh)

    # Détection simple par mots-clés et lignes
    lot_size = detect_by_keywords(raw_text, ['lot'])
    entry_price = detect_by_keywords(raw_text, ['entry'])
    stop_loss = detect_by_keywords(raw_text, ['sl', 'stop'])
    take_profit = detect_by_keywords(raw_text, ['tp', 'profit'])
    entry_type = detect_by_keywords(raw_text, ['buy stop', 'sell stop', 'buy limit', 'sell limit'])
    pair = detect_pair(raw_text)

    response = {
        "lot_size": lot_size,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "spread": "",  # à calculer si besoin
        "slippage": "",  # à fournir ou calculer
        "commission": "",  # à définir
        "type_entree": entry_type,
        "pair": pair
    }

    return jsonify(response)

def detect_by_keywords(text, keywords):
    lines = text.lower().split('\n')
    for line in lines:
        for key in keywords:
            if key in line:
                digits = [s for s in line.split() if any(c.isdigit() for c in s)]
                if digits:
                    return digits[-1]  # prend le dernier chiffre de la ligne
    return ""

def detect_pair(text):
    # Recherche de paires de type GBPUSD, EURUSD etc.
    import re
    match = re.search(r'([A-Z]{6})', text.upper())
    return match.group(1) if match else ""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
