
"""Query German Wiktionary
"""
import os
from wikparse import Wiktionary


def dump_wikitext(wiktentry):
    """Store WikiText to a file whose name is wikitext_<search_term>.txt
    """
    script_full_path = os.path.realpath(__file__)
    wikitext_file_path = os.path.join(os.path.dirname(script_full_path), f'wikitext_{wiktentry.term}.txt')
    with open(wikitext_file_path, 'w', encoding="utf-8") as wikitext_file:
        wikitext_file.write(wiktentry.wikitext)
    return wikitext_file_path


def show(wiktentry):
    if wiktentry.wikitext is None:
        print(f'Search term "{wiktentry.term}" not found')
        return
    # wikitext_file = dump_wikitext(wiktentry)  # debug
    # print(f'DEBUG: WikiText saved in: {wikitext_file}')
    if len(wiktentry.lemma_root) == 0:
        print(f'Root of "{wiktentry.term}" not found')
        return
    print('Root Word:', wiktentry.lemma_root)
    for category in wiktentry.lemma_categories:
        print('Category:', category.name)
        for inflection in category.inflection_table:
            print(f'{inflection.name}: {inflection.value}')
        if len(category.translations) > 0:
            print('Translations:')
            for translation in category.translations:
                print(f'{translation.lang}: {translation.value}')
        print()


if __name__ == '__main__':
    print('Wiktionary query')
    wiki = Wiktionary()
    while True:
        try:
            user_input = input('\nTerm: ')
        except KeyboardInterrupt:
            print()
            break
        entry = wiki.query(user_input)
        show(entry)
        if entry.wikitext and len(entry.lemma_categories) == 0:
            print(f'WikiText for "{user_input}" exists but not successful parsed.')
            wikitext_file = dump_wikitext(entry)
            print(f'WikiText saved in: {wikitext_file}')
