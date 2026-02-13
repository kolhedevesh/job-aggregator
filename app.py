from typing import List, Optional
import os
import math

import streamlit as st
from dotenv import load_dotenv

from services.serpapi_client import cached_search, cached_search_page
from services.job_normalizer import normalize_jobs
from services.llm_service import cached_summarize, cached_summarize_description
from models.job import Job


load_dotenv()


def render_job_card(job: Job, summary: Optional[str] = None) -> None:
    st.markdown("---")
    cols = st.columns([6, 2])
    with cols[0]:
        st.subheader(f"{job.job_title}")
        st.write(f"**{job.company_name}** • {job.location}")
        # Short description (already summarized/truncated upstream)
        desc = summary or job.short_description
        st.write(desc)
        # skills display removed; summarize only
    with cols[1]:
        if job.apply_link:
            # Open in new tab
            st.markdown(f'<a href="{job.apply_link}" target="_blank" rel="noopener noreferrer">Apply</a>', unsafe_allow_html=True)


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
                # Build deterministic q string (mirrors SerpApiClient behavior)
                parts = []
                if query and query.strip():
                    parts.append(query.strip())
                if remote:
                    parts.append(remote)
                if experience:
                    parts.append(experience)
                if employment:
                    parts.append(employment)
                if tech_stack:
                    parts.append(tech_stack)
                q_final = " ".join(parts).strip()

                # Server-side pagination: fetch only the current page
                page = int(st.session_state.page)
                page = max(1, page)

                # Manage page tokens in session_state to use SerpAPI next_page_token pagination
                if "page_tokens" not in st.session_state or submit:
                    st.session_state.page_tokens = {1: None}

                # token for this page (None for page 1)
                token_for_page = st.session_state.page_tokens.get(page)

                raw_page, meta = cached_search_page(
                    api_key=api_key,
                    q=q_final,
                    location=location.strip() if location and len(location.strip()) > 1 and not location.strip().isdigit() else None,
                    remote=remote or None,
                    experience_level=experience or None,
                    employment_type=employment or None,
                    tech_stack=tech_stack or None,
                    next_page_token=token_for_page,
                    num=page_size,
                )

                # store token for next page (page+1) if provided by provider
                next_token = meta.get("next_page_token") if isinstance(meta, dict) else None
                if next_token:
                    st.session_state.page_tokens[page + 1] = next_token

                # expose meta for debug UI
                results_meta = meta

            jobs: List[Job] = normalize_jobs(raw_page)

            if not jobs:
                st.warning("No results found on this page.")
            # Jobs returned on this page
            jobs_returned = results_meta.get("jobs_returned") if isinstance(results_meta, dict) else len(jobs)

            if debug:
                st.info("Debug: SerpAPI parameters and counts")
                st.write({"final_query": q_final, "start": start, "jobs_returned": jobs_returned})

            st.success(f"Found {jobs_returned} jobs on this page (Page {page}).")

            # Pagination controls with reliable callbacks
            def _prev():
                if st.session_state.page > 1:
                    st.session_state.page = st.session_state.page - 1

            def _next():
                # Only advance if this page was full (likely more results)
                if jobs_returned >= page_size:
                    st.session_state.page = st.session_state.page + 1

            cols = st.columns([1, 6, 1])
            with cols[0]:
                st.button("Prev", on_click=_prev, key="prev_btn")
            with cols[1]:
                st.write(f"Page {page}")
            with cols[2]:
                st.button("Next", on_click=_next, key="next_btn")

            ollama_host = os.getenv("OLLAMA_HOST")
            ollama_model = os.getenv("OLLAMA_MODEL")

            # Prepare summaries for each job (store in Job.summary)
            for job in jobs:
                if use_llm:
                    try:
                        s = cached_summarize_description(ollama_host, ollama_model, job.short_description)
                        if s:
                            job.summary = s.strip()
                        else:
                            job.summary = job.short_description[:500].strip()
                    except Exception:
                        job.summary = job.short_description[:500].strip()
                else:
                    job.summary = job.short_description[:500].strip()

            for job in jobs:
                render_job_card(job, summary=job.summary)

        except Exception as exc:
            st.error(f"Error: {exc}")


if __name__ == "__main__":
    main()
