#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re

import pyparsing as pp

from pyparsing_ext.actions import *
from pyparsing_ext.oplists import *

'''notations:
pe: ParserElement
s: string
l, loc: location
char, chr: character
*x: extension
'''

# for short
_Enhance = pp.ParseElementEnhance
_Exception = pp.ParseException
_Token = pp.Token


# def scanFile(pe, file, *args, **kwargs):
#     """Execute the parse expression on the given file or filename.
#        If a filename is specified (instead of a file object),
#        the entire file is opened, read, and closed before parsing.
#     """
#     if isinstance(file, str):
#         with open(file) as f:
#             file_contents = f.read()
#     else: # file is a file object
#         file_contents = file.read()
#     return pe.scanString(file_contents, *args, **kwargs)

_whitepattern = re.compile(r'\A[ \n\t]+\Z')

def iswhite(s):
    # is or not whitespace
    return _whitepattern.match(s)


# useful tokens
# words
IDEN = pp.pyparsing_common.identifier
DIGIT = pp.Word(pp.nums)
WORD = pp.Word(pp.alphas, pp.alphas+'-')

# punctuations
DOT = pp.Literal('.')
STAR = pp.Literal('*')
DASH = pp.Literal('\\')
SLASH = pp.Literal('/')
PM = pp.oneOf('+ -')
_punctuation = '_[]<>%$^|{}*+/\\!~#?.:'
PUNC = pp.Word(_punctuation)

LPAREN = pp.Suppress('(')
RPAREN = pp.Suppress(')')
LBRACE = pp.Suppress('{')
RBRACE = pp.Suppress('}')
LBRACK = pp.Suppress('[')
RBRACK = pp.Suppress(']')
COLON = pp.Suppress(':')
SEMICOLON = pp.Suppress(';')
COMMA = pp.Suppress(',')

# numbers
INTEGER = pp.pyparsing_common.signed_integer
FRACTIOIN = pp.pyparsing_common.fraction
DECIMAL = pp.Combine(pp.Optional(PM) + pp.Optional(DIGIT) + DOT + DIGIT)
NUMBER = pp.pyparsing_common.fnumber | DECIMAL
STRING = pp.quotedString.setParseAction(pp.removeQuotes) | pp.QuotedString('"""', multiline=True) | pp.QuotedString("'''", multiline=True)


# subclass of Token
class Escape(_Token):
    r'''Escape Token

    It matches \ in \latex instead of second \ in \\latex.
    The motivation of the token is to parse the commands in .tex files.
'''

    def __init__(self, escChar='\\'):
        super(Escape, self).__init__()
        self.mayReturnEmpty = True
        self.mayIndexError = False
        self.escChar = escChar  #len(escChar)==1
        self.name = 'escChar(%s)'%escChar
        self.errmsg = "Expected " + self.name

    def parseImpl(self, instring, loc=0, doBaseActions=True):
        if instring[loc]==self.escChar:
            if loc==0 or instring[loc-1] != self.escChar:
                return loc+1, self.escChar
            else:
                try:
                    self.tryParse(instring, loc-1)
                except _Exception:
                    return loc+1, self.escChar
        raise _Exception(instring, loc, self.errmsg, self)


class EscapeRight(_Token):
    '''
    it matches '}' in latex} instead of first '}' in latex}}

    See also Escape
'''
    def __init__(self, escChar='}'):
        super(EscapeRight, self).__init__()
        self.mayReturnEmpty = True
        self.mayIndexError = False
        self.escChar = escChar  #  len(escChar)==1
        self.name = 'escChar(%s)'%escChar
        self.errmsg = "Expected " + self.name

    def parseImpl(self, instring, loc=0, doActions=True):
        if instring[loc] == self.escChar:
            if loc == len(instring)-1 or instring[loc+1] != self.escChar:
                return loc+1, self.escChar
            else:
                try:
                    self.tryParse(instring, loc+1)
                except _Exception:
                    return loc+1, self.escChar
        raise _Exception(instring, loc, self.errmsg, self)


