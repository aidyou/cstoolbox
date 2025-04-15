import asyncio
from search_extractor import SearchExtractor
import json


async def test_bing_search():
    extractor = SearchExtractor("bing")
    results = await extractor.search("光线传媒", page=1, number=20)
    if results:
        results = json.loads(results)

        print(f"Found {len(results)} results:")
        for result in results:
            print(f"Site: {result.get('site_name','')}")
            print(f"Title: {result.get('title','')}")
            print(f"URL: {result.get('url','')}")
            print(f"Summary: {result.get('summary','')}")
            print(f"Publish Date: {result.get('publish_date','')}")
            print("\n")
    else:
        print("No results found")


if __name__ == "__main__":
    asyncio.run(test_bing_search())
