from __future__ import annotations

from typing import Any


def recommend_jobs(sections: dict[str, str], top_k: int = 5) -> dict[str, Any]:
    """
    Rekomendasi pekerjaan sederhana berbasis keyword yang terdeteksi di CV.
    Input:
      - sections: hasil parsing CV (nama_section -> teks)
      - top_k: jumlah rekomendasi maksimum
    Output dict:
      { success: bool, recommendations: [ {title, reason, matched_skills} ] }
    """
    try:
        text = " ".join(sections.values()).lower()
    except Exception:
        text = ""

    mapping = {
        "data": [
            "python",
            "pandas",
            "numpy",
            "sql",
            "power bi",
            "tableau",
            "machine learning",
        ],
        "backend": ["python", "django", "flask", "fastapi", "rest", "postgres", "mysql"],
        "frontend": ["html", "css", "javascript", "react", "vue", "typescript"],
        "mobile": ["kotlin", "swift", "flutter", "react native"],
        "cloud_devops": ["docker", "kubernetes", "aws", "gcp", "azure", "ci/cd"],
        "ai": ["pytorch", "tensorflow", "llm", "nlp", "computer vision"],
    }

    domain_hits: dict[str, set[str]] = {k: set() for k in mapping}
    for domain, kws in mapping.items():
        for kw in kws:
            if kw in text:
                domain_hits[domain].add(kw)

    suggestions: list[dict[str, Any]] = []
    ranked = sorted(domain_hits.items(), key=lambda kv: len(kv[1]), reverse=True)
    for domain, hits in ranked:
        if not hits:
            continue
        if domain == "data":
            title = "Data Analyst / Data Scientist (Junior)"
        elif domain == "backend":
            title = "Backend Engineer (Python)"
        elif domain == "frontend":
            title = "Frontend Engineer"
        elif domain == "mobile":
            title = "Mobile Developer"
        elif domain == "cloud_devops":
            title = "Cloud/DevOps Engineer (Junior)"
        elif domain == "ai":
            title = "Machine Learning Engineer / AI Engineer"
        else:
            title = f"Role terkait {domain}"
        suggestions.append(
            {
                "title": title,
                "reason": f"Cocok karena ditemukan skill: {', '.join(sorted(hits))}",
                "matched_skills": sorted(hits),
            }
        )

    if not suggestions:
        suggestions.append(
            {
                "title": "Generalist Software/IT Role",
                "reason": "Belum terdeteksi skill spesifik yang dominan. Pertimbangkan memperkaya bagian Skills dan Projects.",
                "matched_skills": [],
            }
        )

    return {"success": True, "recommendations": suggestions[: max(1, int(top_k))]}
