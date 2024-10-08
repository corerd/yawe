"""Wiktionary Wikitext parser.

The structure and formatting of Each MediaWiki wiki page content is specified
in a markup language called Wikitext, also known as wiki markup or Wikicode.

Its syntax is uniq but any language Wiktionary defines the structure of their pages.
This script parse information from the German Wiktionary.

# References
Wikitext Help Main Page: https://en.wikipedia.org/wiki/Help:Wikitext

## German Wiktionary Wikitext Syntax and Keywords
- Help Main Page: https://de.wiktionary.org/wiki/Wiktionary:Hilfe
- Basic structure for dictionary entries: https://de.wiktionary.org/wiki/Hilfe:Formatvorlage
- Deflection tables for noun, verb, adjective, pronoun: https://de.wiktionary.org/wiki/Hilfe:Flexionstabellen

## Italian Wiktionary Wikitext Syntax and Keywords
As a comparison, here are the specifications of Italian Wiktionary pages format:
- Help Main Page: https://it.wiktionary.org/wiki/Pagina_principale
- Basic structure of Wiktionary pages: https://it.wiktionary.org/wiki/Wikizionario:Manuale_di_stile
"""
import wikitextparser as wtp
import re
import sys
from collections import namedtuple
from wikxtract import WiktiDs


"""Categories found in 780117 terms:
Substantiv
Personalpronomen
Verb
Adjektiv
Abkürzung
Adverb
Zahlzeichen
Deklinierte Form
Partikel
Indefinitpronomen
Präposition
Demonstrativpronomen
Interjektion
Temporaladverb
Konjugierte Form
Kontraktion
Grußformel
Subjunktion
Konjunktion
Numerale
Onomatopoetikum
Artikel
Eigenname
Pronomen
Antwortpartikel
Gradpartikel
Partizip II
Fokuspartikel
Reflexivpronomen
Komparativ
Konjunktionaladverb
Pronominaladverb
Relativpronomen
Interrogativpronomen
Modaladverb
Possessivpronomen
Lokaladverb
Modalpartikel
Toponym
Negationspartikel
Partizip I
Präfix
Interrogativadverb
Reziprokpronomen
Redewendung
Nachname
Erweiterter Infinitiv
Adjektiv
Buchstabe
Postposition
Straßenname
Superlativ
Dekliniertes Gerundivum
Wortverbindung
"""


# Section descriptor
SECTION_DATA = namedtuple('SECTION_DATA', ['level', 'header', 'body'])


def wiki_headers_factory(string):
    """Iterate through the wikitext string in pure python
    to find patterns that match r'(==+.*?==+)' then return
    the tuple (header_start_position, header_end_position, level) one at a time.

    It looks for sequences of == characters, followed by any characters
    until another sequence of == characters is found.
    Then collects these matches as an iterable object.

    Understand iterables and generators:
    https://stackoverflow.com/a/231855
    """
    cursor = 0
    while cursor < len(string):
        if string[cursor] == '=' and cursor + 1 < len(string) and string[cursor + 1] == '=':
            start = cursor
            level = 0
            while cursor < len(string) and string[cursor] == '=':
                cursor += 1
                level += 1
            while cursor < len(string) and string[cursor] != '=':
                cursor += 1
            while cursor < len(string) and string[cursor] == '=':
                cursor += 1
            end = cursor
            yield (start, end, level)
        else:
            cursor += 1


def wiki_sections_factory(wikitext):
    """Iterate through wikitext to find division sections
    returning them one at a time
    """
    matching_headers = wiki_headers_factory(wikitext)
    # get the first header
    first_match = matching_headers.__next__()
    if not first_match:
        return None
    current_level = first_match[2]
    current_header = wikitext[first_match[0]:first_match[1]]
    # section body is the text between
    # the and of current header and the start of next
    body_start = first_match[1]
    # look forward headers
    for next_match in matching_headers:
        next_header = wikitext[next_match[0]:next_match[1]]
        if next_header[4] == '=':
            # merge sections with eheader level 5 or more
            # in the current section
            continue
        yield SECTION_DATA(current_level, current_header, wikitext[body_start:next_match[0]])
        current_level = next_match[2]
        current_header = next_header
        body_start = next_match[1]
    yield SECTION_DATA(current_level, current_header, wikitext[body_start:])


