import os
from random import random
import pytest

import lxml.html
import pandas as pd

import run
import constants

def _test_frame_equal(fn, expected):
    try:
        df = pd.read_csv(fn)
        pd.testing.assert_frame_equal(df, expected)
    finally:
        if os.path.isfile(fn):
            os.remove(fn)


def test_load_csv(input_urls_filename, input_urls):
    df = run.load_csv(input_urls_filename)
    pd.testing.assert_frame_equal(df, input_urls)


def test_load_csv_missing():
    # by default, missing_ok = False and an error is thrown
    with pytest.raises(RuntimeError):
        run.load_csv(None)

    # if a file is passed, but it's not found, that's always an error
    with pytest.raises(RuntimeError):
        run.load_csv('this file does not exist')
    with pytest.raises(RuntimeError):
        run.load_csv('this file does not exist', missing_ok=True)

    # when allowed, None is returned
    df = run.load_csv(None, missing_ok=True)
    assert df is None


def test_get_links_no_nav(page_xml_tree):
    links = run.get_links(page_xml_tree)
    assert len(links) == 24


def test_get_links_with_nav(page_xml_tree):
    links = run.get_links(page_xml_tree, include_nav_links=True)
    assert len(links) == 36


def test_clean_input_url_data():
    df = pd.DataFrame()

    # test truth values
    df['include_nav_links'] = [1, 'True', 'true', '1', 'yes', 'Yes']
    run.clean_input_url_data(df)
    assert df['include_nav_links'].sum() == len(df)

    # test false values
    df['include_nav_links'] = [0, 'False', 'false', '0', 'no', 'No']
    run.clean_input_url_data(df)
    assert df['include_nav_links'].sum() == 0


def test_validate_input_url_data(input_urls):
    # test data is valid
    run.validate_input_url_data(input_urls)
    # make it invalid and verify an error occurs
    input_urls.columns = ['foo', 'bar', 'baz']
    with pytest.raises(RuntimeError):
        run.validate_input_url_data(input_urls)


def test_parse_link():
    link = lxml.html.HtmlElement(
        origin='https://www.website.com',
        href='https://www.website.com/path?arg=val',
        text=' Hello  World ',
    )
    link.text = ' Hello\t  World '
    parsed = {'link': '/path?arg=val'}
    expected = {
        'link': '/path?arg=val',
        'full_link': 'https://www.website.com/path?arg=val',
        'link_text': 'hello world',
    }
    # extra assertion for the 'class' property (due to reserved python keyword)
    random_class_name = str(int(random()))
    link.set('link_class_name', random_class_name)
    expected['link_class_name'] = random_class_name

    run.parse_link(link, parsed)
    assert parsed == expected


@pytest.mark.parametrize(['link', 'expected'], [
    ('https://www.google.com', 'www.google.com'),
    ('https://www.google.com/path?arg=val', 'www.google.com')
])
def test_get_site_domain(link, expected):
    assert run.get_site_domain(link) == expected


def test_process_item(browser):
    item = pd.Series({
        'url': 'https://webscraper.io/test-sites/e-commerce/static',
        'label': 'testing',
        'domain': 'www.website.com'
    })
    response = run.process_item(item, browser)
    assert len(response['links']) > 0
    assert response['failure_reason'] == ''


def test_process_item_error(browser):
    item = pd.Series({'url': 'foo', 'label': 'label', 'domain': 'www.website.com'})
    response = run.process_item(item, browser)
    assert response['links'] == []
    assert len(response['failure_reason']) > 0


def test_process_page(page_xml_tree, processed_page_records):
    row = pd.Series({
        'url': 'https://www.website.com',
        'label': 'label',
        'domain': 'www.website.com',
        'include_nav_links': False
    })
    result = run.parse_page_links(row, page_xml_tree)
    # import pdb; pdb.set_trace()
    with open('test/fixtures/processed_page.json', 'w') as fp:
        import json
        json.dump(result, fp, indent=4)
    assert result == processed_page_records


def test_handle_failures(failures):
    run.handle_failures(failures['input'])
    _test_frame_equal('data/failed_%s.csv' % run.RUN_TIMESTAMP, failures['expected'])


def test_handle_failures_empty():
    run.handle_failures([])
    _test_frame_equal('data/failed_%s.csv' % run.RUN_TIMESTAMP, pd.DataFrame([], columns=['failure_reason', 'url']))


def test_find_new_links(find_new_links_data):
    cur_links, all_links, new_links_expected, all_links_expected = find_new_links_data
    new_links, all_links = run.find_new_links(cur_links, all_links)
    pd.testing.assert_frame_equal(all_links, all_links_expected)
    pd.testing.assert_frame_equal(new_links, new_links_expected)


def test_find_new_links_empty_current(find_new_links_data):
    _, all_links, _, _ = find_new_links_data
    prev_all_links = all_links.copy()
    new_links, all_links = run.find_new_links(None, all_links)
    assert len(new_links) == 0
    pd.testing.assert_frame_equal(all_links, prev_all_links)

def test_find_new_links_empty_previous(find_new_links_data):
    cur_links, _, _, _ = find_new_links_data
    new_links, all_links = run.find_new_links(cur_links, None)
    pd.testing.assert_frame_equal(new_links.drop('defined_change', axis=1), all_links)
    assert (new_links['defined_change'] == 'new link').sum() == len(cur_links)


def test_find_new_links_empty_both():
    new_links, all_links = run.find_new_links(None, None)
    assert len(new_links) == 0
    assert all(new_links.columns == constants.NEW_LINKS_FILE_HEADER)
    assert len(all_links) == 0
    assert all(all_links.columns == constants.ALL_LINKS_FILE_HEADER)
