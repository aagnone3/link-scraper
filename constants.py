class XPathMatchers:
    # match all links that have an href property
    LINKS = "//a[@href]"
    # match all links that have an href property and do not have a
    # <nav> element as an ancestor
    LINKS_NOT_UNDER_NAV = "//a[@href and not(ancestor::nav)]"


NEW_LINKS_FILE_HEADER = [
    "url",
    "label",
    "domain",
    "link",
    "full_link",
    "link_text",
    "link_class_name",
    "defined_change",
]

ALL_LINKS_FILE_HEADER = [
    "url",
    "label",
    "domain",
    "link",
    "full_link",
    "link_text",
    "link_class_name",
]
