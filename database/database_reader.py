import json
import os
import re

from unidecode import unidecode

from utils import date_management
from database.database import get_path


def get_all_votes_for_day(date: str) -> dict:
    """
    Return the votes for a given day
    :param date: date as iso formatted string
    """
    file_name = get_path(date + ".json")
    if not os.path.exists(file_name):
        return {}
    else:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)


def search_eu_document(keywords: str, date: str):
    all_votes_for_day = get_all_votes_for_day(date)
    keywords_re = ".*".join(map(lambda kw: re.escape(unidecode(kw)), keywords.split(" ")))
    keywords_regex = re.compile(f".*{keywords_re}.*", flags=re.IGNORECASE | re.MULTILINE)
    matching_items = {}
    for eu_document_code, value in all_votes_for_day.items():
        # This might happen if data is not completely available in europarl.europa.eu
        if "details" not in value:
            continue
        if keywords_regex.match(unidecode(" ".join([value["details"]["title"], value["details"]["description"], eu_document_code]))):
            matching_items[eu_document_code] = value
    return matching_items


def search_in_time_range(start_date: str, end_date: str, keywords: str):
    for date in date_management.date_range(start_date, end_date):
        yield search_eu_document(keywords, date)


def get_vote_corrections(eu_document_code: str, date: str, vote_id: str | None = None) -> list[dict]:
    """
    Members who declared after a vote that they wanted to vote differently: they pressed the wrong button, or did
    not manage to vote. These corrections do not change the official result. They are published since 2018.
    :param eu_document_code: code of the voted document, for example "A10-0258/2026"
    :param date: date of the vote as iso formatted string
    :param vote_id: identifier of one of the votes on the document (amendment, paragraph, ...), as listed in its
    "amendments". None for the final vote on the document.
    :return: [{"name": ..., "group": "France / <group> :", "voted": "+" | "-" | "0" | None, "intended": "+" | "-" | "0"}],
    "voted" is None if the member did not vote. Empty list if the document or the vote is unknown.
    """
    document = get_all_votes_for_day(date).get(eu_document_code, {})
    if vote_id is None:
        return document.get("corrections", [])
    for amendment in document.get("amendments", []):
        if amendment["id"] == vote_id:
            return amendment.get("corrections", [])
    return []
