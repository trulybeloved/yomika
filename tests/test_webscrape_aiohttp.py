from yomika.webscrape_aiohttp import webscrape_aiohttp
from yomika.processors import run_async, scrape_url_list_async
from yomika.classes import ScrapedResponse

def test_scrape_url():

    with open('tests/samples/example_com_html.txt', 'r', encoding='utf-8') as sample_file:
        expected_html = sample_file.read()

    scrape_result: ScrapedResponse = run_async(webscrape_aiohttp('https://example.com'))
    assert scrape_result.text == expected_html

def test_scrape_url_list():

    with open('tests/samples/example_com_html.txt', 'r', encoding='utf-8') as sample_file:
        expected_html = sample_file.read()

    url_list = [
        "http://example.com",
        "http://example.com",
        "http://example.com",
        "http://example.com",
        "http://example.com",
        "http://example.com",
        "http://example.com",
        "http://example.com",
        "http://example.com",
        "http://example.com",
        "http://example.com",
        "http://example.com"
    ]
    results = scrape_url_list_async(url_list)

    for scrape_result in results:
        assert scrape_result.text == expected_html

