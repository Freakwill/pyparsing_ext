# -*- coding: utf-8 -*-
'''pyparsing_ext (extension of module pyparsing)

Application: text parsing
Require: pyparsing
-------------------------------
Path:
Author: William
'''

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
DIGIT = pp.pyparsing_common.integer
WORD = pp.Word(pp.alphas, pp.alphas+'-')

# punctuations
DOT = pp.Literal('.')
STAR = pp.Literal('*')
DASH = pp.Literal('\\')
COMMA = pp.Literal(',')
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

# numbers
INTEGER = pp.pyparsing_common.signed_integer
FRACTIOIN = pp.Optional(PM) + DIGIT + SLASH + DIGIT
DECIMAL = pp.Combine(pp.Optional(PM) + pp.Optional(DIGIT) + DOT + DIGIT)
NUMBER = pp.Combine(pp.Optional(PM) + DIGIT + pp.Optional(DOT + DIGIT)) | DECIMAL
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
    example:
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


class TestToken(_Token):
    # test token
    def __init__(self, test=None):
        super(TestToken, self).__init__()
        self.test = test
        self.errmsg = "did not pass the test!"

    def parseImpl(self, instring, loc=0, doActions=True):
        if self.test is None:
            return loc, []
        elif self.test(instring, loc):
            return loc, []
        else:
            raise _Exception(instring, loc, self.errmsg, self)

    def __str__(self):
        return 'this is a test'

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
    '''return Wordx in which the characters satisfy start<=ord(x)<=end'''
    return keyRange(start, end, key=ord, *arg, **kwargs)

# parse natural languages based on ordRange
def CJK(*arg, **kwargs):
    # Chinese Japanese Korean
    return ordRange(0x4E00, 0x9FD5, *arg, **kwargs)

def chinese(*arg, **kwargs):
    # chinese
    return ordRange(start=0x4E00, end=0x9FA5, *arg, **kwargs)

def hiragana(*arg, **kwargs):
    # japanese
    return ordRange(0x3040, 0x309F, *arg, **kwargs)

def katakana(*arg, **kwargs):
    # japanese
    return ordRange(0x30A0, 0x30FF, *arg, **kwargs)

def korean(*arg, **kwargs):
    return ordRange(0x1100, 0x11FF, *arg, **kwargs)

def chrRange(start='', end=None, *arg, **kwargs):
    # return keyRange(start='', end=None, key=lambda x: x, *arg, **kwargs)
    if end is None:
        func = lambda x: start <= x <= end
    else:
        func = lambda x: start <= x
    return Wordx(func, *arg, **kwargs)

# def pinyin(*arg, **kwargs):
#     return ordRange(0x3100, 0x312F, *arg, **kwargs)

