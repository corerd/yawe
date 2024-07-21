"""Look up a word in the Wiktionary, then fetch and
return the Wikitext of the corresponding page.

MediaWiki Action API provides a means to read and write content of a MediaWiki wiki.
It is structured in modules that can be extended by extensions, so they can differ from wiki to wiki.

This script interfaces with the German Wiktionary API


# Searching for a word definition
In the German Wiktionary, each word definition belongs to a section with the wikitext heading:
    == word ({{Sprache|Deutsch}}) ==
i.e. the word whose definition follows is surrounded by "== " and " ({{Sprache|Deutsch}}) ==".

The section heading pattern can be defined by the regular expression:
    `== [\w]+ \({{Sprache\|Deutsch}}\) ==`

- `== `: Matches the first surrounding literal string "== ".

- `[\w]+`: Matches one or more word characters (letters, digits, and underscores).
  This part of the pattern will match the word whose definition follows this heading.
  
- ` \({{Sprache\|Deutsch}}\) `: Matches the literal string " ({{Sprache|Deutsch}}) ".
  The `\(` and `\)` are used to match the literal parentheses characters, `\|` matches the literal pipe command
  and `{{Sprache\|Deutsch}}` matches the exact string "{{Sprache|Deutsch}}".

- `==`: Matches the last surrounding literal string "=="

Any regex broken part can be surrounded by the parentheses `()` creating a capturing group,
meaning whatever matches this part of the pattern will be captured for later use.


# References

## MediaWiki API
Main page: https://www.mediawiki.org/wiki/API
Action API Main page: https://www.mediawiki.org/wiki/API:Main_page
API Tutorial: https://www.mediawiki.org/wiki/API:Tutorial
German Wiktionary API Help page: https://de.wiktionary.org/w/api.php
"""
import os
import re
import sys
import requests
from time import time


# Define section heading pattern by means of regex and format() placeholder:
# - the empty curly braces placeholder `{}` will be replaced by the word whose definition follows the heading.
# - `\({{{{Sprache\|Deutsch}}}}\)` uses `\(`, `\|` and `\)` regex with `{{{{` and `}}}}` format() escaping
#   to match the exact string "{{Sprache|Deutsch}}".
WIKITEXT_SECTION_HEAD_TEMPLATE = r'== {} \({{{{Sprache\|Deutsch}}}}\) =='


class WiktiDs:
    """Wiktionary Data Store"""
    # MediaWiki German Wiktionary API Endpoint
    WIKTI_API_URL = "https://de.wiktionary.org/w/api.php"

    # MediaWiki German Wiktionary dump
    WIKTIONARY_PAGES = r'ds\dewiktionary-20240701-pages-articles.xml'  # 58.226.026 lines

    def __init__(self, online=False):
        self.wikti_pages = None
        self.wikti_pages_idx = None
        self.wikti_pages_cache = {}
        if online:
            self.get_wikitext = self.get_wikitext_from_web
            return
        self.get_wikitext = self.get_wikitext_from_ds
        wiktionary_basename, wiktionary_ext = os.path.splitext(WiktiDs.WIKTIONARY_PAGES)
        wiktionary_index_file_name = wiktionary_basename + '-index.csv'
        try:
            self.wikti_pages_idx = open(wiktionary_index_file_name, 'r', encoding='utf-8')
        except FileNotFoundError:
            print('Index file not found')
            self.make_ds_index(WiktiDs.WIKTIONARY_PAGES, wiktionary_index_file_name)
            # Try again to open index file
            self.wikti_pages_idx = open(wiktionary_index_file_name, 'r', encoding='utf-8')
        self.wikti_pages = open(WiktiDs.WIKTIONARY_PAGES, 'r', encoding='utf-8')

    def __del__(self):
        # print('Delete WiktiDs class')
        if self.wikti_pages is not None:
            self.wikti_pages.close()
        if self.wikti_pages_idx is not None:
            self.wikti_pages_idx.close()

    def make_ds_index(self, file_name, index_file_name):
        """Parsed 58226026 lines in 38.40424108505249 s"""
        # Define the section heading pattern:
        # - `[\w]+` matches the word whose definition follows its section heading.
        #   The parentheses () around [\w]+ create a matching group.
        # - `.*`: Matches any character (except for line terminators) zero or more times.
        #   This part of the pattern will match everything before and after the specific patterns.
        section_head_search_pattern = '.*' + WIKITEXT_SECTION_HEAD_TEMPLATE.format(r'([\w]+)') + '.*'
        print(f'Making index file: {index_file_name}')
        # Check line ending size of input file:
        # computing the offset of a line in a text file,
        # the size of line ending matters because readline()
        # converts it to one only character ('\n') for any Operating System.
        line_ending_extra_sz = 0
        with open(file_name, 'rb') as file:
            # Open file as binary to avoid line ending conversion
            for line in file:
                if b'\r\n' in line:
                    # Windows text file line ending
                    # else '\n' (unix) or '\r' (mac)
                    line_ending_extra_sz = 1
                break
        # Parse input file and create its index
        time_start = time()
        with open(file_name, 'r', encoding='utf-8') as file, \
                open(index_file_name, 'w', encoding='utf-8') as index_file:
            offset = 0
            linen = 0
            for line in file:
                if linen % 500000 == 0:
                    # Use sys.stdout.write() instead of print()
                    # as a workaround to fix '\r' display in VS Code terminal
                    sys.stdout.write(f'Parsed {linen} lines\r')
                linen += 1
                # Search the wikitext page title in the current line
                match = re.match(section_head_search_pattern, line)
                if match:
                    # append the offset to the index
                    index_file.writelines(f'{match.group(1)},{offset}\n')
                offset += len(line.encode('utf-8')) + line_ending_extra_sz
        time_elapsed = time() - time_start
        print(f'Parsed {linen} lines in {time_elapsed} s')

    def get_wikitext_from_ds(self, search_word):
        line_number = -1
        # First search the index cache
        try:
            line_number = self.wikti_pages_cache[search_word]
        except KeyError:
            # if not already in cache, search the index file
            for line in self.wikti_pages_idx:
                items = line.rstrip().split(',')
                line_number = int(items[1])
                # Add to the cache
                self.wikti_pages_cache[items[0]] = line_number
                if items[0] == search_word:
                    break
                line_number = -1
        if line_number < 0:
            # Not found
            return None
        # Then seek to the beginning of the search word entry section
        self.wikti_pages.seek(line_number)

        # Define the section heading pattern for the searching word
        # removing regex '\' escape character.
        section_head_pattern = WIKITEXT_SECTION_HEAD_TEMPLATE.format(search_word).replace('\\', '')

        # Extract wikitext from the word section
        first_section_line = self.wikti_pages.readline()
        # Remove everything from the beginning of the first line to section title
        section_line = re.sub(r'^.*?' + re.escape(section_head_pattern), section_head_pattern, first_section_line)
        wikitext = ''
        while True:
            end_text_position = section_line.find('</text>')
            if end_text_position > 0:
                wikitext = wikitext + section_line[:end_text_position]
                break
            wikitext = wikitext + section_line
            section_line = self.wikti_pages.readline()
        return wikitext

    def get_wikitext_from_web(self, search_word):
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
        query_result = requests.get(WiktiDs.WIKTI_API_URL, headers=req_headers, params=req_params)
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
