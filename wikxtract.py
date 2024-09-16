"""Look up a word in the Wiktionary, then fetch and
return the Wikitext of the corresponding page.

The structure and formatting of Each MediaWiki wiki page content is specified
in a markup language called Wikitext, also known as wiki markup or Wikicode.

Its syntax is uniq but any language Wiktionary defines the structure of their pages.
This script parse Wikitext from the German Wiktionary.


# The German Wiktionary structure
In the body of a lemma definition, Wikitext provides six levels of division or sectioning.
The = through ====== markup are headings for the sections with which they are associated:
= Heading 1 =
== Heading 2 ==
=== Heading 3 ===
==== Heading 4 ====
===== Heading 5 =====
====== Heading 6 ======

The level 1 heading is styled as the lemma title and is not used within a definition.

The structure of a German Wiktionary lemma definition consists of at least 2 sections:
- A uniq `head` (`Der Kopf`), that is a level 2 heading at very top which specifies the language to which the lemma belongs.
  Example for the German lemma Haus:
    == Haus ({{Sprache|Deutsch}}) ==
- Next is the `middle section` (`Der Mittelteil`) where the inflection tables and most of the text modules are located.
  This section follows a level 3 heading as:
    === {{Wortart|Substantiv|Deutsch}}, {{n}} ===
  {{Wortart|abc|xyz}} ensures that the lemma is sorted into the category for the part of speech (`die Wortart`) abc in the language xyz.
  Category refers to noun, verb, adjective, etc.
  (Haus is thus sorted into the category:Noun (`Substantiv`) into the German (`Deutsch`) categories).
  The specification {{n}} does not assign the lemma to a category, but the n simply indicates that in the example case Haus is neuter.
  Accordingly, there is {{f}} for feminine nouns and {{m}} for masculine nouns.
- Inside the vast majority of lemma definitions there is also the `translation section` (`Der Übersetzungsabschnitt`), which includes the translations,
  but also the references and possibly the sources and similarities module and one or more navigation bars.
  This optional section follows a level 4 heading as:
    ==== {{Übersetzungen}} ====

If the lemma has more than one definition, then new middle sections are added accordingly,
each with its optional translation section.

## Regular expression template for Level 2 heading
In the German Wiktionary, the first section in a lemma definition starts with the Wikitext level 2 heading:
    == lemma ({{Sprache|Deutsch}}) ==
i.e. the lemma whose definition follows is surrounded by "== " and " ({{Sprache|Deutsch}}) ==".

The head section heading pattern can be defined by the regular expression:
    `== [\w]+ \({{Sprache\|Deutsch}}\) ==`

- `== `: Matches the first surrounding literal string "== ".

- `[\w]+`: Matches one or more word characters (letters, digits, and underscores).
  This part of the pattern will match the lemma whose definition follows this heading.
  
- ` \({{Sprache\|Deutsch}}\) `: Matches the literal string " ({{Sprache|Deutsch}}) ".
  The `\(` and `\)` are used to match the literal parentheses characters, `\|` matches the literal pipe command
  and `{{Sprache\|Deutsch}}` matches the exact string "{{Sprache|Deutsch}}".

- `==`: Matches the last surrounding literal string "=="

Any regex broken part can be surrounded by the parentheses `()` creating a capturing group,
meaning whatever matches this part of the pattern will be captured for later use.


# MediaWiki APIs
MediaWiki Action API provides a means to read and write content of a MediaWiki wiki.
It is structured in modules that can be extended by extensions, so they can differ from wiki to wiki.

This script interfaces with the German Wiktionary API


# References
Wikitext Help Main Page: https://en.wikipedia.org/wiki/Help:Wikitext

## German Wiktionary Wikitext Syntax and Keywords
- Help Main Page: https://de.wiktionary.org/wiki/Wiktionary:Hilfe
- Basic structure for dictionary entries: https://de.wiktionary.org/wiki/Hilfe:Formatvorlage
- Deflection tables for noun, verb, adjective, pronoun: https://de.wiktionary.org/wiki/Hilfe:Flexionstabellen

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


# MediaWiki German Wiktionary dump
WIKTIONARY_PAGES_DUMP = r'ds\dewiktionary-20240701-pages-articles.xml'  # 58.226.026 lines

# Define lemma head pattern by means of regex and python format() placeholder:
# - the empty curly braces placeholder `{}` will be replaced by the lemma whose definition follows the heading.
# - `\({{{{Sprache\|Deutsch}}}}\)` uses `\(`, `\|` and `\)` regex with `{{{{` and `}}}}` format() escaping
#   to match the exact string "{{Sprache|Deutsch}}".
WIKITEXT_LEMMA_HEAD_TEMPLATE = r'== {} \({{{{Sprache\|Deutsch}}}}\) =='


class WiktiDs:
    """Wiktionary Data Store"""
    # MediaWiki German Wiktionary API Endpoint
    WIKTI_API_URL = "https://de.wiktionary.org/w/api.php"

    def __init__(self, online=False):
        self.wikti_pages = None
        self.wikti_pages_idx = None
        self.wikti_pages_cache = {}
        if online:
            self.get_wikitext = self.get_wikitext_from_web
            self.wikti_pages_articles_path = ''
            self.wiktionary_index_path = ''
            return
        self.get_wikitext = self.get_wikitext_from_ds
        script_full_path = os.path.realpath(__file__)
        self.wikti_pages_articles_path = os.path.join(os.path.dirname(script_full_path), WIKTIONARY_PAGES_DUMP)
        wiktionary_basename, wiktionary_ext = os.path.splitext(self.wikti_pages_articles_path)
        self.wiktionary_index_path = wiktionary_basename + '-index.csv'
        try:
            self.wikti_pages_idx = open(self.wiktionary_index_path, 'r', encoding='utf-8')
        except FileNotFoundError:
            print('Index file not found')
            self.make_ds_index(self.wikti_pages_articles_path, self.wiktionary_index_path)
            # Try again to open index file
            self.wikti_pages_idx = open(self.wiktionary_index_path, 'r', encoding='utf-8')
        self.wikti_pages = open(self.wikti_pages_articles_path, 'r', encoding='utf-8')

    def __del__(self):
        # print('Delete WiktiDs class')
        if self.wikti_pages is not None:
            self.wikti_pages.close()
        if self.wikti_pages_idx is not None:
            self.wikti_pages_idx.close()

    def make_ds_index(self, file_name, index_file_name):
        """Parsed 58226026 lines in 38.40424108505249 s"""
        # Define the lemma head pattern:
        # - `[\w]+` matches the lemma whose definition follows its section heading.
        #   The parentheses () around [\w]+ create a matching group.
        # - `.*`: Matches any character (except for line terminators) zero or more times.
        #   This part of the pattern will match everything before and after the specific patterns.
        lemma_head_pattern = '.*' + WIKITEXT_LEMMA_HEAD_TEMPLATE.format(r'([\w]+)') + '.*'
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
                match = re.match(lemma_head_pattern, line)
                if match:
                    # append the offset to the index
                    index_file.writelines(f'{match.group(1)},{offset}\n')
                offset += len(line.encode('utf-8')) + line_ending_extra_sz
        time_elapsed = time() - time_start
        print(f'Parsed {linen} lines in {time_elapsed} s')

    def fetch_wikitext_from_ds(self, lemma, line_number):
        """Return Wikitext between the local Data Store line number
        and the end of lemma definitions.
        """
        # define the lemma title pattern
        # removing regex '\' escape character.
        lemma_head_pattern = WIKITEXT_LEMMA_HEAD_TEMPLATE.format(lemma).replace('\\', '')

        # Wikitext lemma definitions are found between <text>..</text> XML tags in the local Data Store.
        # line_number points to the line containing the lemma title inside <text>..</text> tags.
        self.wikti_pages.seek(line_number)
        first_section_line = self.wikti_pages.readline()
        # Remove everything from the beginning of the first line to lemma title
        section_line = re.sub(r'^.*?' + re.escape(lemma_head_pattern), lemma_head_pattern, first_section_line)
        wikitext = ''
        while True:
            end_text_position = section_line.find('</text>')  # search the end of lemma definitions
            if end_text_position > 0:
                # found the end of lemma definitions
                wikitext = wikitext + section_line[:end_text_position]
                break
            # else continue extracting
            wikitext = wikitext + section_line
            section_line = self.wikti_pages.readline()
        return wikitext

    def get_wikitext_from_ds(self, search_word):
        """Search the given word in the local Data Store
        returning the corresponding Wikitext markup language.
        The search is case sensitive.
        """
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
        # Then return the Wikitext corresponding to search_word  
        # in the local Data Store starting from line_number
        return self.fetch_wikitext_from_ds(search_word, line_number)

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
    print('Show performance results searching the first and last words in Wiktionary pages dump')
    ds = WiktiDs()
    # Get the first and last words in index file
    first_line = ''
    last_line = ''
    with open(ds.wiktionary_index_path, 'r', encoding='utf-8') as index_file:
        for line in index_file:
            if len(first_line) == 0:
                first_line = line
            last_line = line
    first_word = first_line.rstrip().split(',')[0]
    last_word = last_line.rstrip().split(',')[0]

    print(f'Get first word "{first_word}" wikitext:')  # 0.001001119613647461 s
    time_start = time()
    wikitext = ds.get_wikitext(first_word)
    time_elapsed = time() - time_start
    if wikitext:
        print(f'\tTime: {time_elapsed} s')
    else:
        print('\tNot found!')

    print(f'Get last word "{last_word}" wikitext:')  # 0.42599916458129883 s
    time_start = time()
    wikitext = ds.get_wikitext(last_word)
    time_elapsed = time() - time_start
    if wikitext:
        print(f'\tTime: {time_elapsed} s')
    else:
        print('\tNot found!')

    print('Show performance results searching online')
    online_wiktionary = WiktiDs(True)

    print(f'Get first word "{first_word}" wikitext on line:')  # 0.49244213104248047 s
    time_start = time()
    wikitext = online_wiktionary.get_wikitext(first_word)
    time_elapsed = time() - time_start
    if wikitext:
        print(f'\tTime: {time_elapsed} s')
    else:
        print('\tNot found!')

    print(f'Get last word "{last_word}" wikitext on line:')  # 0.41349339485168457 s
    time_start = time()
    wikitext = online_wiktionary.get_wikitext(last_word)
    time_elapsed = time() - time_start
    if wikitext:
        print(f'\tTime: {time_elapsed} s')
    else:
        print('\tNot found!')
