from yomika.webscrape_requests import webscrape_requests

def test_add():

    with open('tests/samples/example_com_html.txt', 'r', encoding='utf-8') as sample_file:
        expected_html = sample_file.read()

    dom_contents = webscrape_requests('https://example.com')
    assert dom_contents.text == expected_html