class Wiktionary:
    """The WikiTextParser package is used to parse WikiText.

    References for WikiTextParser:
    https://github.com/5j9/wikitextparser/tree/main#wikitextparser
    """
    TEMPLATE_PATTERNS_TABLE = {
        # Category            template name regex 
        'Verb'              : r'Deutsch (\w+) Übersicht.*',
        'Adjektiv'          : r'Deutsch (\w+) Übersicht.*',
        'Indefinitpronomen' : r'Deutsch (\w+) Übersicht.*',
        'Artikel'           : r'Pronomina-Tabelle.*',
        'Substantiv'        : r'Deutsch (\w+) Übersicht.*'
    }
    LIST_ITEM_PATTERNS_TABLE = {
        # Category            list item regex 
        'Konjugierte Form'  : r"([\w\s\.]+)'''\[\[(\w+)\]\]'''",
        'Deklinierte Form'  : r"([\w\s\.]+)'''\[\[(\w+)\]\]'''"
    }
    LEMMA_CLASS = namedtuple('LEMMA_CLASS', ['type', 'defs'])
    LEMMA_DESC = namedtuple('LEMMA_DESC', ['term', 'wikitext', 'lemma_root', 'lemma_categories'])
    INFLECTION_ITEM = namedtuple('INFLECTION_ITEM', ['name', 'value'])
    TRANSLATION_ITEM = namedtuple('TRANSLATION_ITEM', ['lang', 'value'])
    ENTRY = namedtuple('ENTRY', ['term', 'wikitext', 'root_word', 'category', 'inflection_table'])

    class category_desc:

        def __init__(self, name):
            self.name = name
            self.inflection_table = ()
            self.translations = ()
        
        def append_inflection_table(self, inflection_item):
            # TODO filter inflection items
            self.inflection_table += (inflection_item,)

        def append_translation(self, translation_item):
            if translation_item.lang in ('en', 'fr', 'it', 'sp'):
                self.translations += (translation_item,)
            # ignore othe languages

    def __init__(self, online=False):
        self.ds = WiktiDs(online)

    def get_category_list(self):
        category_list = []
        with open(self.ds.wiktionary_index_path, 'r', encoding='utf-8') as index_file:
            linen = 0
            for line in index_file:
                if linen % 5000 == 0:
                    # Use sys.stdout.write() instead of print()
                    # as a workaround to fix '\r' display in VS Code terminal
                    sys.stdout.write(f'Parsed {linen} lines\r')
                linen += 1

                term, line_number = line.rstrip().split(',')
                line_number = int(line_number)
                wikitext = self.ds.fetch_wikitext_from_ds(term, line_number)
                if wikitext:
                    wikitext_parsed = wtp.parse(wikitext)
                    root_word, category = self.get_header(wikitext_parsed)
                    if len(category) > 0:
                        if category not in category_list:
                            category_list.append(category)
        print(f'Parsed {linen} lines')
        return category_list

    def parse_head(self, section):
        """Parse lemma section HEAD
        returning the root lemma
        """
        if not section:
            return None
        if section.level != 2:
            return None
        # check that the lemma belongs to the German language
        match = re.match(r'==\s*(\w+) \({{Sprache\|Deutsch}}\).*', section.header)
        if not match:
            return None
        return match.group(1)

    def parse_middle(self, section):
        middle_header_pattern = r".*?(?:{{Wortart\|([\w\s]+)\|Deutsch}})(?:, {{([fmn]+)}})?(?:, {{Wortart\|([\w\s]+)\|Deutsch}})?.*"
        match_list = re.findall(middle_header_pattern, section.header)
        if not match_list:
            return None
        # findall returns all non-overlapping matches
        # of the pattern in section header as a list of tuples.
        category = self.category_desc(', '.join(match_list[0]))  # the name
        wikitext_parsed = wtp.parse(section.body)
        # Parse templates
        for template in wikitext_parsed.templates:
            match  = re.match(r'Deutsch (\w+) Übersicht.*', template.name)
            if match:
                for argc in range(len(template.arguments)):
                    argv = template.arguments[argc]
                    category.append_inflection_table(Wiktionary.INFLECTION_ITEM(argv.name, argv.value.rstrip()))
        # Parse lists
        for wikilist in wikitext_parsed.get_lists(pattern=r'\*'):
            for list_item in wikilist.items:
                match  = re.match(r"([\w\s\.]+)'''\[\[(\w+)\]\]'''", list_item)
                if match:
                    category.append_inflection_table(Wiktionary.INFLECTION_ITEM(match[1], match[2]))
        return category

    def parse_translation(self, category, section):
        if section.header != '==== {{Übersetzungen}} ====':
            return
        pattern = r"\*{{(\w+)}}: {{Ü\|\w+\|(\w+)}}(?: {{(\w+)}})?"
        match_list = re.findall(pattern, section.body)
        if match_list:
            for match in match_list:
                category.append_translation(Wiktionary.TRANSLATION_ITEM(match[0], ', '.join(match[1:])))
            
    def query(self, search_word):
        """Search for a word and return its lemma description"""
        lemma_root = ''
        categories = ()
        word_wikitext = self.ds.get_wikitext(search_word)
        if word_wikitext:
            # split wikitext in lemma description sections
            sections = wiki_sections_factory(word_wikitext)
            # the first section of a lemma description must be the HEAD
            lemma_root = self.parse_head(sections.__next__())
            if lemma_root:
                # parse next sections
                for section in sections:
                    if section.level == 3:
                        category = self.parse_middle(section)
                        if category:
                            categories += (category,)
                    elif section.level == 4:
                        current_category = len(categories) - 1
                        if current_category >= 0:
                            self.parse_translation(categories[current_category], section)
        return Wiktionary.LEMMA_DESC(search_word, word_wikitext, lemma_root, categories)

    def query_old(self, term):
        root_word = ''
        category = ''
        inflection_table = ()
        wikitext = self.ds.get_wikitext(term)
        if wikitext:
            wikitext_parsed = wtp.parse(wikitext)
            root_word, category = self.get_header(wikitext_parsed)
            if len(root_word) and len(category):
                inflection_table = self.get_inflection_table(category, wikitext_parsed)
        return Wiktionary.ENTRY(term, wikitext, root_word, category, inflection_table)

    def get_inflection_table(self, category, wikitext_parsed):
        try:
            template_pattern = Wiktionary.TEMPLATE_PATTERNS_TABLE[category]
        except KeyError:
            try:
                list_item_pattern = Wiktionary.LIST_ITEM_PATTERNS_TABLE[category]
            except KeyError:
                # No pattern for this category
                return ()
            return self.wiki_list_2_list(wikitext_parsed.get_lists(pattern=r'\*'), list_item_pattern)
        return self.wiki_template_2_list(wikitext_parsed.templates, template_pattern)

    def get_header(self, wikitext_parsed):
        """Return the title of the wikitext markup page"""
        root_word = ''
        category = ''
        headings = wikitext_parsed.sections
        for heading in headings:
            if heading.level == 2:
                if len(root_word) == 0:
                    match = re.match(r'\s*(\w+) \({{Sprache\|Deutsch}}\).*', heading.title)
                    if match:
                        root_word = match.group(1)
            elif heading.level == 3:
                if len(category) == 0:
                    match = re.match(r'\s* {{Wortart\|([\w\s]+)\|Deutsch}}.*', heading.title)
                    if match:
                        category = match.group(1)
        return root_word, category

    def wiki_template_2_list(self, templates, pattern):
        """Convert WikiTextParser template arguments into Python list
        """
        inflection_list = ()
        for template in templates:
            template_inflection_type = template.name
            match  = re.match(pattern, template_inflection_type)
            if match:
                for argc in range(len(template.arguments)):
                    argv = template.arguments[argc]
                    inflection_list = inflection_list + (Wiktionary.INFLECTION_ITEM(argv.name, argv.value.rstrip()),)
                break
        return inflection_list

    def wiki_list_2_list(self, lists, pattern):
        """Convert WikiTextParser list into Python list
        """
        inflection_list = ()
        for wikilist in lists:
            for list_item in wikilist.items:
                match  = re.match(pattern, list_item)
                if match:
                    inflection_list = inflection_list + (Wiktionary.INFLECTION_ITEM(match[1], match[2]),)
        return inflection_list


if __name__ == '__main__':
    wiki = Wiktionary()

    wiki.query('Mann')
    exit(0)

    category_list = wiki.get_category_list()
    for cat in category_list:
        print(cat)
