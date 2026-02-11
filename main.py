from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")

os.makedirs(FILES_DIR, exist_ok=True)

app = FastAPI(title="Générateur de CV et Page de Garde")

# ✅ Configuration CORS pour Railway/Netlify
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Accepte toutes les origines pour Railway
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles de données
class LettreMotivationData(BaseModel):
    # Informations personnelles
    nom: str
    prenom: str
    adresse: str
    code_postal: str
    ville: str
    email: EmailStr
    telephone: str
    
    # Informations destinataire
    entreprise: str
    destinataire_nom: Optional[str] = None
    destinataire_titre: Optional[str] = None
    adresse_entreprise: Optional[str] = None
    
    # Informations sur le poste
    poste: str
    type_contrat: str  # "Stage", "CDI", "CDD", "Alternance"
    date_disponibilite: Optional[str] = None
    
    # Contenu
    objet: str
    paragraphe_intro: str
    paragraphe_competences: str
    paragraphe_motivation: str
    paragraphe_conclusion: str
    
    # Optionnel
    reference_annonce: Optional[str] = None
    lieu_redaction: str
    date_redaction: Optional[str] = None

class PageDeGardeData(BaseModel):
    annee_universitaire: str
    type_rapport: str  # "Stage d'initiation", "Stage de perfectionnement", "PFE"
    titre_stage: str
    entreprise: str
    logo_entreprise: Optional[str] = None
    etudiant_nom: str
    etudiant_prenom: str
    filiere: str
    encadrant_entreprise: str
    encadrant_academique: str
    date_debut: str
    date_fin: str
    etablissement: str
    logo_etablissement: Optional[str] = None

class ExperiencePro(BaseModel):
    poste: str
    entreprise: str
    date_debut: str
    date_fin: str
    description: str

class Formation(BaseModel):
    diplome: str
    etablissement: str
    annee: str
    mention: Optional[str] = None

class CVData(BaseModel):
    nom: str
    prenom: str
    titre_professionnel: str
    email: EmailStr
    telephone: str
    adresse: str
    date_naissance: Optional[str] = None
    photo: Optional[str] = None
    profil: str
    experiences: List[ExperiencePro]
    formations: List[Formation]
    competences_techniques: List[str]
    competences_linguistiques: List[str]
    loisirs: Optional[List[str]] = []

def wrap_text(c, text, font_name, font_size, max_width):
    """
    Coupe un texte en plusieurs lignes pour respecter une largeur maximale
    Compatible ReportLab
    """
    if not text:
        return [""]

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

