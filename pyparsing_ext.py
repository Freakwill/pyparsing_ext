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
import functools

import pyparsing as pp


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


def scanFile(pe, file, *args, **kwargs):
    """Execute the parse expression on the given file or filename.
       If a filename is specified (instead of a file object),
       the entire file is opened, read, and closed before parsing.
    """
    if isinstance(file, str):
        with open(file) as f:
            file_contents = f.read()
    else: # file is a file object
        file_contents = file.read()
    return pe.scanString(file_contents, *args, **kwargs)

_whitepattern = re.compile('\A[ \n\t]+\Z')

def iswhite(s):
    # is or not whitespace
    return _whitepattern.match(s)


# useful tokens
# words
IDEN = pp.pyparsing_common.identifier
DIGIT = pp.pyparsing_common.integer
WORD = pp.Word(pp.alphas+'-')

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
class Escape(pp.Token):
    '''escape character
    it matches \ in \latex instead of second \ in \\latex
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


class EscapeRight(pp.Token):
    '''escape character
    it matches '}' in latex} instead of first '}' in latex}}
'''
    def __init__(self, escChar='}'):
        super(EscapeRight, self).__init__()
        self.mayReturnEmpty = True
        self.mayIndexError = False
        self.escChar = escChar  #len(escChar)==1
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


class Wordx(pp.Token):
    """extension of Word
    like pyparsing.pWord, but initChars, bodyChars (=None) are both functions
    use 'lambda x: x not in *' to exclude *
    use 'lambda x: True' to match any character
    example:
    Wordx(initChars=lambda x: x in {'a', 'b'}, bodyChars=lambda x:x in {'a', 'b', 'c'}) == (a|b)(a|b|c)*
    """
    def __init__(self, initChars, bodyChars=None, min=1, max=0, exact=0, asKeyword=False):
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


class CharsNot(pp.Token):
    """behaves like pyparsing.CharsNotIn but notChars is a function
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

    def __str__(self ):
        try:
            return super(CharsNot, self).__str__()
        except:
            pass

        if self.strRepr is None:
            self.strRepr = "W:(not %s)" % self.notChars.__name__

        return self.strRepr


class TestToken(pp.Token):
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
    '''return Wordx in which the characters satisfy start<=key(x)<=end
    key [ord]: function (just use ordRange)
    start, end [None]: number or other type that can be compared'''
    if end is None:
        if start is None:
            func = lambda x: key(x) <= end
        else:
            func = lambda x: start <= key(x) <= end
    else:
        func = lambda x: start <= key(x)
        # if start is None: func = lambda x: True # deprecated
    return Wordx(func, *arg, **kwargs)

def ordRange(start=None, end=None, *arg, **kwargs):
    '''return Wordx in which the characters satisfy start<=ord(x)<=end'''
    return keyRange(start, end, key=ord, *arg, **kwargs)

# parse natural languages based on ordRange
def CJK(*arg, **kwargs):
    # Chinese Japanese Korean
    return ordRange(0x4E00, 0x9FD5, *arg, **kwargs)

def kangxi(*arg, **kwargs):
    # chinese
    return ordRange(0x2F00, 0x2FDF, *arg, **kwargs)
chinese = kangxi

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
class LeadedBy(_Enhance):
    """
    Works as FollowedBy

    Lookahead matching of the given parse expression.  C{LeadedBy}
    does not advance the parsing position within the input string, it only
    verifies that the specified parse expression matches at the current
    position.  C{LeadedBy} always returns a null token list."""
    def __init__(self, expr, start=0, retreat=None):
        super(LeadedBy, self).__init__(expr)
        self.mayReturnEmpty = True
        self.start = start
        self.retreat = retreat

    def parseImpl(self, instring, loc=0, doActions=True):
        if self.retreat is None:
            start = self.start
        else:
            start = loc - self.retreat
        if (self.expr + stringEnd).searchString(instring[start:loc], maxMatches=1):
            return loc, []
        else:
            raise _Exception(instring, loc, self.errmsg, self)


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

class Meanwhile(pp.ParseExpression):
    """ Meanwhile([A, B, ...])
       example:
       A = Meanwhile([IDEN, ~('_'+ DIGIT)]) # IDEN / ('_'+ DIGIT)
       to parse identitiers such as _a123 excluding _123
    """
    def __init__(self, exprs):
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

    def append(self, other):
        if isinstance(other, str):
            other = pp.ParserElement._literalStringClass(other)
        return self.append(other)

    def exclude(self, other):
        return self.append(~other)

    def __truediv__(self, other):
        return self.append(~other)

    def checkRecursion(self, parseElementList):
        subRecCheckList = parseElementList[:] + [self]
        for e in self.exprs:
            e.checkRecursion(subRecCheckList)
            if not e.mayReturnEmpty:
                break

    def __str__( self ):
        if hasattr(self, "name"):
            return self.name

        if self.strRepr is None:
            self.strRepr = str(self.exprs[0]) + "{%s}"%(" ".join(str(e) for e in self.exprs[1:]))

        return self.strRepr

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
    """Matches if current position is at the beginning of the n-th line within the parse string"""
    def __init__(self, n=1):
        super(LineStart,self).__init__()
        self.setWhitespaceChars( ParserElement.DEFAULT_WHITE_CHARS.replace("\n","") )
        self.errmsg = "Expected start of the %d-th line"%n
        self.linen = n

    def preParse(self, instring, loc):
        preloc = super(LinenStart,self).preParse(instring,loc)
        if instring[preloc] == "\n":
            loc += 1
        return loc

    def parseImpl(self, instring, loc, doActions=True):
        if loc==0 and self.linen==1 or instring[0:loc-1].count('\n')==self.linen-1 and  instring[loc-1]=="\n":
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
        return (pp.Group(no + pp.SkipTo(pp.StringEnd() | no).setParseAction(strip()))) * (min_, max_)
    else:
        return (pp.Group(no + baseExpr.setParseAction(strip()))) * (min_, max_)

def strip(ch=None):
    if ch is None:
        return lambda s, l, t: t[0].strip()
    else:
        return lambda s, l, t: t[0].strip(ch)


def delimitedMatrix(baseExpr=pp.Word(pp.alphanums), ch1=',', ch2=';'):
    '''works like delimitedList
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
            ch1=pp.Literal(ch1)
    if isinstance(ch2, str):
        if ch2 is '':
            raise Exception('make sure ch2 is not empty')
        if iswhite(ch2):
            ch2 = pp.Literal(ch2).leaveWhitespace()
        else:
            ch2=pp.Literal(ch2)
    return pp.delimitedList(pp.Group(pp.delimitedList(baseExpr, ch1.suppress())), ch2.suppress())


