from dotenv import load_dotenv
load_dotenv(dotenv_path='.env', override=True)
from services.serpapi_client import SerpApiClient

c = SerpApiClient()
print('SERPAPI_present:', bool(c.api_key))
print('\n--- running test_fetch_once ---')
try:
    c.test_fetch_once(q='software engineer')
except Exception as e:
    print('test_fetch_once exception:', type(e).__name__, e)

print('\n--- running search_page (page1) ---')
try:
    res, meta = c.search_page(query='software engineer', next_page_token=None, num=10)
    print('search_page status/meta:', meta)
    print('first_item_keys:', list(res[0].keys()) if len(res)>0 else 'no items')
except Exception as e:
    print('search_page exception:', type(e).__name__, e)

print('\n--- trying next page if token provided ---')
try:
    token = meta.get('next_page_token') if isinstance(meta, dict) else None
    print('token from page1:', token)
    if token:
        res2, meta2 = c.search_page(query='software engineer', next_page_token=token, num=10)
        print('page2 meta:', meta2)
        print('page2 count:', len(res2))
except Exception as e:
    print('next page exception:', type(e).__name__, e)
