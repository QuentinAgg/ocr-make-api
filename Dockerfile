FROM python:3.11-slim

# Installer Tesseract + dépendances
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Créer un dossier de travail
WORKDIR /app

# Copier les fichiers du projet dans le conteneur
COPY . .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Démarrer le serveur Flask avec gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "main:app"]