class Wordx(_Token):
    """Extension of Word

    like pyparsing.Word, but initChars, bodyChars (=None) are both functions
    use 'lambda x: x not in *' to exclude '*'
    use 'lambda x: True' to match any character

    Example:
    ------
    Wordx(initChars=lambda x: x in {'a', 'b'}, bodyChars=lambda x:x in {'a', 'b', 'c'}) == (a|b)(a|b|c)*
    """
    def __init__(self, initChars, bodyChars=None, min=1, max=0, exact=0, asKeyword=False):
        """
        Arguments:
            initChars {function: string -> bool} -- the condition of initial charactor
        
        Keyword Arguments:
            bodyChars {function: string -> bool} -- the condition of body charactors (default: {None})
            ......
        """
        super(Wordx, self).__init__()
        self.initChars = initChars
        if bodyChars:
            self.bodyChars = bodyChars
        else:
            self.bodyChars = initChars

        self.maxSpecified = max > 0

        if min < 1:
            raise ValueError("cannot specify a minimum length < 1; use Optional(Word()) if zero-length word is permitted")

        if exact > 0:
            self.maxLen = self.minLen = exact
        else:
            self.minLen = min
            self.maxLen = max if max > 0 else None

        self.name = str(self)
        self.errmsg = "Expected " + self.name  # super(, self).setName(str(self))
        self.mayIndexError = False
        self.asKeyword = asKeyword


    def parseImpl(self, instring, loc=0, doActions=True):
        if not self.initChars(instring[loc]):
            raise _Exception(instring, loc, self.errmsg, self)

        start = loc
        loc += 1
        instrlen = len(instring)
        maxloc = instrlen if self.maxLen is None else min(start + self.maxLen, instrlen)
        while loc < maxloc and self.bodyChars(instring[loc]):
            loc += 1
        # from start to loc

        if loc - start < self.minLen:
            # too short
            raise _Exception(instring, loc, self.errmsg, self)
        if self.maxSpecified and loc < instrlen and self.bodyChars(instring[loc]):
            # too long
            raise _Exception(instring, loc, self.errmsg, self)
        if self.asKeyword and (start>0 and self.bodyChars(instring[start-1])) or (loc<instrlen and self.bodyChars(instring[loc])):
            # instring : bodychar + ... + bodychar
            raise _Exception(instring, loc, self.errmsg, self)

        return loc, instring[start:loc]

    def __str__(self):
        try:
            return super(Word,self).__str__()   # self.name
        except:
            pass

        if self.strRepr is None:

            if self.initChars != self.bodyChars:
                self.strRepr = "W:(head:%s, body:%s)" % (self.initChars.__name__, self.bodyChars.__name__)
            else:
                self.strRepr = "W:(all:%s)" % self.initChars.__name__

        return self.strRepr


class CharsNot(_Token):
    """behaves like pyparsing.CharsNotIn but notChars is a function

    See also:
        Wordx
    """
    def __init__(self, notChars, min=1, max=0, exact=0):
        super(CharsNot, self).__init__()
        self.skipWhitespace = False
        self.notChars = notChars

        if min < 1:
            raise ValueError("cannot specify a minimum length < 1; use Optional(CharsNot(*)) if zero-length char group is permitted")

        if exact > 0:
            self.maxLen = self.minLen = exact
        else:
            self.minLen = min
            self.maxLen = max if max>0 else sys.maxsize  # None

        self.name = str(self)
        self.errmsg = "Expected " + self.name
        self.mayReturnEmpty = self.minLen == 0
        self.mayIndexError = False

    def parseImpl(self, instring, loc, doActions=True):
        if instring[loc] in self.notChars:
            raise _Exception(instring, loc, self.errmsg, self)

        start = loc
        loc += 1
        maxlen = min(start+self.maxLen, len(instring))  # if self.maxlen == None
        while loc < maxlen and not self.notChars(instring[loc]):
            loc += 1

        if loc - start < self.minLen:
            # too short
            raise _Exception(instring, loc, self.errmsg, self)

        return loc, instring[start:loc]

    def __str__(self):
        try:
            return super(CharsNot, self).__str__()
        except:
            pass

        if self.strRepr is None:
            self.strRepr = "W:(not %s)" % self.notChars.__name__

        return self.strRepr


# functions returning Wordx
def keyRange(start=None, end=None, key=ord, *arg, **kwargs):
    '''Range-like parser, more powerful then srange
    
    Keyword Arguments:
        start, end {number or other type that can be compared}
        key {function:charactor->number} (default: {ord})
    
    Returns:
        Wordx whose characters satisfy start<=key(x)<=end
    '''
    if end is None:
        func = lambda x: start <= key(x)
    else:
        if start is None:
            func = lambda x: key(x) <= end
        else:
            func = lambda x: start <= key(x) <= end
    return Wordx(func, *arg, **kwargs)

