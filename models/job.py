from dataclasses import dataclass


@dataclass
class Job:
    company_name: str
    job_title: str
    location: str
    short_description: str
    employment_type: str
    source_site: str
    apply_link: str
