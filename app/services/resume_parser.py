import os
import pdfplumber
from typing import Dict, List, Any, Optional, Union

from ..matching.embedding import get_embedding
from . import semantic_matcher


def extract_text_from_pdf(file_path: str) -> str:
    text = ""

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print("Extraction error:", e)
        return ""

    return text.strip()


_nlp = None


def _load_spacy():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy as _spacy
    except Exception:
        return None

    try:
        _nlp = _spacy.load("en_core_web_sm")
    except Exception:
        try:
            _nlp = _spacy.blank("en")
        except Exception:
            _nlp = None
    return _nlp


def _load_skills_list() -> List[str]:
    skills_path = os.path.join(os.path.dirname(__file__), "..", "data", "skills.txt")
    skills_path = os.path.normpath(skills_path)
    skills = []
    try:
        with open(skills_path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s:
                    skills.append(s.lower())
    except Exception:
        # minimal fallback list
        skills = [
            "python",
            "fastapi",
            "docker",
            "aws",
            "sql",
            "nlp",
            "machine learning",
        ]
    return skills


def extract_entities_and_skills(text: str) -> Dict:
    """
    Returns a dict with simple extracted entities and skills.
    """
    nlp = _load_spacy()
    skills_master = _load_skills_list()
    result = {"entities": {}, "skills": []}

    if nlp:
        doc = nlp(text)
        ents = {}
        for ent in doc.ents:
            ents.setdefault(ent.label_, []).append(ent.text)
        result["entities"] = ents

    # skills: simple substring match against a skills list
    text_lc = text.lower()
    found = set()
    for skill in skills_master:
        if skill in text_lc:
            found.add(skill)
    result["skills"] = sorted(found)
    return result


def parse_resume(file_path: str, add_to_index: bool = False, resume_id: Optional[Union[str, int]] = None) -> Dict:
    """
    Full parse routine: text extraction, entity & skill extraction, embedding.
    If `add_to_index` is True and `resume_id` provided, the embedding will be added
    to the project's semantic index (if available).
    """
    text = extract_text_from_pdf(file_path)
    if not text:
        return {"text": "", "entities": {}, "skills": [], "embedding": None}

    meta = extract_entities_and_skills(text)
    emb = None
    try:
        emb = get_embedding(text)
    except Exception as e:
        print("Embedding error:", e)

    if add_to_index and resume_id is not None:
        try:
            semantic_matcher.get_global_index().add(resume_id, text, emb)
        except Exception as e:
            print("Indexing error:", e)

    return {"text": text, "entities": meta.get("entities", {}), "skills": meta.get("skills", []), "embedding": emb}
