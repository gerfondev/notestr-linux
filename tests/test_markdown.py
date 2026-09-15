from markdown_it import MarkdownIt
from nostr_notes.markdown import explicit_line_breaks
from nostr_notes.core import Identity


def test_user_example_is_visible_in_commonmark():
    original = '**Gras**\n~~Barré~~\n*Italique*\n\nJe suis content\nje suis pas content'
    output = explicit_line_breaks(original)
    html = MarkdownIt('commonmark').enable('strikethrough').render(output)
    assert '<strong>Gras</strong><br' in html
    assert '<s>Barré</s><br' in html
    assert 'Je suis content<br' in html
    assert explicit_line_breaks(output) == output


def test_code_structure_and_existing_breaks_are_preserved():
    for text in ['```python\na = 1\nb = 2\n```\n', '    a = 1\n    b = 2\n',
                 'Un `code\nmultiligne` dans une phrase.', 'un  \ndeux', 'un\\\ndeux',
                 '# Titre\n\nParagraphe\n\nAutre\n',
                 '| A | B |\n| --- | --- |\n| 1 | 2 |\n',
                 '<div>\nHTML brut\n</div>\n', '- a\n- b\n\n1. c\n2. d\n']:
        assert explicit_line_breaks(text) == text


def test_list_quote_and_crlf():
    assert explicit_line_breaks('> un\n> deux') == '> un  \n> deux'
    assert explicit_line_breaks('- un\n  suite\n- autre') == '- un  \n  suite\n- autre'
    assert explicit_line_breaks('un\r\ndeux') == 'un  \r\ndeux'


def test_save_encrypts_explicit_breaks_and_keeps_d():
    identity = Identity('0' * 63 + '1')
    event = identity.save('Je suis content\nje suis pas content', d='abcdef')
    notes, errors = identity.notes([event])
    assert not errors
    assert notes[0].d == 'abcdef'
    assert notes[0].markdown == 'Je suis content  \nje suis pas content'
