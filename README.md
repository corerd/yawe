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


# References

## German Wiktionary Wikitext Syntax and Keywords
- [Help Main Page](https://de.wiktionary.org/wiki/Wiktionary:Hilfe)
- [Basic structure for dictionary entries](https://de.wiktionary.org/wiki/Hilfe:Formatvorlage)
- [Deflection tables for noun, verb, adjective, pronoun](https://de.wiktionary.org/wiki/Hilfe:Flexionstabellen)
