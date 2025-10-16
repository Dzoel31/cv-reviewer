from __future__ import annotations

import re
from typing import Any, Iterable


def _tokenize_simple(s: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9\+\#\.]{2,}", s.lower())


def _keywords_from_text(s: str, min_len: int = 3) -> set[str]:
    toks = _tokenize_simple(s)
    return {t for t in toks if len(t) >= min_len}


def score_cv(
    sections: dict[str, str],
    job_description: str | None = None,
    target_role: str | None = None,
) -> dict[str, Any]:
    """
    Skor heuristik sederhana untuk CV:
    - Kelengkapan section
    - Kepadatan kata kunci (opsional) berdasar job description
    - Panjang wajar (tidak terlalu pendek)
    Hasil: skor 0-100 + rincian.
    """
    score = 0
    details: dict[str, Any] = {}

    # 1) Kelengkapan section
    required = ["summary", "experience", "education", "skills"]
    present = [k for k in required if k in sections and sections[k].strip()]
    completeness = round(100 * len(present) / len(required))
    score += round(0.45 * completeness)  # bobot 45%
    details["required_sections_present"] = present
    details["required_sections_missing"] = [k for k in required if k not in present]
    details["section_completeness_pct"] = completeness

    # 2) Panjang konten (kasar)
    total_tokens = sum(len(sec.split()) for sec in sections.values())
    # Asumsi ideal min 200 kata
    length_score = 100 if total_tokens >= 200 else int((total_tokens / 200) * 100)
    length_score = max(0, min(100, length_score))
    score += round(0.20 * length_score)  # bobot 20%
    details["length_tokens"] = total_tokens
    details["length_score_pct"] = length_score

    # 3) Kecocokan kata kunci dari Job Description (opsional)
    jd_score = 0
    jd_hits: list[str] = []
    if job_description:
        jd_kw = _keywords_from_text(job_description)
        cv_kw = _keywords_from_text(" ".join(sections.values()))
        if jd_kw:
            overlap = jd_kw & cv_kw
            recall = len(overlap) / len(jd_kw)
            jd_score = int(recall * 100)
            details["jd_keywords_overlap"] = sorted(list(overlap))
            details["jd_keywords_coverage_pct"] = jd_score
        else:
            details["jd_keywords_coverage_pct"] = 0
    score += round(0.25 * jd_score)  # bobot 25%

    # 4) Struktur & kebersihan dasar (judul, bullet, tanggal)
    structure_score = 0
    bullets = sum(
        sections.get(k, "").count("\n-") + sections.get(k, "").count("•")
        for k in sections
    )
    has_years = bool(re.search(r"\b(20\d{2}|19\d{2})\b", " ".join(sections.values())))
    if bullets >= 5:
        structure_score += 50
    if has_years:
        structure_score += 50
    score += round(0.10 * structure_score)  # bobot 10%
    details["structure_bullets_count"] = bullets
    details["structure_has_years"] = has_years
    details["structure_score_pct"] = structure_score

    final = max(0, min(100, score))
    return {
        "success": True,
        "overall_score": final,
        "breakdown": details,
        "notes": (
            "Skor berbasis heuristik ringan. Gunakan sebagai indikasi cepat, "
            "perkaya dengan analisis LLM untuk saran spesifik."
        ),
        "target_role": target_role,
    }
