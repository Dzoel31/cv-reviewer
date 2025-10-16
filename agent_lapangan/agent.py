from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from google.adk.agents.llm_agent import Agent
from .tools.read_pdf import read_pdf
from .tools.cv_parser import cv_parse_sections
from .tools.cv_scoring import score_cv
from .tools.job_recommendation import recommend_jobs


class CVReviewRequest(BaseModel):
    file_path: str = Field(..., description="Path ke file PDF CV.")
    job_description: Optional[str] = Field(
        None, description="Deskripsi pekerjaan (opsional) untuk penilaian kecocokan."
    )
    target_role: Optional[str] = Field(
        None, description="Peran/posisi target kandidat (opsional)."
    )
    page_start: Optional[int] = Field(
        None, description="Batas halaman awal (1-based, opsional)."
    )
    page_end: Optional[int] = Field(
        None, description="Batas halaman akhir (1-based, opsional)."
    )
    language: Optional[str] = Field(
        default="id",
        description="Bahasa keluaran review (id/en). Default: id.",
    )


class CVReviewResponse(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    ats_keywords_coverage_pct: int = Field(..., ge=0, le=100)
    section_completeness_pct: int = Field(..., ge=0, le=100)
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    risks_or_red_flags: list[str]
    sections_present: list[str]
    sections_missing: list[str]
    tokens_estimate: int
    meta: dict[str, Any] = Field(default_factory=dict)


INSTRUCTION = """\
Anda adalah asisten spesialis review Curriculum Vitae (CV).
Tujuan Anda:
1) Ekstrak teks CV dari PDF menggunakan tool read_pdf.
2) Pemetaan bagian-bagian CV menggunakan tool cv_parse_sections.
3) Skor & analisis heuristik menggunakan tool score_cv (termasuk kecocokan dengan Job Description jika tersedia).
4) Hasilkan review terstruktur dan rekomendasi yang spesifik, ringkas, dan dapat ditindaklanjuti.
5) Jika konten kosong atau CV hasil scan (halaman kosong), minta pengguna menjalankan OCR atau memberi versi PDF bertipe teks.

Pedoman penulisan:
- Gunakan bahasa sesuai permintaan (field language), default Bahasa Indonesia.
- Berikan umpan balik yang jelas, contoh konkret perbaikan, dan urutkan dalam bullet.
- Fokus pada kejelasan pencapaian, kuantifikasi dampak, relevansi skills dengan peran target, dan keterbacaan.

Langkah eksekusi (implicit):
- Panggil read_pdf(file_path, page_start, page_end).
- Jika read_pdf sukses, panggil cv_parse_sections(content).
- Panggil score_cv(sections, job_description, target_role).
- Sintesis hasil ke Strengths, Weaknesses, Recommendations, Red Flags, nilai skor, dan coverage ATS keywords (jika JD ada).
"""


root_agent = Agent(
    model="gemini-2.5-flash",
    name="cv_review_agent",
    instruction=INSTRUCTION,
    description="Agent untuk me-review CV PDF secara terstruktur dan memberi rekomendasi perbaikan.",
    input_schema=CVReviewRequest,
    output_schema=CVReviewResponse,
    tools=[read_pdf, cv_parse_sections, score_cv, recommend_jobs],
)