def ordRange(start=None, end=None, *arg, **kwargs):
    '''Special keyRange

    return Wordx in which the characters satisfy start<=ord(x)<=end

    Examples:
    --------
    >>> cjk = ordRange(0x4E00, 0x9FD5)
    >>> cjk.parseString('我爱你, I love you') # => ['我爱你']
    '''
    return keyRange(start, end, key=ord, *arg, **kwargs)

# parse natural languages based on ordRange
# def CJK(*arg, **kwargs):
#     # Chinese Japanese Korean
#     return ordRange(0x4E00, 0x9FD5, *arg, **kwargs)

# def chinese(*arg, **kwargs):
#     # chinese
#     return ordRange(start=0x4E00, end=0x9FA5, *arg, **kwargs)

# def hiragana(*arg, **kwargs):
#     # japanese
#     return ordRange(0x3040, 0x309F, *arg, **kwargs)

# def katakana(*arg, **kwargs):
#     # japanese
#     return ordRange(0x30A0, 0x30FF, *arg, **kwargs)

# def korean(*arg, **kwargs):
#     return ordRange(0x1100, 0x11FF, *arg, **kwargs)
#     

# def pinyin(*arg, **kwargs):
#     return ordRange(0x3100, 0x312F, *arg, **kwargs)


def chrRange(start='', end=None, *arg, **kwargs):
    # return keyRange(start='', end=None, key=lambda x: x, *arg, **kwargs)
    if end is None:
        func = lambda x: start <= x <= end
    else:
        func = lambda x: start <= x
    return Wordx(func, *arg, **kwargs)

def keyRanges(ran, key=ord, *arg, **kwargs):
    '''Multi-range version of keyRange
    
    We can take ran several ranges, instead of just one in keyRange
    
    Arguments:
        ran {tuple} -- ranges of key(x), see also keyRange
                       (a, b, c, d) means (union of) two ranges a-b and c-d
    
    Keyword Arguments:
        key {function} -- function from charactor to number (default: {ord})
    
    Returns:
        Wordx
    '''

    L = len(ran)    # L >= 1
    if L % 2 == 0:
        func = lambda x: any(ran[k] <= key(x) <= ran[k+1] for k in range(0, L, 2))
    else:
        func = lambda x: any(ran[k] <= key(x) <= ran[k+1] for k in range(0, L, 2)) or ran[-1] <= key(x)
    return Wordx(func, *arg, **kwargs)

def ordRanges(ran, *arg, **kwargs):
    '''Special keyRanges
    
    Examples:
    -------
    >>> cjk = ordRanges((0x4E00, 0x9FD5, 0, 256))
    >>> cjk.parseString('我爱你 I love you') # => ['我爱你 I love you']
    '''

    return keyRanges(ran, key=ord, *arg, **kwargs)