def draw_lettre_motivation(data: LettreMotivationData, filename: str):
    """Génère une lettre de motivation professionnelle"""
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Marges
    left_margin = 2.5*cm
    right_margin = width - 2.5*cm
    content_width = right_margin - left_margin
    
    y_pos = height - 2*cm
    
    # === COORDONNÉES EXPÉDITEUR (en haut à gauche) ===
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    
    c.drawString(left_margin, y_pos, f"{data.prenom} {data.nom}")
    y_pos -= 0.5*cm
    c.drawString(left_margin, y_pos, data.adresse)
    y_pos -= 0.5*cm
    c.drawString(left_margin, y_pos, f"{data.code_postal} {data.ville}")
    y_pos -= 0.5*cm
    c.drawString(left_margin, y_pos, f"Tél : {data.telephone}")
    y_pos -= 0.5*cm
    c.drawString(left_margin, y_pos, f"Email : {data.email}")
    
    y_pos -= 1.5*cm
    
    # === COORDONNÉES DESTINATAIRE (à droite) ===
    dest_x = width - 7*cm
    y_dest = height - 2*cm
    
    if data.destinataire_nom and data.destinataire_titre:
        c.drawString(dest_x, y_dest, f"{data.destinataire_titre} {data.destinataire_nom}")
        y_dest -= 0.5*cm
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(dest_x, y_dest, data.entreprise)
    y_dest -= 0.5*cm
    
    c.setFont("Helvetica", 10)
    if data.adresse_entreprise:
        adresse_lines = wrap_text(c, data.adresse_entreprise, "Helvetica", 10, 6*cm)
        for line in adresse_lines:
            c.drawString(dest_x, y_dest, line)
            y_dest -= 0.5*cm
    
    # === LIEU ET DATE ===
    c.setFont("Helvetica", 10)
    date_str = data.date_redaction if data.date_redaction else "Le [date]"
    lieu_date = f"{data.lieu_redaction}, {date_str}"
    c.drawString(left_margin, y_pos, lieu_date)
    
    y_pos -= 1.5*cm
    
    # === OBJET ===
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y_pos, "Objet : ")
    c.setFont("Helvetica", 11)
    
    objet_text = data.objet
    objet_x = left_margin + c.stringWidth("Objet : ", "Helvetica-Bold", 11)
    objet_lines = wrap_text(c, objet_text, "Helvetica", 11, content_width - c.stringWidth("Objet : ", "Helvetica-Bold", 11))
    
    for i, line in enumerate(objet_lines):
        if i == 0:
            c.drawString(objet_x, y_pos, line)
        else:
            c.drawString(left_margin + 1.5*cm, y_pos - (i * 0.5*cm), line)
    
    y_pos -= (len(objet_lines) * 0.5*cm) + 0.3*cm
    
    # Référence annonce (si fournie)
    if data.reference_annonce:
        c.setFont("Helvetica", 10)
        c.drawString(left_margin, y_pos, f"Réf. : {data.reference_annonce}")
        y_pos -= 0.8*cm
    else:
        y_pos -= 0.5*cm
    
    # === FORMULE D'APPEL ===
    c.setFont("Helvetica", 11)
    if data.destinataire_nom:
        appel = f"Madame, Monsieur {data.destinataire_nom},"
    else:
        appel = "Madame, Monsieur,"
    c.drawString(left_margin, y_pos, appel)
    
    y_pos -= 1*cm
    
    # === PARAGRAPHE INTRODUCTION ===
    c.setFont("Helvetica", 11)
    intro_lines = wrap_text(c, data.paragraphe_intro, "Helvetica", 11, content_width)
    for line in intro_lines:
        if y_pos < 4*cm:
            c.showPage()
            y_pos = height - 2*cm
            c.setFont("Helvetica", 11)
        c.drawString(left_margin, y_pos, line)
        y_pos -= 0.55*cm
    
    y_pos -= 0.5*cm
    
    # === PARAGRAPHE COMPÉTENCES ===
    comp_lines = wrap_text(c, data.paragraphe_competences, "Helvetica", 11, content_width)
    for line in comp_lines:
        if y_pos < 4*cm:
            c.showPage()
            y_pos = height - 2*cm
            c.setFont("Helvetica", 11)
        c.drawString(left_margin, y_pos, line)
        y_pos -= 0.55*cm
    
    y_pos -= 0.5*cm
    
    # === PARAGRAPHE MOTIVATION ===
    motiv_lines = wrap_text(c, data.paragraphe_motivation, "Helvetica", 11, content_width)
    for line in motiv_lines:
        if y_pos < 4*cm:
            c.showPage()
            y_pos = height - 2*cm
            c.setFont("Helvetica", 11)
        c.drawString(left_margin, y_pos, line)
        y_pos -= 0.55*cm
    
    y_pos -= 0.5*cm
    
    # === PARAGRAPHE CONCLUSION ===
    conclu_lines = wrap_text(c, data.paragraphe_conclusion, "Helvetica", 11, content_width)
    for line in conclu_lines:
        if y_pos < 4*cm:
            c.showPage()
            y_pos = height - 2*cm
            c.setFont("Helvetica", 11)
        c.drawString(left_margin, y_pos, line)
        y_pos -= 0.55*cm
    
    y_pos -= 1*cm
    
    # === FORMULE DE POLITESSE ===
    if y_pos < 5*cm:
        c.showPage()
        y_pos = height - 2*cm
    
    c.setFont("Helvetica", 11)
    politesse = "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées."
    politesse_lines = wrap_text(c, politesse, "Helvetica", 11, content_width)
    for line in politesse_lines:
        c.drawString(left_margin, y_pos, line)
        y_pos -= 0.55*cm
    
    y_pos -= 1.5*cm
    
    # === SIGNATURE ===
    c.setFont("Helvetica", 11)
    signature_x = width - 6*cm
    c.drawString(signature_x, y_pos, f"{data.prenom} {data.nom}")
    
    c.save()
    print(f"Lettre de motivation générée: {filename}")

