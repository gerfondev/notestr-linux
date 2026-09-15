"""Rendre explicites les retours du texte, sans modifier le code ni la structure Markdown."""
import re
from markdown_it import MarkdownIt
from markdown_it.rules_inline import newline


def _record_newline(state, silent):
    position = state.pos
    matched = newline(state, silent)
    if matched and not silent and state.tokens[-1].type == 'softbreak':
        state.tokens[-1].meta['source_line'] = state.src.count('\n', 0, position)
    return matched


def explicit_line_breaks(markdown: str) -> str:
    """Les simples retours d'un paragraphe deviennent des hardbreaks CommonMark.

    Le parseur distingue paragraphes, listes, tableaux, HTML et code (y compris
    code inline multiligne). On ne réécrit pas le document : seuls les espaces
    de fin des lignes contenant un softbreak sont ajustés.
    """
    parser = MarkdownIt('commonmark').enable(['table', 'strikethrough'])
    parser.inline.ruler.at('newline', _record_newline)
    breaks = set()
    for token in parser.parse(markdown):
        if token.type == 'inline' and token.map:
            for child in token.children or []:
                if child.type == 'softbreak' and 'source_line' in child.meta:
                    breaks.add(token.map[0] + child.meta['source_line'])
    # Conserver les séparateurs d'origine, même dans les blocs de code.
    parts = re.split(r'(\r\n|\r|\n)', markdown)
    for line in breaks:
        index = line * 2
        if index + 1 < len(parts):
            parts[index] = parts[index].rstrip(' \t') + '  '
    return ''.join(parts)
