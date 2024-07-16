"""Look up a word in the Wiktionary, then fetch and
return the Wikitext of the corresponding page.

MediaWiki Action API provides a means to read and write content of a MediaWiki wiki.
It is structured in modules that can be extended by extensions, so they can differ from wiki to wiki.

This script interfaces with the German Wiktionary API


# References

## MediaWiki API
Main page: https://www.mediawiki.org/wiki/API
Action API Main page: https://www.mediawiki.org/wiki/API:Main_page
API Tutorial: https://www.mediawiki.org/wiki/API:Tutorial
German Wiktionary API Help page: https://de.wiktionary.org/w/api.php
"""
import requests


# MediaWiki Wiktionary German API Endpoint
WIKTI_API_URL = "https://de.wiktionary.org/w/api.php"


def wikxtract_from_web(search_word):
    """Search Wiktionary for the given word using MediaWiki Action API and requests library,
    returning the corresponding page in Wikitext markup language.
    The search is case sensitive.

    See: https://github.com/earwig/mwparserfromhell?tab=readme-ov-file#integration
    """
    # Action API request claiming output data in JSON format
    req_headers = {"User-Agent": "yawe/1.0"}
    req_params = {
        "action": "parse",
        "prop": "wikitext",
        "page": search_word,
        "format": "json",
        "formatversion": "2",  # modern JSON format
    }
    query_result = requests.get(WIKTI_API_URL, headers=req_headers, params=req_params)
    # Deserialize JSON data:
    response = query_result.json()
    # if the search word exists, Action API returns the following JSON data:
    # response = {
    #     "parse": {
    #         "title": "search_words",
    #         "pageid": <PAGE_ID>,
    #         "wikitext": <wiki_markup>
    #     }
    # }
    try:
        wikitext = response["parse"]["wikitext"]
    except:
        # search word not found
        return None
    return wikitext


if __name__ == '__main__':
    pass