# Utilitaires pour la génération PDF
def draw_page_de_garde(data: PageDeGardeData, filename: str):
    """Génère une page de garde académique conforme au modèle ENSA"""
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    margin = 2.5 * cm
    y = height - 2.5 * cm

    # ================== EN-TÊTE ==================
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y, "Royaume du Maroc")
    y -= 0.6 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, y, data.etablissement or "")
    y -= 0.5 * cm

    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y, data.filiere or "")
    y -= 0.8 * cm

    c.line(margin, y, width - margin, y)
    y -= 1.2 * cm

    # ================== TYPE DE DOCUMENT ==================
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(width / 2, y, "Mémoire de Projet de Fin d'Étude")
    y -= 0.7 * cm

    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y, "Présenté en vue de l'obtention")
    y -= 0.6 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, y, "du Diplôme d'Ingénieur d'État")
    y -= 0.6 * cm

    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y, f"Spécialité : {data.filiere or ''}")
    y -= 0.6 * cm

    c.setFont("Helvetica", 9)
    annee = data.annee_universitaire or ""
    c.drawCentredString(width / 2, y, f"N° : {annee.replace('-', '/')}")
    y -= 1.2 * cm

    # ================== SUJET ==================
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, y, "Sujet :")
    y -= 0.8 * cm

    # ===== TITRE DANS CADRE (ALIGNÉ) =====
    c.setFont("Helvetica-Bold", 13)
    titre_lines = wrap_text(
        c,
        data.titre_stage or "",
        "Helvetica-Bold",
        13,
        width - 2 * margin - 2 * cm
    )

    line_height = 0.7 * cm
    padding = 0.8 * cm

    box_height = len(titre_lines) * line_height + 2 * padding
    box_y = y - box_height

    c.rect(
        margin + 1 * cm,
        box_y,
        width - 2 * margin - 2 * cm,
        box_height
    )

    ty = box_y + box_height - padding - line_height
    for line in titre_lines:
        c.drawCentredString(width / 2, ty, line)
        ty -= line_height

    y = box_y - 1.5 * cm

    # ================== INFORMATIONS ==================
    shift_x = 2.5 * cm   # décalage vers la droite (ajustable)
    col_left = margin + shift_x
    col_right = width / 2 + 0.5 * cm + shift_x

    c.setFont("Helvetica-Bold", 11)
    c.drawString(col_left, y, "Réalisé par :")
    c.drawString(col_right, y, "Soutenu le :")
    y -= 0.6 * cm

    c.setFont("Helvetica", 10)
    c.drawString(
        col_left,
        y,
        f"Mme/M. {data.etudiant_prenom or ''} {data.etudiant_nom or ''}"
    )
    c.drawString(col_right, y, data.date_fin or "—")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(col_left, y, "Membres du Jury :")
    c.drawString(col_right, y, "Encadré par :")
    y -= 0.6 * cm

    c.setFont("Helvetica", 10)
    c.drawString(col_left, y, data.encadrant_academique or "—")

    enc_lines = wrap_text(
        c,
        f"Mme/M. {data.encadrant_entreprise or ''}",
        "Helvetica",
        10,
        width / 2 - margin
    )
    for i, line in enumerate(enc_lines):
        c.drawString(col_right, y - i * 0.5 * cm, line)

    y -= max(len(enc_lines) * 0.5 * cm, 0.6 * cm)
    y -= 0.4 * cm

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.grey)
    c.drawString(col_right, y, f"({data.entreprise or ''})")
    c.setFillColor(colors.black)

    # ================== PIED DE PAGE ==================
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(
        width / 2,
        2 * cm,
        f"Année Universitaire : {data.annee_universitaire or ''}"
    )

    c.save()

