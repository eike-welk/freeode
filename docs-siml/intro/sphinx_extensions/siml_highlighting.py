# -*- coding: utf-8 -*-
"""
    siml_highlighting.py
    ~~~~~~~~~~~~~~~~~~~~~

    Lexer for the Siml language.
    
    Derived from `pygments.lexers.agile.py`
    Sphinx integration taken from Matplotlib's `ipython_console_highlighting.py`

    :copyright: Copyright 2006-2010 by the Pygments team, see AUTHORS.
    :copyright: Copyright 2010-2010 by Eike Welk.
    :license: BSD, see LICENSE for details.
"""

import re

from pygments.lexer import RegexLexer, include, combined, bygroups
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
                           Number, Punctuation
#from pygments.util import get_bool_opt, get_list_opt, shebang_matches
from pygments import unistring as uni

from sphinx import highlighting



class SimlLexer(RegexLexer):
    """
    Lexer for the Siml language.
    
    This is a modified version of `Python3Lexer` and `PythonLexer` thrown 
    together.
    """

    name = 'Siml'
    aliases = ['siml']
    filenames = ['*.siml'] 
    mimetypes = ['text/x-siml', 'application/x-siml']

    flags = re.MULTILINE | re.UNICODE

    uni_name = "[%s][%s]*" % (uni.xid_start, uni.xid_continue)

    tokens = {
        'root': [
            (r'\n', Text),
            (r'^(\s*)("""(?:.|\n)*?""")', bygroups(Text, String.Doc)),
            (r"^(\s*)('''(?:.|\n)*?''')", bygroups(Text, String.Doc)),
            (r'[^\S\n]+', Text),
            (r'#.*$', Comment),
            (r'[]{}:(),;[]', Punctuation),
            (r'\\\n', Text),
            (r'\\', Text),
            (r'(in|is|and|or|not)\b', Operator.Word),
            (r'!=|==|<<|>>|[-~+/*%=<>&^|.]', Operator),
            include('keywords'),
            (r'(def)((?:\s|\\\s)+)', bygroups(Keyword, Text), 'funcname'),
            (r'(class)((?:\s|\\\s)+)', bygroups(Keyword, Text), 'classname'),
            (r'(from)((?:\s|\\\s)+)', bygroups(Keyword.Namespace, Text), 'fromimport'),
            (r'(import)((?:\s|\\\s)+)', bygroups(Keyword.Namespace, Text), 'import'),
            include('builtins'),
            include('backtick'),
            ('(?:[rR]|[uU][rR]|[rR][uU])"""', String, 'tdqs'),
            ("(?:[rR]|[uU][rR]|[rR][uU])'''", String, 'tsqs'),
            ('(?:[rR]|[uU][rR]|[rR][uU])"', String, 'dqs'),
            ("(?:[rR]|[uU][rR]|[rR][uU])'", String, 'sqs'),
            ('[uU]?"""', String, combined('stringescape', 'tdqs')),
            ("[uU]?'''", String, combined('stringescape', 'tsqs')),
            ('[uU]?"', String, combined('stringescape', 'dqs')),
            ("[uU]?'", String, combined('stringescape', 'sqs')),
            include('name'),
            include('numbers'),
        ],
        'keywords': [
            (r'(assert|break|continue|del|elif|else|except|'
             r'finally|for|global|if|lambda|pass|raise|'
             r'return|try|while|yield|as|with|True|False|None)\b', Keyword),
        ],
        'builtins': [
            (r'(?<!\.)(__import__|abs|all|any|bin|bool|bytearray|bytes|'
             r'chr|classmethod|cmp|compile|complex|delattr|dict|dir|'
             r'divmod|enumerate|eval|filter|float|format|frozenset|getattr|'
             r'globals|hasattr|hash|hex|id|input|int|isinstance|issubclass|'
             r'iter|len|list|locals|map|max|memoryview|min|next|object|oct|'
             r'open|ord|pow|print|property|range|repr|reversed|round|'
             r'set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|'
             r'vars|zip)\b', Name.Builtin),
            (r'(?<!\.)(self|Ellipsis|NotImplemented)\b', Name.Builtin.Pseudo),
            (r'(?<!\.)(ArithmeticError|AssertionError|AttributeError|'
             r'BaseException|BufferError|BytesWarning|DeprecationWarning|'
             r'EOFError|EnvironmentError|Exception|FloatingPointError|'
             r'FutureWarning|GeneratorExit|IOError|ImportError|'
             r'ImportWarning|IndentationError|IndexError|KeyError|'
             r'KeyboardInterrupt|LookupError|MemoryError|NameError|'
             r'NotImplementedError|OSError|OverflowError|'
             r'PendingDeprecationWarning|ReferenceError|'
             r'RuntimeError|RuntimeWarning|StopIteration|'
             r'SyntaxError|SyntaxWarning|SystemError|SystemExit|TabError|'
             r'TypeError|UnboundLocalError|UnicodeDecodeError|'
             r'UnicodeEncodeError|UnicodeError|UnicodeTranslateError|'
             r'UnicodeWarning|UserWarning|ValueError|VMSError|Warning|'
             r'WindowsError|ZeroDivisionError)\b', Name.Exception),
        ],
        'numbers': [
            (r'(\d+\.\d*|\d*\.\d+)([eE][+-]?[0-9]+)?', Number.Float),
            (r'0[oO][0-7]+', Number.Oct),
            (r'0[bB][01]+', Number.Bin),
            (r'0[xX][a-fA-F0-9]+', Number.Hex),
            (r'\d+', Number.Integer)
        ],
        'backtick': [],
        'name': [
            (r'@[a-zA-Z0-9_]+', Name.Decorator),
            (uni_name, Name),
        ],
        'funcname': [
            (uni_name, Name.Function, '#pop')
        ],
        'classname': [
            (uni_name, Name.Class, '#pop')
        ],
        'import': [
            (r'(\s+)(as)(\s+)', bygroups(Text, Keyword, Text)),
            (r'\.', Name.Namespace),
            (uni_name, Name.Namespace),
            (r'(\s*)(,)(\s*)', bygroups(Text, Operator, Text)),
            (r'', Text, '#pop') # all else: go back
        ],
        'fromimport': [
            (r'(\s+)(import)\b', bygroups(Text, Keyword), '#pop'),
            (r'\.', Name.Namespace),
            (uni_name, Name.Namespace),
        ],
        'stringescape': [
            (r'\\([\\abfnrtv"\']|\n|N{.*?}|u[a-fA-F0-9]{4}|'
             r'U[a-fA-F0-9]{8}|x[a-fA-F0-9]{2}|[0-7]{1,3})', String.Escape)
        ],
        'strings': [
            (r'[^\\\'"%\n]+', String),
            # quotes, percents and backslashes must be parsed one at a time
            (r'[\'"\\]', String),
            # unhandled string formatting sign
            (r'%', String)
            # newlines are an error (use "nl" state)
        ],
        'nl': [
            (r'\n', String)
        ],
        'dqs': [
            (r'"', String, '#pop'),
            (r'\\\\|\\"|\\\n', String.Escape), # included here again for raw strings
            include('strings')
        ],
        'sqs': [
            (r"'", String, '#pop'),
            (r"\\\\|\\'|\\\n", String.Escape), # included here again for raw strings
            include('strings')
        ],
        'tdqs': [
            (r'"""', String, '#pop'),
            include('strings'),
            include('nl')
        ],
        'tsqs': [
            (r"'''", String, '#pop'),
            include('strings'),
            include('nl')
        ],
    }



#--------- Sphinx integration ------------------------------------------
def setup(_app):
    """Setup as a sphinx extension."""

    # This is only a lexer, so adding it below to Pygments appears sufficient.
    # But if somebody knows that the right API usage should be to do that via
    # Sphinx, by all means fix it here.  At least having this setup.py
    # suppresses the Sphinx warning we'd get without it.
    pass

# Register the extension as a valid Pygments lexer
highlighting.lexers['siml'] = SimlLexer()
