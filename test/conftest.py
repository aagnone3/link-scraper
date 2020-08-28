import os
import json
import pytest

import pandas as pd
from lxml import html
from selenium import webdriver

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(scope="session")
def input_urls_filename():
    return os.path.join(FIXTURES_DIR, "input_urls.csv")


@pytest.fixture(scope="function")
def failed_urls():
    return pd.read_csv(os.path.join(FIXTURES_DIR, "failed_urls.csv"))


@pytest.fixture(scope="function")
def input_urls(input_urls_filename):
    return pd.read_csv(input_urls_filename)


@pytest.fixture(scope="function")
def links():
    return pd.read_csv(os.path.join(FIXTURES_DIR, "links.csv"))


@pytest.fixture(scope="function")
def page_content():
    with open(os.path.join(FIXTURES_DIR, "page.html"), "r") as fp:
        content = fp.read().strip()
    return content


@pytest.fixture(scope="function")
def page_xml_tree(page_content):
    return html.fromstring(page_content)


@pytest.fixture(scope="function")
def processed_page_records():
    with open(os.path.join(FIXTURES_DIR, "processed_page.json"), "r") as fp:
        content = json.load(fp)
    return content


@pytest.fixture(scope="session")
def browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)


@pytest.fixture(scope="session")
def failures():
    df_input = pd.DataFrame(
        [
            {
                "links": [],
                "failed": 1,
                "url": "https://www.website.com",
                "failure_reason": "URL navigation",
            },
            {
                "links": [],
                "failed": 1,
                "url": "https://www.website.com",
                "failure_reason": "HTML parse failure",
            },
            {
                "links": [],
                "failed": 1,
                "url": "https://www.website.com",
                "failure_reason": "Unknown",
            },
        ]
    )
    df_expected = pd.DataFrame(
        [
            {"url": "https://www.website.com", "failure_reason": "URL navigation"},
            {"url": "https://www.website.com", "failure_reason": "HTML parse failure"},
            {"url": "https://www.website.com", "failure_reason": "Unknown"},
        ]
    )
    return {"input": df_input, "expected": df_expected}


@pytest.fixture(scope="function")
def find_new_links_data():
    cur_links = pd.DataFrame(
        [
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "#id",
                "full_link": "https://www.website.com#id",
                "link_text": "foo",
                "link_class_name": "class",
            },
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "/path",
                "full_link": "https://www.website.com/path",
                "link_text": "changed_foo",
                "link_class_name": "class",
            },
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "/other",
                "full_link": "https://www.website.com/other",
                "link_text": "other_foo",
                "link_class_name": "class",
            },
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "#id2",
                "full_link": "https://www.website.com#id2",
                "link_text": "bar",
                "link_class_name": "class",
            },
        ]
    )
    all_links = pd.DataFrame(
        [
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "/path",
                "full_link": "https://www.website.com/path",
                "link_text": "path_foo",
                "link_class_name": "class",
            },
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "/other",
                "full_link": "https://www.website.com/other",
                "link_text": "other_foo",
                "link_class_name": "class",
            },
        ]
    )
    new_links_expected = pd.DataFrame(
        [
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "/path",
                "full_link": "https://www.website.com/path",
                "link_text": "changed_foo",
                "link_class_name": "class",
                "defined_change": "text change",
            },
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "#id",
                "full_link": "https://www.website.com#id",
                "link_text": "foo",
                "link_class_name": "class",
                "defined_change": "new link",
            },
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "#id2",
                "full_link": "https://www.website.com#id2",
                "link_text": "bar",
                "link_class_name": "class",
                "defined_change": "new link",
            },
        ]
    )
    all_links_expected = pd.DataFrame(
        [
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "/path",
                "full_link": "https://www.website.com/path",
                "link_text": "changed_foo",
                "link_class_name": "class",
            },
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "/other",
                "full_link": "https://www.website.com/other",
                "link_text": "other_foo",
                "link_class_name": "class",
            },
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "#id",
                "full_link": "https://www.website.com#id",
                "link_text": "foo",
                "link_class_name": "class",
            },
            {
                "url": "website.com",
                "label": "label",
                "domain": "www.website.com",
                "link": "#id2",
                "full_link": "https://www.website.com#id2",
                "link_text": "bar",
                "link_class_name": "class",
            },
        ]
    )
    return cur_links, all_links, new_links_expected, all_links_expected