def chrRanges(ran, *arg, **kwargs):
    # Special keyRanges
    L = len(ran)    # L >= 1
    if L%2 == 0:
        func = lambda x: any(ran[k] <= x <= ran[k+1] for k in range(0, L//2, 2))
    else:
        func = lambda x: any(ran[k] <= x <= ran[k+1] for k in range(0, L//2, 2)) or ran[-1] <= x
    return Wordx(func, *arg, **kwargs)


# subclass of ParserElementEnhance

class Meanwhile(pp.ParseExpression):
    """Parse expression whose all sub-expressions have to be matched at the same time

        Grammar:
            Meanwhile([A, B, ...]), where A, B, ... are parse expressions.
       
        Example:
            >>> A = Meanwhile([IDEN, ~('_'+ DIGIT)]) # IDEN % ('_'+ DIGIT) for short
            >>> to parse identifiers such as _a123 excluding _123
            >>> A.parseString('_a123')  # => ['_a123']
            >>> A.parseString('_123')   # => ParseException

            >>> A = Meanwhile([IDEN, pp.Word('?_123456xend'), pp.Word('_+-*/123x')+'end']) # (_|x) (_123x)* end
            >>> A.parseString('_xend')  # => ['_xend']
            >>> A.parseString('_123end') # => ['_123end']
            >>> A.parseString('_abc')   # => ParseException
    """

    def __init__(self, exprs=[]):
        '''
        Keyword Arguments:
            exprs {list} -- list of parse expressions (default: {[]})
        '''
        super(Meanwhile, self).__init__(exprs)
        self.mayReturnEmpty = all(e.mayReturnEmpty for e in self.exprs)
        self.setWhitespaceChars(self.exprs[0].whiteChars)
        self.skipWhitespace = self.exprs[0].skipWhitespace
        self.callPreparse = True

    def parseImpl(self, instring, loc, doActions=True):
        postloc, result = self.exprs[0]._parse(instring, loc, doActions)
        for e in self.exprs[1:]:
            if not e.matches(instring[loc:], parseAll=True):
                raise _Exception(instring, len(instring), e.errmsg, self)
        return postloc, result

    def __mod__(self, other):
        if isinstance(other, str):
            other = pp.ParserElement._literalStringClass(other)
        return self.exprs.append(~other)

    def checkRecursion(self, parseElementList):
        subRecCheckList = parseElementList[:] + [self]
        for e in self.exprs:
            e.checkRecursion(subRecCheckList)
            if not e.mayReturnEmpty:
                break

    def __str__(self):
        if hasattr(self, "name"):
            return self.name

        if self.strRepr is None:
            self.strRepr = "%s{%s}"%(str(self.exprs[0]), " ".join(str(e) for e in self.exprs[1:]))

        return self.strRepr


class TokenConverterx(_Enhance):
    """Abstract subclass of ParseElementEnhance, for converting parsed results.
    it and its subclasses override postParse
    Compared with pyparsing.TokenConverter, it has property 'converter' that
    maps (instring, loc, tokenlist) to tokenlist"""
    def __init__(self, expr, savelist=False, converter=None):
        # converter: tokens -> tokens
        super(TokenConverterx, self).__init__(expr) #, savelist )
        self.saveAsList = False
        self.converter = converter

    def postParse(self, instring, loc, tokenlist):
        if self.converter is None:
            return tokenlist
        else:
            return self.converter(instring, loc, tokenlist)


class StrConverter(TokenConverterx):
    """Converte strings in the matching tokens."""
    def __init__(self, expr, savelist=False, mapping=None):
        # mapping: str -> str
        converter = lambda ins, loc, lst: list(map(mapping, lst)) if mapping is not None else None
        super(StrConverter, self).__init__(expr, savelist, converter=converter)


class StripConverter(StrConverter):
    """Converte strings in the matching tokens."""
    def __init__(self, expr, ch=None):
        # mapping: str -> str
        mapping = lambda s: s.strip(ch) if ch else lambda s: s.strip()
        super(StripConverter, self).__init__(expr, savelist=False, mapping=mapping)


class DeleteConverter(StrConverter):
    """Converte strings in the matching tokens."""
    def __init__(self, expr):
        # mapping: str -> str
        mapping = lambda s: ''
        super(DeleteConverter, self).__init__(expr, savelist=False, mapping=mapping)


class DictConverter(TokenConverterx):
    """Converte strings in the matching tokens."""
    def __init__(self, expr, savelist=False, dict_=None):
        # mapping: str -> str
        converter = lambda ins, loc, lst: [dict_[a] for a in lst] if dict_ is not None else None
        super(DictConverter, self).__init__(expr, savelist, converter=converter)


class LinenStart(pp._PositionToken):
    """Matches if current position is at the beginning of the n-th line within the parse string
    """
    def __init__(self, n=1):
        super(LineStart, self).__init__()
        self.setWhitespaceChars(ParserElement.DEFAULT_WHITE_CHARS.replace("\n",""))
        self.errmsg = "Expected start of the %d-th line"%n
        self.linen = n

    def preParse(self, instring, loc):
        preloc = super(LinenStart, self).preParse(instring, loc)
        if instring[preloc] == "\n":
            loc += 1
        return loc

    def parseImpl(self, instring, loc, doActions=True):
        # at the beginning of the whole string or at the beginning of the n-th line
        if loc==0 and self.linen==1 or instring[0:loc-1].count('\n')==self.linen-1 and instring[loc-1]=="\n":
            return loc, []
        raise ParseException(instring, loc, self.errmsg, self)

