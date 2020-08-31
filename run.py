"""
"""
import argparse
import os
from datetime import datetime
from typing import Optional, List
from urllib.parse import urlparse

import lxml.html
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver

import constants
from log import log


RUN_TIMESTAMP = datetime.now().isoformat().replace(':', '')


def is_truthy(value: any) -> bool:
    if str(value).lower() in ('1', 'true', 'yes', 'y'):
        return True
    return False


def validate_input_url_data(input_urls: pd.DataFrame):
    if sorted(input_urls.columns) != ['include_nav_links', 'label', 'url']:
        raise RuntimeError('Expected fields url, label, and include_nav_links, got %s' % repr(input_urls.columns))


def clean_input_url_data(input_urls: pd.DataFrame) -> pd.DataFrame:
    # convert include_nav_links based on truthiness
    input_urls['include_nav_links'] = input_urls['include_nav_links'].map(is_truthy)
    return input_urls


def get_links(xml_tree: lxml.html.HtmlElement, include_nav_links: bool = False) -> List[lxml.html.HtmlElement]:
    if include_nav_links:
        return xml_tree.xpath(constants.XPathMatchers.LINKS)
    return xml_tree.xpath(constants.XPathMatchers.LINKS_NOT_UNDER_NAV)


def get_site_domain(site: str) -> str:
    netloc = urlparse(site).netloc
    # netloc is what we expect for well-formed links
    if netloc and len(netloc) > 0:
        return netloc
    # otherwise, this is a malformed/unmodeled link
    return ''


def parse_link(link: lxml.html.HtmlElement, parsed_info: dict):
    href = link.get('href')
    parsed_info['full_link'] = href
    parsed_info['link_class_name'] = link.get('link_class_name', '')
    parsed_info['link_text'] = link.text_content().lower().strip().replace('  ', ' ').replace('\n', '').replace('\t', '')


def process_item(row: pd.Series, browser: WebDriver) -> dict:
    # get current URL content
    try:
        log.info(f"Parsing links from {row['url']}")
        response = requests.get(row['url'])
        fail = response.status_code >= 400
        if not fail:
            browser.get(row['url'])
            import time
            time.sleep(3)
    except Exception:
        import traceback
        log.warning(f"Error navigating to url {row['url']}.")
        log.warning(traceback.format_exc(limit=5))
        fail = True

    if fail:
        return {
            'failed': True,
            'failure_reason': 'URL navigation',
            'url': row['url'],
            'links': []
        }
    return process_page(row, browser.page_source)


def process_page(row: pd.Series, page_source: str) -> dict:
    # try to parse the HTML. if something crazy went wrong, report that and continue
    try:
        page_xml = lxml.html.fromstring(page_source)
    except Exception:
        log.warning(f'Error parsing HTML content of {row["url"]}', exc_info=True)
        return {
            'failed': True,
            'failure_reason': 'HTML parse failure',
            'url': row['url'],
            'links': []
        }

    try:
        links = parse_page_links(row, page_xml)
    except Exception:
        log.warning(f'Unexpected error processing {row["url"]}', exc_info=True)
        return {
            'failed': True,
            'url': row['url'],
            'failure_reason': 'Unknown',
            'links': []
        }
    return links


def parse_page_links(row: pd.Series, page_xml: lxml.html.HtmlElement) -> dict:
    include_nav_links = row.get('include_nav_links')

    # get original href tags before making them absolute
    parsed_links = list()
    for link in get_links(page_xml, include_nav_links=include_nav_links):
        parsed_links.append({
            'link': link.get('href'),
            'url': row['url'],
            'domain': row['domain'],
            'label': row['label']
        })

    # make href tags absolute and finish parsing links
    page_xml.make_links_absolute(row['url'])
    for i, link in enumerate(get_links(page_xml, include_nav_links=include_nav_links)):
        parse_link(link, parsed_links[i])

    return {
        'failed': False,
        'failure_reason': '',
        'links': parsed_links
    }


def write_csv_dataframe(df, prefix):
    df.to_csv(f'data/{prefix}_{RUN_TIMESTAMP}.csv', index=False)


def handle_failures(failures: List[dict]):
    if len(failures) > 0:
        failures = pd.DataFrame(failures)
        failures.drop(['links', 'failed'], axis=1, inplace=True)
    else:
        failures = pd.DataFrame([], columns=['failure_reason', 'url'])
    write_csv_dataframe(failures, 'failed')


def handle_links(cur_links: pd.DataFrame, all_links: pd.DataFrame):
    new_links, all_links = find_new_links(cur_links, all_links)
    write_csv_dataframe(new_links, 'new_links')
    write_csv_dataframe(all_links, 'all_links')


def make_element_ids(df: pd.DataFrame) -> str:
    # form the "pre-id" of links as their domain and absolute href
    df['pre_id'] = df.apply(
        lambda row: f"{row['domain']}_{row['full_link']}",
        axis=1
    )
    # form a unique id by the ordering inwhich each item occurs in the pageq2""" ÇÇÇ """
    df['id'] = ''
    for pre_id, group in df.groupby('pre_id'):
        df.loc[group.index, 'id'] = [f"{pre_id}{number}" for number in range(len(group))]
    del df['pre_id']


