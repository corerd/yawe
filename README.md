# YAWE (Yet Another Wikitext Extractor)
A simple Python utility for extracting and parsing Wikitext from
[German Wiktionary](https://de.wiktionary.org/wiki/Wiktionary:Hauptseite).

This utility performs a German Wiktionary lookup for a word,
fetches the corresponding page and parses its content
for extracting word definition and inflection.

The structure and formatting of Each Wiktionary page content is specified
in the [MediaWiki](https://www.mediawiki.org/wiki/MediaWiki) markup language called Wikitext,
also known as wiki markup or Wikicode.

Its syntax is uniq and can be found in [Wikitext Help Main Page](https://en.wikipedia.org/wiki/Help:Wikitext),
but any language Wiktionary defines the structure of their pages.

At the moment, this utility parses only German Wiktionary (see references below).
But it's an ongoing project; stay tuned for subsequent updates.


# Overview
The main utility consists of two module:
- The Extractor
- The Parser

## The Extractor
The Extractor looks up a word in the Wiktionary,
then it fetches and returns the Wikitext of the corresponding page.

## The Parser
The Parser returns definition and inflection from the Wikitext of the searched word.


# Requirements


# WARNING for windows users: Enable UTF-8 support in the Window terminal
On macOS and Linux, UTF-8 is the standard encoding.
But Windows still uses legacy encoding (e.g. cp1252, cp932, etc...) as system encoding.

Python works very well about file names, but the legacy system encoding is used for
the default encoding of text files, pipes and console IO (i.e. Window terminal).

Adding `encoding="utf-8"` option to the function `open()` solves the issue for file read / write, e.g.:
```python
    with open(file_name, 'r', encoding='utf-8') as file:
        # do something with file
```

Setting the environment variable 
```
    PYTHONUTF8=1 
```
solves the console IO issue too.

See also [Python: Use the UTF-8 mode on Windows](https://dev.to/methane/python-use-utf-8-mode-on-windows-212i)


# References

## German Wiktionary Wikitext Syntax and Keywords
- [Help Main Page](https://de.wiktionary.org/wiki/Wiktionary:Hilfe)
- [Basic structure for dictionary entries](https://de.wiktionary.org/wiki/Hilfe:Formatvorlage)
- [Deflection tables for noun, verb, adjective, pronoun](https://de.wiktionary.org/wiki/Hilfe:Flexionstabellen)