# classes for actions
class BaseAction:
    '''Base class for parsing action classes
    '''
    def __init__(self, tokens, *args, **kwargs):  # instring, loc,
        self.tokens = tokens
        #self.instring = instring
        #self.loc = loc

    def has(self, name):
        return name in self.tokens

    def __len__(self):
        return len(self.tokens)

    def __eq__(self, other):
        if isinstance(other, BaseAction):
            return self.tokens == other.tokens
        else:
            return self.tokens == other

    def __repr__(self):
        return ' '.join(map(str, self.tokens))

    def __call__(self, *args, **kwargs):
        # if eval defined in action
        return self.eval(*args, **kwargs)

    def eval(self, *args, **kwargs):
        # evaluate it
        pass

    def execute(self, *args, **kwargs):
        pass

class VarOpAction(BaseAction):
    # for operators with variables
    pass


class CallOpAction(VarOpAction):
    '''x(args, kwargs=values) where (args, kwargs=values) is an operator and x is the corresponding operand
    distinguished with f(x)
    '''
    def __init__(self, tokens):
        super(IndexOpAction, self).__init__(tokens)
        self.args = tokens.args if self.has('args') else ()
        self.kwargs = dict(zip(tokens.kwargs[::2], tokens.kwargs[1::2])) if self.has('kwargs') else {}


