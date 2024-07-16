
"""Query German Wiktionary
"""
from wikparse import Wiktionary


def dump_wikitext(wiktentry):
    """Store WikiText to a file whose name is wikitext_<search_term>.txt
    """
    wikitext_file_name = f'wikitext_{wiktentry.term}.txt'
    with open(wikitext_file_name, 'w', encoding="utf-8") as wikitext_file:
        wikitext_file.write(wiktentry.wikitext)
    return wikitext_file_name


def show(wiktentry):
    if wiktentry.wikitext is None:
        print(f'Search term "{wiktentry.term}" not found')
        return
    if len(wiktentry.root_word) == 0:
        print(f'Root of "{wiktentry.term}" not found')
        return
    print('Root Word:', wiktentry.root_word)
    if len(wiktentry.category) == 0:
        print('Category not found')
        return
    print('Category:', wiktentry.category)
    if len(wiktentry.inflection_table) == 0:
        print("Inflection_table not found")
        return
    for inflection in wiktentry.inflection_table:
        print(f'{inflection.name}: {inflection.value}')


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
        if entry.wikitext and len(entry.inflection_table) == 0:
            print(f'WikiText for "{user_input}" exists but not successful parsed.')
            wikitext_file = dump_wikitext(entry)
            print(f'WikiText saved in: {wikitext_file}')
