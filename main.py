import aiohttp
from yomika.webscrape_aiohttp import webscrape_aiohttp


# Example usage
async def example_usage():
    # Create a connection pool to be used across multiple requests
    async with aiohttp.ClientSession() as session:
        # Single request
        result = await webscrape_aiohttp(
            url="https://example.com",
            session=session
        )
        print(f"Status: {result.status_code}, Size: {len(result.text)} bytes")

        # Multiple concurrent requests with the same session
        urls = ["https://example.com", "https://httpbin.org", "https://python.org"]
        tasks = [webscrape_aiohttp(url=url, session=session) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error with {urls[i]}: {result}")
            else:
                print(f"{urls[i]} - Status: {result.status_code}, Size: {len(result.text)} bytes")


# Run the example
if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