def find_new_links(cur_links: pd.DataFrame, all_links: pd.DataFrame) -> List[pd.DataFrame]:

    # quick helper method (D.R.Y) for cleaning a DataFrame
    def clean(df, column_order):
        return (
            df
            .drop_duplicates()
            .loc[:, column_order]
            .reset_index(drop=True)
        )

    new_links = list()
    changes = list()

    no_cur_links = cur_links is None or len(cur_links) == 0
    no_all_links = all_links is None or len(all_links) == 0

    # if both are empty, both are empty :)
    if no_cur_links and no_all_links:
        log.info('No current or previous links.')
        return (
            pd.DataFrame([], columns=constants.NEW_LINKS_FILE_HEADER),
            pd.DataFrame([], columns=constants.ALL_LINKS_FILE_HEADER)
        )

    # if no previous links, all current links are new
    if no_all_links:
        log.info('No previous links to merge with.')
        all_links = clean(cur_links, constants.ALL_LINKS_FILE_HEADER)
        cur_links['defined_change'] = 'new link'
        return (
            clean(cur_links, constants.NEW_LINKS_FILE_HEADER),
            all_links
        )

    # if no current links, nothing is new
    if no_cur_links:
        log.info('No new links to consider.')
        return pd.DataFrame([], columns=constants.NEW_LINKS_FILE_HEADER), all_links

    # otherwise, parse current links to reconcile new ones
    all_links.fillna('', inplace=True)
    make_element_ids(cur_links)
    make_element_ids(all_links)
    for _, row in cur_links.iterrows():
        existing_link = all_links.loc[all_links['id'] == row['id']]
        if len(existing_link) == 0:
            # link is new
            item = dict(row)
            item['defined_change'] = 'new link'
            new_links.append(item)
        elif len(existing_link) > 1:
            # should never happen. if it does, then logic is broken to determine state changes of link text.
            raise RuntimeError("Multiple matches found for HTML (domain, link, order).")
        else:
            existing_link = existing_link.iloc[0]
            index = existing_link.name

            if row['link_text'] != existing_link['link_text']:
                # text has changed for same link
                item = dict(row)
                item['defined_change'] = 'text change'
                changes.append(item)
                log.info(f"Link {row['id']} changed text from {existing_link['link_text']} to {row['link_text']}.")
                all_links.loc[index, 'link_text'] = row['link_text']

    new_links = pd.DataFrame(new_links)
    changes = pd.DataFrame(changes, columns=constants.NEW_LINKS_FILE_HEADER).append(new_links)
    log.info(f'{len(changes)} changes detected.')

    all_links = all_links.append(new_links)

    return (
        clean(changes, constants.NEW_LINKS_FILE_HEADER),
        clean(all_links, constants.ALL_LINKS_FILE_HEADER)
    )


def get_browser(headless: bool = True) -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    if headless:
        log.info('Running browser as headless')
        options.add_argument('--headless')
    return webdriver.Chrome(options=options)


def main(browser: WebDriver, input_urls: pd.DataFrame, all_links: Optional[pd.DataFrame]):
    validate_input_url_data(input_urls)
    # validate_links(all_links)
    clean_input_url_data(input_urls)
    try:
        links = list()
        failed = list()
        log.info(f'Scraping {len(input_urls)} URLs.')
        input_urls['domain'] = input_urls['url'].map(get_site_domain)
        for _, row in input_urls.iterrows():
            result = process_item(row, browser)
            if result['failed']:
                failed.append(result)
            else:
                links += result['links']
        links = pd.DataFrame(links).drop_duplicates().reset_index(drop=True)

        handle_failures(failed)
        handle_links(links, all_links)
    except Exception:
        log.error('Uncaught error in main method. Exiting.', exc_info=True)
    finally:
        browser.close()


def load_csv(filename: str, missing_ok: bool = False) -> Optional[pd.DataFrame]:
    if filename:
        # if you pass a filename, but it doesn't exist, bad dog...
        if not os.path.isfile(filename):
            raise RuntimeError(f"File {filename} does not exist")
        return pd.read_csv(filename)
    # only throw an error if specified that an unspecified file is unacceptable
    if not missing_ok:
        raise RuntimeError("File not passed, but required.")
    return None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        dest='new_urls_file',
        type=str
    )
    parser.add_argument(
        dest='all_links_file',
        type=str,
        nargs='?',
        default=None
    )
    parser.add_argument(
        '--headless',
        dest='headless',
        action='store_true',
        default=False,
        required=False
    )
    return parser.parse_args()


def cli():
    args = parse_args()
    main(
        get_browser(args.headless),
        load_csv(args.new_urls_file, missing_ok=False),
        load_csv(args.all_links_file, missing_ok=True),
    )


if __name__ == '__main__':
    rc = 0
    try:
        cli()
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 1
    os.sys.exit(rc)