class DotOpAction(VarOpAction):
    # x.attr
    def __init__(self, tokens):
        super(IndexOpAction, self).__init__(tokens)
        self.attr = tokens.attr

    def eval(self, calculator):
        return self.attr.eval(calculator)

class IndexOpAction(VarOpAction):
    # x[start:stop]
    def __init__(self, tokens):
        super(IndexOpAction, self).__init__(tokens)
        if self.has('slice'):
            slc = tokens.slice
            self.start = slc.start if 'start' in slc else None
            self.stop = slc.stop if 'stop' in slc else None
            self.step = slc.step if 'step' in slc else None
        else:
            self.index = tokens.index

    def eval(self, calculator):
        if self.has('slice'):
            return slice(self.start.eval(calculator), self.stop.eval(calculator), self.step.eval(calculator))
        else:
            return self.index.eval(calculator)


# operators, arithmetic, mathematics, logic:
def _tosx(x):
    return x if isinstance(x, str) else x.sexpr()

# actions for expressions
class FunctionAction(BaseAction):
    '''action class for function function(args)
       properties: 
       function: a function
       args: the arguments of the function'''
    def __init__(self, tokens):
        super(FunctionAction, self).__init__(tokens)
        if 'function' in tokens:
            self.function = tokens.function
        if 'args' in tokens:
            self.args = tokens.args

    def __eq__(self, other):
        if isinstance(other, FunctionAction):
            return self.args == other.args and self.function == other.function
        else:
            return self.args == other[1:] and self.function == other[0]

    def __repr__(self):
        return "%s(%s)"%(self.function, ', '.join(map(str, self.args)))

    def sexpr(self):
        return "(%s %s)"%(_tosx(self.function) , ' '.join(_tosx(arg) for arg in self.args))

    def arity(self):
        return len(self.args)

    def eval(self, calculator):
        # calculator(self.function, *self.args)
        return calculator(self.function, *(arg.eval(calculator) for arg in self.args))


class OperatorAction(FunctionAction):
    pass

 
class BifixAction(FunctionAction):
    '''action class for bifix operator such as 
    |x|=abs(x) or ||x||=norm(x) or <x,y>=inner product of x and y;
    bifix operator has function of parentheses
    parentheses in the expression (<x, y>) is tedious'''
    def __init__(self, tokens):
        super(BifixAction, self).__init__(tokens)
        if self.has('args'):
            self.args = tokens.args
        else:
            self.args = [tokens.arg]
        self.function = (tokens.left, tokens.right)


class InfixOperatorAction(OperatorAction):
    # action class for operators used in operatorPrecedence
    def __init__(self, tokens):
        super(InfixOperatorAction, self).__init__(tokens[0])


class UnaryOperatorAction(InfixOperatorAction):
    # action class for unary operators used in operatorPrecedence
    def __init__(self, tokens):
        super(UnaryOperatorAction, self).__init__(tokens)
        self.function, self.args = self.tokens[0], (self.tokens[1],)
        self.operand = self.tokens[1]

    def eval(self, calculator):
        # calculator(self.function, *self.args)
        return calculator(self.function, self.operand.eval(calculator))

class RightUnaryOperatorAction(UnaryOperatorAction):
    pass

class LeftUnaryOperatorAction(UnaryOperatorAction):
    '''action class for unary operators used in operatorPrecedence
    such as a*, a' '''
    def __init__(self, tokens):
        super(UnaryOperatorAction, self).__init__(tokens)
        self.function, self.args = self.tokens[1], (self.tokens[0],)
        self.operand = self.tokens[0]

