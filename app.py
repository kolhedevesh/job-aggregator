from typing import List, Optional
import os
import math

import streamlit as st
from dotenv import load_dotenv

from services.serpapi_client import cached_search
from services.job_normalizer import normalize_jobs
from services.llm_service import cached_summarize, cached_extract_skills
from models.job import Job
from utils.validators import clamp_limit


load_dotenv()


def render_job_card(job: Job, summary: Optional[str] = None, skills: Optional[str] = None) -> None:
    st.markdown("---")
    cols = st.columns([6, 2])
    with cols[0]:
        st.subheader(f"{job.job_title}")
        st.write(f"**{job.company_name}** • {job.location}")
        # Short description with 'Read more' for long text
        desc = summary or job.short_description
        if len(desc) > 200:
            st.write(desc[:197].rstrip() + "...")
            with st.expander("Read more"):
                st.write(desc)
        else:
            st.write(desc)
        if skills:
            st.caption(f"Skills: {skills}")
    with cols[1]:
        if job.apply_link:
            st.markdown(f"[Apply]({job.apply_link})")
        st.write(f"Source: {job.source_site}")


def main() -> None:
    st.title("Job Aggregator")
    st.write("Search multiple job boards and normalize results.")

    # Sidebar: search filters
    st.sidebar.header("Search filters")
    query = st.sidebar.text_input("Job title / keywords", value="Software Engineer")
    location = st.sidebar.text_input("Location", value="")
    remote = st.sidebar.selectbox("Work type", ["", "Remote", "Hybrid", "Onsite"])
    experience = st.sidebar.selectbox("Experience level", ["", "Intern", "Junior", "Mid", "Senior"])
    employment = st.sidebar.selectbox("Employment type", ["", "Full-time", "Contract"])
    tech_stack = st.sidebar.text_input("Tech stack (optional)")
    limit = st.sidebar.number_input("Max results", min_value=1, max_value=50, value=10)
    use_llm = st.sidebar.checkbox("Use local Ollama LLM for summaries and skills", value=False)
    debug = st.sidebar.checkbox("Show debug logs", value=False)
    submit = st.sidebar.button("Search")

    # Session state for pagination
    if "page" not in st.session_state:
        st.session_state.page = 1

    page_size = 10

    if submit:
        # Reset to first page on new search
        st.session_state.page = 1

    # Trigger search when submit or when page changes (pagination handled below)
    if submit or st.session_state.page:
        api_key = os.getenv("SERPAPI_API_KEY", "")
        try:
            st.info("Fetching jobs — this may take a few seconds.")
            with st.spinner("Fetching results..."):
                # Build params dict for diagnostics display
                params = {
                    "engine": "google_jobs",
                    "q": f"{query} {tech_stack}".strip(),
                    "api_key": api_key,
                    "num": 30,
                }
                if location and len(location.strip()) > 1 and not location.strip().isdigit():
                    params["location"] = location.strip()

                raw = cached_search(
                    api_key=api_key,
                    q=params["q"],
                    location=params.get("location"),
                    remote=remote or None,
                    experience_level=experience or None,
                    employment_type=employment or None,
                    tech_stack=tech_stack or None,
                    limit=clamp_limit(limit),
                )

            jobs: List[Job] = normalize_jobs(raw)

            if not jobs:
                st.warning("No results found.")
                return

            total = len(jobs)
            if debug:
                st.info("Debug: SerpAPI parameters and counts")
                st.write(params)
                st.write({"jobs_returned": total})
            total_pages = math.ceil(total / page_size)
            page = int(st.session_state.page)
            page = max(1, min(page, total_pages))

            start = (page - 1) * page_size
            end = start + page_size
            visible_jobs = jobs[start:end]

            st.success(f"Found {total} jobs — showing {start+1}-{min(end,total)}.")

            # Pagination controls
            cols = st.columns([1, 6, 1])
            with cols[0]:
                if st.button("Prev") and page > 1:
                    st.session_state.page = page - 1
                    st.experimental_rerun()
            with cols[1]:
                st.write(f"Page {page} / {total_pages}")
            with cols[2]:
                if st.button("Next") and page < total_pages:
                    st.session_state.page = page + 1
                    st.experimental_rerun()

            ollama_host = os.getenv("OLLAMA_HOST")
            ollama_model = os.getenv("OLLAMA_MODEL")

            for job in visible_jobs:
                summary = None
                skills = None
                if use_llm:
                    with st.spinner("Summarizing and extracting skills..."):
                        try:
                            summary = cached_summarize(ollama_host, ollama_model, job.short_description) or job.short_description
                            skills = cached_extract_skills(ollama_host, ollama_model, job.short_description) or ""
                        except Exception:
                            summary = job.short_description
                render_job_card(job, summary=summary, skills=skills)

        except Exception as exc:
            st.error(f"Error: {exc}")


if __name__ == "__main__":
    main()