def draw_cv(data: CVData, filename: str):
    """Génère un CV 100% compatible ATS"""
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    left = 2 * cm
    right = width - 2 * cm
    max_width = right - left
    y = height - 2 * cm

    # =========================
    # NAME
    # =========================
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.black)
    c.drawString(left, y, f"{data.prenom.upper()} {data.nom.upper()}")
    y -= 0.6 * cm

    # TITLE
    c.setFont("Helvetica", 11)
    c.drawString(left, y, data.titre_professionnel)
    y -= 0.6 * cm

    # CONTACT
    c.setFont("Helvetica", 9)
    c.drawString(
        left,
        y,
        f"{data.email} | {data.telephone} | {data.adresse}"
    )
    y -= 0.8 * cm

    # =========================
    # SECTION TITLE UTILS
    # =========================
    def section(title):
        nonlocal y
        if y < 3 * cm:
            c.showPage()
            y = height - 2 * cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left, y, title)
        y -= 0.4 * cm
        c.line(left, y, right, y)
        y -= 0.4 * cm

    def wrap(text, size=9):
        nonlocal y
        c.setFont("Helvetica", size)
        words = text.split()
        line = ""
        for w in words:
            test = f"{line} {w}".strip()
            if c.stringWidth(test, "Helvetica", size) <= max_width:
                line = test
            else:
                c.drawString(left, y, line)
                y -= 0.4 * cm
                line = w
        if line:
            c.drawString(left, y, line)
            y -= 0.4 * cm

    # =========================
    # SUMMARY
    # =========================
    section("PROFESSIONAL SUMMARY")
    wrap(data.profil)

    y -= 0.3 * cm

    # =========================
    # SKILLS
    # =========================
    section("SKILLS")
    wrap(", ".join(data.competences_techniques))

    y -= 0.3 * cm

    # =========================
    # EXPERIENCE
    # =========================
    section("PROFESSIONAL EXPERIENCE")

    for exp in data.experiences:
        if y < 4 * cm:
            c.showPage()
            y = height - 2 * cm

        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, y, f"{exp.poste} – {exp.entreprise}")
        y -= 0.4 * cm

        c.setFont("Helvetica-Oblique", 9)
        c.drawString(left, y, f"{exp.date_debut} – {exp.date_fin}")
        y -= 0.4 * cm

        c.setFont("Helvetica", 9)
        for line in exp.description.split("\n"):
            wrap(f"- {line}", 9)

        y -= 0.2 * cm

    # =========================
    # EDUCATION
    # =========================
    section("EDUCATION")

    for f in data.formations:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, y, f.diplome)
        y -= 0.4 * cm

        c.setFont("Helvetica", 9)
        mention = f" ({f.mention})" if f.mention else ""
        c.drawString(left, y, f"{f.etablissement} – {f.annee}{mention}")
        y -= 0.5 * cm

    # =========================
    # LANGUAGES
    # =========================
    section("LANGUAGES")
    wrap(", ".join(data.competences_linguistiques))

    # =========================
    # INTERESTS (OPTIONAL)
    # =========================
    if data.loisirs:
        section("INTERESTS")
        wrap(", ".join(data.loisirs))

    c.save()

# Routes API
@app.get("/")
def read_root():
    return {"message": "API Générateur de CV et Page de Garde", "status": "online"}

@app.post("/generate/lettre-motivation")
async def generate_lettre_motivation(data: LettreMotivationData):
    """Génère une lettre de motivation professionnelle"""
    try:
        print(f"\n=== GÉNÉRATION LETTRE DE MOTIVATION ===")
        print(f"Candidat: {data.nom} {data.prenom}")
        print(f"Poste: {data.poste}")
        print(f"Entreprise: {data.entreprise}")

        filename = (
            f"lettre_motivation_{data.nom}_{data.prenom}_"
            f"{data.entreprise.replace(' ', '_')}.pdf"
        )
        filepath = os.path.join(FILES_DIR, filename)

        draw_lettre_motivation(data, filepath)

        if not os.path.exists(filepath):
            raise Exception("Le fichier PDF n'a pas été créé")

        print(f"Fichier créé: {filepath} ({os.path.getsize(filepath)} bytes)")

        return FileResponse(
            filepath,
            media_type="application/pdf",
            filename=filename
        )

    except Exception as e:
        print(f"ERREUR LETTRE MOTIVATION: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/page-de-garde")
async def generate_page_de_garde(data: PageDeGardeData):
    """Génère une page de garde de rapport de stage"""
    try:
        filename = f"page_de_garde_{data.etudiant_nom}_{data.etudiant_prenom}.pdf"
        filepath = os.path.join(FILES_DIR, filename)

        draw_page_de_garde(data, filepath)

        return FileResponse(
            filepath,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        print(f"ERREUR PAGE DE GARDE: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/cv")
async def generate_cv(data: CVData):
    """Génère un CV professionnel"""
    try:
        filename = f"cv_{data.nom}_{data.prenom}.pdf"
        filepath = os.path.join(FILES_DIR, filename)

        draw_cv(data, filepath)

        return FileResponse(
            filepath,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        print(f"ERREUR CV: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}

# ✅ IMPORTANT pour Railway - Utilise la variable PORT
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # ✅ Railway utilise $PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