class ICDAction(LeftUnaryOperatorAction):
    '''action for index, call and dot:
    a[...], a(...), a.xxx where a is an operand'''
    def __init__(self, tokens):
        super(ICDAction, self).__init__(tokens)
        self.ops = self.tokens[1:]
        self.operand = self.tokens[0]

    def eval(self, calculator):
        retval = self.operand.eval(calculator)
        for op in self.ops:
            if isinstance(op, IndexOpAction):
                retval = retval[op.eval(calculator)]
            elif isinstance(op, CallOpAction):
                args = (arg.eval(calculator) for args in op.args)
                kwargs = {k:v.eval(calculator) for k, v in op.kwargs.items()}
                retval = retval(*args, **kwargs)
            elif isinstance(op, DotOpAction):
                retval = getattr(retval, op.eval(calculator))
        return retval


class BinaryOperatorAction(InfixOperatorAction):
    # action class for binary operators used in operatorPrecedence
    def __init__(self, tokens):
        super(BinaryOperatorAction, self).__init__(tokens)
        tokens = tokens[0]
        self.args = self.tokens[0::2]
        if len(set(self.tokens[1::2]))==1:
            self.ishybrid = False
            self.function = self.tokens[1]
        else:
            self.ishybrid = True
            self.function = self.tokens[1::2]

    def prefix(self):
        if not self.ishybrid:
            return "%s(%s)" %(self.function, ', '.join(map(str, self.args)))
        else:
            return "(%s)(%s)" %(', '.join(self.function), ', '.join(map(str, self.args)))

    def __repr__(self):
        if not self.ishybrid:
            return (' %s '%self.function).join(map(str, self.args))
        else:
            s = str(self.args[0])
            for k, f in enumerate(self.function):
                s += ' %s %s'%(f, self.args[k])
            return s

    def sexpr(self):
        if not self.ishybrid:
            return "(%s %s)" %(_tosx(self.function), ' '.join(_tosx(arg) for arg in self.args))
        else:
            return "((%s) %s)" %(', '.join(self.function), ' '.join(map(_tosx, self.args)))

    def eval(self, calculator):
        # calculator(self.function, *self.args)
        args = tuple(arg.eval(calculator) for arg in self.args)
        if self.ishybrid:
            ret = calculator(self.function[0])(args[0], args[1])
            for f, arg in zip(self.function[1:], self.args[2:]):
                ret = calculator(f)(ret, arg)
            return ret
        else:
            return functools.reduce(calculator(self.function), args)


class LeftBinaryOperatorAction(BinaryOperatorAction):
    pass


class RightBinaryOperatorAction(BinaryOperatorAction):

    def eval(self, calculator):
        args = tuple(arg.eval(calculator) for arg in self.args)
        if self.ishybrid:
            ret = calculator(self.function[-1])(args[-2], args[-1])
            for f, arg in zip(self.function[-2::-1], args[-3::-1]):
                ret = calculator(f)(arg, ret)
            return ret
        else:
            f = calculator(self.function)
            ret = f(args[-2], args[-1])
            for arg in args[-3::-1]:
                ret = f(arg, ret)
            return ret

class CompareAction(BinaryOperatorAction):
    # action for comparison
    def eval(self, calculator):
        args = tuple(arg.eval(calculator) for arg in self.args)
        if self.ishybrid:
            for k, f in enumerate(self.function):
                f = calculator(self.function)
                if not f(args[k], args[k+1]):
                    return False
            return True
        else:
            f = calculator(self.function)
            for k in range(len(args)-1):
                if not f(args[k], args[k+1]):
                    return False
            return True


class TernaryOperatorAction(OperatorAction):
    # action class for ternary operators used in operatorPrecedence
    def __init__(self, tokens):
        super(TernaryOperatorAction, self).__init__(tokens)
        tokens = tokens[0]
        self.function = self.tokens[1], self.tokens[3]
        self.args = self.tokens[0], self.tokens[2], self.tokens[4]

    def __repr__(self):
        return "(%s, %s)(%s)" %(self.function[0], self.function[1], ', '.join(map(str, self.args)))

    def sexpr(self):
        return "((%s, %s) %s)" %(self.function[0], self.function[1], ', '.join(map(str, self.args)))


