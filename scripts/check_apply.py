from services.serpapi_client import SerpApiClient

c = SerpApiClient()
res, meta = c.search_page(query='software engineer', next_page_token=None, num=10)
print('meta:', meta)
if res:
    first = res[0]
    print('first keys:', list(first.keys()))
    print('first apply_link:', first.get('apply_link') or first.get('url') or first.get('jobUrl'))
    print('apply_options field (raw):')
    print(first.get('apply_options'))
    # normalize and inspect Job.apply_link
    from services.job_normalizer import normalize_job
    job = normalize_job(first)
    print('normalized apply_link:', job.apply_link)
else:
    print('no results')
