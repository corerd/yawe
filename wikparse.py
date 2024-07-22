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
"""
import wikitextparser as wtp
import re
from collections import namedtuple
from wikxtract import WiktiDs


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
    INFLECTION_ITEM = namedtuple('INFLECTION_ITEM', ['name', 'value'])
    ENTRY = namedtuple('ENTRY', ['term', 'wikitext', 'root_word', 'category', 'inflection_table'])

    def __init__(self, online=False):
        self.ds = WiktiDs(online)

    def query(self, term):
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
    pass