def keyRanges(ran, key=ord, *arg, **kwargs):
    # ran = (a,b,c,d) means two ranges a-b and c-d
    # multi-range version of keyRange
    L = len(ran)    # L >= 1
    if L%2 == 0:
        func = lambda x: any(ran[k] <= ord(x) <= ran[k+1] for k in range(0, L//2, 2))
    else:
        func = lambda x: any(ran[k] <= ord(x) <= ran[k+1] for k in range(0, L//2, 2)) or ran[-1] <= ord(x)
    return Wordx(func, *arg, **kwargs)

def ordRanges(ran, *arg, **kwargs):
    # ran = (a,b,c,d) means two ranges a-b and c-d
    # multi-range version of ordRange
    return keyRanges(ran, key=ord, *arg, **kwargs)

def chrRanges(ran, *arg, **kwargs):
    # multi-range version of chrRange
    # ran = (a,b,c,d) means two ranges a-b and c-d
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
            if not e.matches(instring, loc):
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


# helpers:
def enumeratedItems(baseExpr=None, form='[1]', **min_max):
    if form is None:
        form = '[1]'
    if '1' in form:
        no = pp.Regex(re.escape(form).replace('1','(?P<no>\\d+)')) #.setParseAction(lambda x:x.no)
    else:
        no = pp.Regex(re.escape(form))
    # no.suppress()
    if 'exact' in min_max and min_max['exact'] > 0:
        max_ = min_ = exact
    else:
        min_ = min_max.get('min', 0)
        max_ = min_max.get('max', None)
    if baseExpr is None:
        return (pp.Group(no + pp.SkipTo(pp.StringEnd() | no).setParseAction(_strip()))) * (min_, max_)
    else:
        return (pp.Group(no + baseExpr.setParseAction(_strip()))) * (min_, max_)

def _strip(ch=None):
    if ch is None:
        return lambda s, l, t: t[0].strip()
    else:
        return lambda s, l, t: t[0].strip(ch)


def delimitedMatrix(baseExpr=pp.Word(pp.alphanums), ch1=',', ch2=';'):
    r'''works like delimitedList
    exmpale:
    'a b\nc d' => [['a', 'b'], ['c', 'd']]
    '''
    if ch1 == ch2:
        raise Exception('make sure ch1 != ch2')
    if isinstance(ch1, str):
        if ch1 is '':
            raise Exception('make sure ch1 is not empty')
        if iswhite(ch1):
            ch1 = pp.Literal(ch1).leaveWhitespace()
        else:
            ch1 = pp.Literal(ch1)
    if isinstance(ch2, str):
        if ch2 is '':
            raise Exception('make sure ch2 is not empty')
        if iswhite(ch2):
            ch2 = pp.Literal(ch2).leaveWhitespace()
        else:
            ch2 = pp.Literal(ch2)
    return pp.delimitedList(pp.Group(pp.delimitedList(baseExpr, ch1.suppress())), ch2.suppress())


# need to be improved
class MixedExpression(_Enhance):
    '''MixedExpression has 4 (principal) propteries
    baseExpr: baseExpr
    opList: opList
    lpar: lpar
    rpar: rpar'''
    def __init__(self, baseExpr, opList=[], lpar=LPAREN, rpar=RPAREN, *args, **kwargs):
        super(MixedExpression, self).__init__(baseExpr, *args, **kwargs)
        self.baseExpr = baseExpr
        self.opList = opList
        self.lpar = lpar
        self.rpar = rpar
        self.expr = pp.infixNotation(baseExpr, opList, lpar, rpar)

    def enableIndex(self, action=IndexOpAction):
        # start:stop:step
        EXP = pp.Forward()
        SLICE = pp.Optional(EXP)('start') + COLON + pp.Optional(EXP)('stop') + pp.Optional(COLON + pp.Optional(EXP)('step'))
        indexop = LBRACK + (SLICE('slice') | EXP('index')) + RBRACK
        indexop.setParseAction(action)
        self.opList.insert(0, indexop)
        self.expr <<= pp.infixNotation(EXP, self.opList, self.lpar, self.rpar)

    def enableCall(self, action=CallOpAction):
        EXP = self.expr
        KWARG = IDEN + pp.Suppress('=') + EXP
        # STAR = pp.Suppress('*') + EXP, DBLSTAR = pp.Suppress('**') + EXP
        callop = LPAREN + pp.Optional(pp.delimitedList(EXP))('args') + pp.Optional(pp.delimitedList(KWARG))('kwargs') + RPAREN
        callop.setParseAction(action)
        self.opList.insert(0, callop)
        self.expr <<= pp.infixNotation(self.baseExpr, self.opList, self.lpar, self.rpar)

    def enableDot(self, action=DotOpAction):
        EXP = self.expr
        dotop = pp.Suppress('.') + IDEN('attr')
        dotop.setParseAction(action)
        self.opList.insert(0, dotop)
        self.expr <<= pp.infixNotation(self.baseExpr, self.opList, self.lpar, self.rpar)


    def enableAll(self, actions=None):
        self.enableIndex()
        self.enableCall()
        self.enableDot()


def mixedExpression(baseExpr, func=None, flag=False, opList=[], lpar=LPAREN, rpar=RPAREN):
    '''mixed expression (return ParserElementEnhance)
    func: function of baseExpr (can be distincted by first token)

    call operatorPrecedence
    example:
    def func(EXP):
        return pp.Group('<' + EXP + ',' + EXP +'>')| pp.Group('||' + EXP + '||') | pp.Group('|' + EXP + '|') | pp.Group(IDEN + '(' + pp.delimitedList(EXP) + ')')
    EXP = mixedExpression(baseExpr, func, arithOplist)
    '''
    
    EXP = pp.Forward()
    if flag:
        # expression as a[d].b(c)
        SLICE = pp.Optional(EXP)('start') + COLON + pp.Optional(EXP)('stop') + pp.Optional(COLON + pp.Optional(EXP)('step'))
        indexop = LBRACK + (SLICE('slice') | EXP('index')) + RBRACK
        indexop.setParseAction(IndexOpAction) # handle with x[y]
        KWARG = IDEN + pp.Suppress('=') + EXP
        # STAR = pp.Suppress('*') + EXP; DBLSTAR = pp.Suppress('**') + EXP
        callop = LPAREN + pp.Optional(pp.delimitedList(EXP))('args') + pp.Optional(pp.delimitedList(KWARG))('kwargs') + RPAREN
        callop.setParseAction(CallOpAction)  # handle with f(x)
        dotop = pp.Suppress('.') + IDEN('attr')
        dotop.setParseAction(DotOpAction)    # handle with x.y
        opList.insert(0, (indexop | callop | dotop, 1, pp.opAssoc.LEFT, ICDAction))
    
    if func:
        if isinstance(func, pp.ParserElement):
            f = pp.Group(func + LPAREN + pp.delimitedList(EXP) + RPAREN)
            block = f | baseExpr
        else:  # func is callable
            block = func(EXP) | baseExpr
        EXP <<= pp.infixNotation(block, opList, lpar, rpar)
    else:
        EXP <<= pp.infixNotation(baseExpr, opList, lpar, rpar)
    return EXP



def logicterm(constant=DIGIT, variable=IDEN, function=IDEN, lambdaterm=False):
    # f(x,y...) | const | x
    if lambdaterm:
        function = function | lambdaterm(variable, lambdaKeyword='lambda')
    t = pp.Forward()
    t <<= (function('function') + LPAREN + pp.delimitedList(t)('args') + RPAREN).setParseAction(FunctionAction) | (constant | variable).setParseAction(AtomAction)
    return t


def lambdaterm(variable=IDEN, lambdaKeyword='lambda'):
    # lambda variable: expression
    t = pp.Forward()
    t <<= pp.Suppress(lambdaKeyword) + pp.delimitedList(variable)('args') + (t | logicterm(constant=DIGIT, variable=IDEN, function=None))('term')
    t.setParseAction(LambdaAction)
    return t