class Operator(object):
    '''Operator has 4 (principal) propteries
    symbol: the symbol of operator
    arity: arity
    assoc: assoc method
    action: action'''
    def __init__(self, symbol, arity=2, assoc=pp.opAssoc.LEFT, action=None):
        self.symbol = symbol
        self.arity = arity
        self.assoc = assoc
        self.action = action

    def __getitem__(self, k):
        return (self.symbol, self.arity, self.assoc, self.action)[k]


arithOplist = [('**', 2, pp.opAssoc.RIGHT, RightBinaryOperatorAction),
    (pp.oneOf('+ - ~'), 1, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.oneOf('* / // %'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.oneOf('+ -'), 2, pp.opAssoc.LEFT, BinaryOperatorAction)]


pyOplist = arithOplist + [('&', 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    ('^', 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    ('|', 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('is') | pp.Keyword('is not'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('in') | pp.Keyword('not in'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.oneOf('< <= > >= == !='), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('not'), 1, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.Keyword('and'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('or'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    ((pp.Keyword('if'), pp.Keyword('else')), 3, pp.opAssoc.RIGHT, TernaryOperatorAction)]

# logic:
logicOplist = [(pp.Keyword('not'), 1, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.Keyword('and'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('or'), 2, pp.opAssoc.LEFT, BinaryOperatorAction)]


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
        self.expr = pp.operatorPrecedence(baseExpr, opList, lpar, rpar)

    def enableIndex(self, action=IndexOpAction):
        # start:stop:step
        self.expr = EXP = pp.Forward()
        SLICE = pp.Optional(EXP)('start') + COLON + pp.Optional(EXP)('stop') + pp.Optional(COLON + pp.Optional(EXP)('step'))
        indexop = LBRACK + (SLICE('slice') | EXP('index')) + RBRACK
        indexop.setParseAction(action)
        self.opList.insert(0, indexop)
        self.expr <<= pp.operatorPrecedence(self.baseExpr, self.opList, self.lpar, self.rpar)

    def enableCall(self, action=CallOpAction):
        self.expr = EXP = pp.Forward()
        KWARG = IDEN + pp.Suppress('=') + EXP
        # STAR = pp.Suppress('*') + EXP, DBLSTAR = pp.Suppress('**') + EXP
        callop = LPAREN + pp.Optional(pp.delimitedList(EXP))('args') + pp.Optional(pp.delimitedList(KWARG))('kwargs') + RPAREN
        indexop = LBRACK + (SLICE('slice') | EXP('index')) + RBRACK
        callop.setParseAction(action)
        self.opList.insert(0, callop)
        self.expr <<= pp.operatorPrecedence(self.baseExpr, self.opList, self.lpar, self.rpar)

    def enableDot(self, action=DotOpAction):
        dotop = pp.Suppress('.') + IDEN('attr')
        dotop.setParseAction(action)
        self.opList.insert(0, dotop)


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
    EXP = mixedExpression(baseExpr, func, arithOplist)'''
    
    EXP = pp.Forward()
    if flag:
        # expression as a[d].b(c)
        SLICE = pp.Optional(EXP)('start') + COLON + pp.Optional(EXP)('stop') + pp.Optional(COLON + pp.Optional(EXP)('step'))
        indexop = LBRACK + (SLICE('slice') | EXP('index')) + RBRACK
        indexop.setParseAction(IndexOpAction) # handle with x[y]
        KWARG = IDEN + pp.Suppress('=') + EXP
        # STAR = pp.Suppress('*') + EXP, DBLSTAR = pp.Suppress('**') + EXP
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
        EXP <<= pp.operatorPrecedence(block, opList, lpar, rpar)
    else:
        EXP <<= pp.operatorPrecedence(baseExpr, opList, lpar, rpar)
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

class LambdaAction(BaseAction):
    # action class for lambda expression used in operatorPrecedence
    def __init__(self, tokens):
        super(LambdaAction, self).__init__(tokens)
        self.args, self.expr = tokens.args, tokens.expression
        self.lambdaKeyword='lambda'

    def __repr__(self):
        return "%s %s: %s"%(self.lambdaKeyword, ', '.join(map(str, self.args)), self.expr)

    def sexpr(self):
        return "(%s (%s) %s)"%(self.lambdaKeyword, ' '.join(map(str, self.args)), self.expr.sexpr())

    def eval(self, calculator):
        localcalculator = calculator.copy()
        def f(*args):
            localcalculator.update({arg:v for arg, v in zip(self.args, args)})
            return self.expr.eval(localcalculator)
        return f


# advanced functitons
def isatomic(pe):
    '''whether ParserElement pe is atomic (is an atom):
    a token is atomic
    enhancement of an atom is atomic
    expression consisting of only one atom is atomic'''
    if pe.checkRecursion([]):
        return False
    if isinstance(pe, pp.Token):
        return True
    elif isinstance(pe, _Enhance):
        return isatomic(pe.expr)
    elif isinstance(pe, pp.ParseExpression):
        if len(pe.exprs) ==1:
            return isatomic(pe.exprs[0])
        else:
            return False
    else:
        return False

def ismonomial(pe, product=(pp.And, pp.Each)):
    # exmpale: a + b + c where a, b, c are atomic as in polynomials
    if pe.checkRecursion([]):
        return False
    if isatomic(pe):
        return True
    elif isinstance(pe, _Enhance):
        return ismonomial(pe.expr)
    elif isinstance(pe, product):
        return all(ismonomial(expr) for expr in pe.exprs)
    else:
        return False


def expand(pe, aslist = False):
    pe.streamline()
    if isinstance(pe, (pp.And, pp.Each)):
        if pe.exprs:
            x = expand(pe.exprs[0], True)
            for expr in pe.exprs[1:]:
                x = [xi + a for xi in x for a in expand(expr, True)]
    elif isinstance(pe, (pp.Or, pp.MatchFirst)):
        x = []
        for expr in pe.exprs:
            x.extend(expand(expr, True))
    elif isinstance(pe, _Enhance):
        x = expand(pe.expr, True)
    else: # x is monomal
        x = [pe]

    x = [xi.streamline() for xi in x]
    if aslist:
        return x
    else:
        if len(x)==1:
            return x[0]
        else:
            return pp.MatchFirst(x)


# def add(expr1, expr2=None):
#     return lookahead(expr1, expr2) + lookahead(expr2)

# def lookahead(expr, other=None):
#     if other is None:
#         if isatomic(expr):
#             return expr
#         elif isinstance(expr, pp.And):
#             if expr.exprs:
#                 xp = expr.exprs.pop(0)
#                 if isatomic(xp):
#                     expr = xp + lookahead(expr)
#                 else:
#                     expr = lookahead(xp, expr)
#             return expr
#         # elif isinstance(expr, pp.Each):
#         #     if expr.exprs:
#         #         xp = expr.exprs.pop(0)
#         #         if isatomic(xp):
#         #             expr = xp & lookahead(expr)
#         #         else:
#         #             expr = lookahead(xp, expr)
#         #     return expr
#         elif isinstance(expr, (pp.MatchFirst, pp.Or)):
#             expr.exprs = [lookahead(xp) for xp in expr.exprs]
#             return expr
#         elif isinstance(expr1, _Enhance):
#             expr.expr = lookahead(expr.expr)
#             return expr
#     else:
#         if isatomic(expr):
#             return expr + pp.FollowedBy(lookahead(other))
#         return lookahead(expr + pp.FollowedBy(lookahead(other)))


if __name__ == "__main__":

    w = Wordx(lambda x: x in {'a', 'b', 'c', 'd'})
    M = delimitedMatrix(w, ch1=' ', ch2=pp.Regex('\n+').leaveWhitespace())
    p = M.parseString('a b\nc d')
    print(p.asList())

    s = '''[1]hehe
    [2]hehe'''
    print(enumeratedItems().parseString(s))