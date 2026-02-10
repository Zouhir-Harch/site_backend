# 1️⃣ Image de base : Python léger et stable
FROM python:3.11-slim

# 2️⃣ Empêche Python de créer des fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3️⃣ Installer dépendances système nécessaires à ReportLab
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# 4️⃣ Dossier de travail dans le conteneur
WORKDIR /app

# 5️⃣ Copier les dépendances Python
COPY requirements.txt .

# 6️⃣ Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# 7️⃣ Copier tout le code backend
COPY . .

# 8️⃣ Créer le dossier files (PDF générés)
RUN mkdir -p files

# 9️⃣ Exposer le port FastAPI
EXPOSE 8000

# 🔟 Lancer l’API (OBLIGATOIRE pour Railway)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
