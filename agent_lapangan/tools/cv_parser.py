from __future__ import annotations

import re
from typing import Any


SECTION_ALIASES = {
    "summary": [r"\bsummary\b", r"\bprofile\b", r"\bobjective\b"],
    "experience": [
        r"\bexperience\b",
        r"\bwork experience\b",
        r"\bprofessional experience\b",
        r"\bemployment\b",
        r"\bexperiences\b"
    ],
    "education": [r"\beducation\b", r"\bacademic\b", r"\bqualification\b"],
    "skills": [r"\bskills\b", r"\btechnical skills\b", r"\bcompetencies\b"],
    "projects": [r"\bprojects\b", r"\bportfolio\b"],
    "certifications": [r"\bcertifications\b", r"\blicenses\b", r"\bcertificates\b"],
    "awards": [r"\bawards\b", r"\bachievements\b", r"\bhonors\b"],
    "contact": [r"\bcontact\b", r"\bcontact information\b", r"\bcontacts\b"],
    "languages": [r"\blanguages\b", r"\blanguage\b"],
    "publications": [r"\bpublications\b"],
    "interests": [r"\binterests\b", r"\bhobbies\b"],
}

SECTION_ORDER = [
    "contact",
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "awards",
    "languages",
    "publications",
    "interests",
]


def cv_parse_sections(content: str) -> dict[str, Any]:
    """
    Heuristik sederhana untuk memetakan bagian-bagian CV dari teks.
    Mengembalikan 'sections' (dict: nama -> teks) dan metadata ringkas.
    """
    text = content or ""
    # Normalisasi
    norm = re.sub(r"[ \t]+", " ", text)
    lines = [ln.strip() for ln in norm.splitlines()]

    # Buat pola gabungan untuk tiap section
    compiled = {
        key: re.compile("|".join(pats), flags=re.IGNORECASE)
        for key, pats in SECTION_ALIASES.items()
    }

    # Cari indeks baris yang cocok sebagai header section
    headers: list[tuple[int, str]] = []
    for idx, ln in enumerate(lines):
        # header heuristik: baris pendek, semua huruf/angka/spasi, tanpa banyak tanda baca
        if 1 <= len(ln) <= 80:
            for key, creg in compiled.items():
                if creg.search(ln):
                    headers.append((idx, key))
                    break

    # Sort by line index
    headers.sort(key=lambda x: x[0])

    # Potong teks berdasarkan header
    sections: dict[str, str] = {}
    if not headers:
        # Fallback: taruh semua ke "summary" jika tak terdeteksi
        sections["summary"] = text.strip()
    else:
        for i, (idx, key) in enumerate(headers):
            start = idx + 1  # konten mulai setelah header
            end = headers[i + 1][0] if i + 1 < len(headers) else len(lines)
            chunk = "\n".join(lines[start:end]).strip()
            # Gabungkan jika section muncul beberapa kali
            if key in sections and chunk:
                sections[key] = (sections[key] + "\n\n" + chunk).strip()
            elif chunk:
                sections[key] = chunk

    # Urutkan output sections mengikuti SECTION_ORDER
    ordered_sections: dict[str, str] = {}
    seen = set()
    for key in SECTION_ORDER:
        if key in sections:
            ordered_sections[key] = sections[key]
            seen.add(key)
    # Tambahkan sisanya (jika ada)
    for key, val in sections.items():
        if key not in seen:
            ordered_sections[key] = val

    tokens_estimate = max(1, len(text.split()))
    present = list(ordered_sections.keys())

    return {
        "success": True,
        "sections": ordered_sections,
        "present_sections": present,
        "missing_sections": [k for k in SECTION_ORDER if k not in ordered_sections],
        "tokens_estimate": tokens_estimate,
    }