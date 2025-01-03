import re
from collections import Counter
from functools import partial
from pathlib import Path

import pdfplumber
from pdfplumber.page import Page
from pdfplumber.pdf import PDF
from pdfplumber.table import Table
from pdfplumber.utils import intersects_bbox

from dataframe_tools import (
    NUM_TO_DOC,
    TABLE_SETTINGS,
    WHITESPACE_HEADER,
)

PARAGRAPH_KEY = min(WHITESPACE_HEADER.keys())

"""
Parse pdf file and converts data into a structured list of dictionaries.
Returns:
    list[dict]: returns pdfs as a structured list of dictionaries.
"""
def pdf_parser(file: str) -> list[dict]:
    pdf_file = Path(file)
    if not pdf_file.exists():
        raise FileExistsError("File does not exist")

    records = []

    with pdfplumber.open(pdf_file) as doc:
        for page in doc.pages:
            tables = page.find_tables(table_settings=TABLE_SETTINGS)
            nontable_page = page.filter(partial(outside_tables, tables=tables))
            char_stat_dict = character_statistics(nontable_page)
            filtered = filter_page_by_chars(nontable_page, char_stat_dict)
            records.extend(text_line_tagger(filtered))

    return sorted(records, key=lambda x: x["doctop"])


"""
    Obtain character characteristics  like font name and font size.
    Returns:  dict: overall character statistics.
"""
def character_statistics(document: Page) -> dict:
    bold_counter = Counter()
    char_counter = Counter()
    size_counter = Counter()
    italic_counter = Counter()

    for char in document.chars:
        if "Bold" in char["fontname"]:
            bold_counter[char["fontname"]] += 1

        elif "Italic" in char["fontname"]:

            italic_counter[char["fontname"]] += 1
        else:
            char_counter[char["fontname"]] += 1

        size_counter[round(char["size"])] += 1

    counter_list = [bold_counter, char_counter, size_counter, italic_counter]
    final_dict = {}
    for counter in counter_list:
        if counter:
            k, v = counter.most_common()[0]
            final_dict[k] = v

    return final_dict


"""
    Get the regions of the page with no table.
    PDF: returns a filtered page that does not contain table data.
"""
def outside_tables(obj: PDF, tables: list[Table]) -> PDF:
    return not any(intersects_bbox([obj], t.bbox) for t in tables)

def filter_page_by_chars(page: Page, char_stat_dict: dict) -> Page:

    return page.filter(
        lambda x: x["object_type"] == "char" and x["fontname"] in char_stat_dict and round(x["size"]) in char_stat_dict,
    )


"""
Tag each line in the page appropriately
Returns: list[dict]: records  for each text line.
"""
def text_line_tagger(page: Page) -> list[dict]:
    page_lines = page.extract_text_lines()
    records = []

    horizontal_white_space = Counter(round(x["x0"]) for x in page_lines)

    for text in page_lines:

        if horizontal_white_space[round(text["x0"])] == 1:
            continue

        header = "Paragraph"

        if check_header(text):
            header = header_type(text)

        records.append(
            {
                "header_type": header,
                "text": text["text"],
                "doctop": text["chars"][0]["doctop"],
                "page_number": text["chars"][0]["page_number"],
            },
        )

    return records

"""
    Check for bold letters.
    Args:  text (dict): line text
    Returns: return True for all bold letters.
"""
def check_header(text: dict) -> bool:
    return all("Bold" in char["fontname"] for char in text["chars"])

"""
    Assigns new header type if the text has :
    1) leading number
    2) white space position
    3) has table or figure within its text.

    These 2 criterias are mutually exclusive and are used for different cases.

    Args:
        text (dict): text line dictionary
        horizontal_white_space (Counter): white space dictionary

    Returns:
        str:  new header string
"""
def header_type(text: dict) -> str:
    non_headers = ["Table", "Figure"]

    if any(text["text"].startswith(non) for non in non_headers):
        return "Paragraph"

    if round(text["x0"]) == PARAGRAPH_KEY:

        return number_to_header(text["text"])

    return whitespace_to_header(text["x0"])


"""
Assigns header type to number.
Args        :  text (str): header and value
Returns     :  header type in the form of string
"""
def number_to_header(text: str) -> str:
    nums = text.split()[0]
    total = len(re.findall(r"[0-9]+", nums))
    if total == 0:
        return "Paragraph"
    return NUM_TO_DOC.get(total, "SubSubSection")


"""
Handle edge case where the tool cannot extract leading numbers. Assigns header type based on whitespace position.
Returns the  _description_
"""
def whitespace_to_header(x0_position: int) -> str:
    min_val = float("inf")
    header = None

    for k, v in WHITESPACE_HEADER.items():
        x0_diff = abs(k - x0_position)
        if x0_diff < min_val:
            min_val = x0_diff
            header = v

    return header
