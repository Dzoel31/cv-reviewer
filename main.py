from __future__ import annotations

import streamlit as st

from agent_lapangan.tools.read_pdf import read_pdf
from agent_lapangan.tools.cv_parser import cv_parse_sections
from agent_lapangan.tools.cv_scoring import score_cv
from agent_lapangan.tools.job_recommendation import recommend_jobs


def main():
    st.set_page_config(page_title="CV Reviewer", page_icon="📄", layout="centered")
    st.title("📄 CV Reviewer — Kernel Debug")
    st.write("Upload CV PDF, lalu dapatkan parsing section, skor heuristik, dan rekomendasi pekerjaan.")

    with st.sidebar:
        st.header("Pengaturan")
        jd = st.text_area("Job Description (opsional)", height=150, placeholder="Tempelkan JD untuk penilaian kecocokan kata kunci…")
        target_role = st.text_input("Target Role (opsional)", placeholder="Contoh: Data Analyst")
        col_a, col_b = st.columns(2)
        with col_a:
            page_start = st.number_input("Halaman awal", min_value=1, value=1, step=1)
        with col_b:
            page_end_opt = st.text_input("Halaman akhir (kosong=hingga akhir)", value="")
        page_end = int(page_end_opt) if page_end_opt.strip().isdigit() else None

    f = st.file_uploader("Upload CV (PDF)", type=["pdf"])
    if f is None:
        st.info("Silakan unggah file PDF CV Anda untuk mulai.")
        return

    # Simpan ke buffer sementara agar kompatibel dengan read_pdf (butuh path). Streamlit memberi BytesIO.
    tmp_path = st.session_state.get("_tmp_pdf_path")
    if not tmp_path:
        import tempfile
        import os

        fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        st.session_state["_tmp_pdf_path"] = tmp_path
    with open(tmp_path, "wb") as w:
        w.write(f.read())

    with st.spinner("Membaca PDF…"):
        out = read_pdf(tmp_path, page_start=page_start, page_end=page_end)
    if not out.get("success"):
        st.error(out.get("error", "Gagal membaca PDF"))
        st.stop()

    st.success(f"Berhasil mengekstrak {out['extracted_range'][1] - out['extracted_range'][0] + 1} halaman (dari {out['total_pages']} halaman total)")
    if out.get("empty_pages"):
        st.warning(f"Halaman tanpa teks terdeteksi: {out['empty_pages']}. {out['note']}")

    content = out.get("content", "").strip()
    with st.expander("Lihat teks CV (ekstraksi)"):
        st.text_area("CV Text", value=content, height=250)

    with st.spinner("Memetakan sections…"):
        parsed = cv_parse_sections(content)
    if not parsed.get("success"):
        st.error("Gagal memetakan sections.")
        st.stop()

    sections = parsed["sections"]
    st.subheader("Sections Terdeteksi")
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Ada:** " + ", ".join(parsed["present_sections"]))
    with cols[1]:
        missing = parsed["missing_sections"]
        if missing:
            st.markdown("**Kurang:** " + ", ".join(missing))
        else:
            st.markdown("**Kurang:** -")

    with st.expander("Detail per section"):
        for name, val in sections.items():
            st.markdown(f"### {name.title()}")
            st.text(val[:4000])

    with st.spinner("Menghitung skor heuristik…"):
        scored = score_cv(sections, job_description=jd or None, target_role=target_role or None)
    if not scored.get("success"):
        st.error("Gagal menghitung skor.")
        st.stop()

    st.subheader("Skor CV")
    st.metric("Overall Score", f"{scored['overall_score']}/100")
    bd = scored["breakdown"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Section Completeness", f"{bd.get('section_completeness_pct', 0)}%")
    c2.metric("Length Adequacy", f"{bd.get('length_score_pct', 0)}%")
    c3.metric("JD Keywords Coverage", f"{bd.get('jd_keywords_coverage_pct', 0)}%")

    with st.expander("Rincian struktur & kata kunci"):
        st.json(bd)

    st.subheader("Rekomendasi Pekerjaan")
    recs_out = recommend_jobs(sections)
    recs = recs_out.get("recommendations", []) if isinstance(recs_out, dict) else []
    for r in recs:
        st.markdown(f"- **{r['title']}** — {r['reason']}")


if __name__ == "__main__":
    main()
