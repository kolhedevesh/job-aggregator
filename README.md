# Job Aggregator (AI-Ready Job Search Tool)

A Python-based job aggregation web application that collects job listings from multiple sources, normalizes them into a structured format, and displays them through an interactive Streamlit interface.

The platform supports filtering, pagination, and optional LLM-based summarization of job descriptions.

---

## Live Demo

https://ai-job-aggregator.streamlit.app/

---

## Features

- Search jobs by **title or keywords**
- Filter by **location**
- Filter by **experience level**
- Filter by **employment type**
- Pagination for browsing large result sets
- Job listings normalized into a structured format
- Optional **LLM-powered job description summarization**
- Direct **Apply links** to job postings
- Clean and interactive **Streamlit UI**

---

## Tech Stack

Backend
- Python

Frontend
- Streamlit

Data Source
- SerpAPI (Google Jobs API)

AI / LLM
- Ollama (optional local LLM integration)

Libraries
- requests
- python-dotenv
- typing-extensions

Deployment
- Streamlit Community Cloud

---

## Architecture

User  
↓  
Streamlit UI (app.py)  
↓  
SerpAPI Client  
↓  
Job Normalizer  
↓  
Optional LLM summarization (Ollama)  
↓  
Job Cards UI  

---

## Project Structure

job-aggregator
│
├── app.py                 # Streamlit UI
├── models
│   └── job.py             # Job data model
│
├── services
│   ├── serpapi_client.py  # API integration
│   ├── job_normalizer.py  # Data normalization
│   └── llm_service.py     # LLM summarization
│
├── utils
│   └── validators.py
│
├── scripts
│   ├── debug_fetch.py
│   └── check_apply.py
│
├── requirements.txt
└── README.md

---

## Setup (Local Development)

Clone the repository

git clone https://github.com/kolhedevesh/job-aggregator.git
cd job-aggregator

Create a virtual environment

python -m venv .venv
source .venv/bin/activate

Install dependencies

pip install -r requirements.txt

Create environment variables

cp .env.example .env

Add your API key

SERPAPI_API_KEY=your_key_here

Run the application

streamlit run app.py

---

## Future Improvements

- Resume upload + AI job matching
- Semantic search for job descriptions
- Skill extraction from job listings
- Email job alerts
- Multi-source job aggregation (LinkedIn, Indeed, Naukri)

---

## Author

Devesh Kolhe  
IIT Delhi | AI Product & Systems Enthusiast  

GitHub  
https://github.com/kolhedevesh
