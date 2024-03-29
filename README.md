Introduction
=============

Abstract
----------
Extension of [pyparsing](https://github.com/pyparsing/pyparsing). You can easily build your own languages. :v:

Keywords
----------
* PEG
* Regular Expressions
* Parser
* Formal Grammar
* Operating Semantics


## Awesome Feature:

    1. mixedExpression
    2. build languages (see example)

Requirements
-----------
pyparsing



## Download

`pip install pyparsing_ext`



## Structure

- core: basic token classes
- actions: classes for parsing actions
- expressions: complicated expressions
- utils: some useful tools

Content
=========

Classes::

    Tokens:
    
    Wordx: powerful Word
    CharsNot: powerful CharsNotIn
    PrecededBy: as FollowedBy  (moved to pyparsing)
    MeanWhile:
    LinenStart:
    
    Actions:
    BaseAction: Base Class of Actions
    BifixAction: action for bifix operators such as <x,y>
    ...

How to define an 'Action' class, that is a wrapper of `ParseResults`
```python
# inherit BaseAction directly
class VarOpAction(BaseAction):
    # for operators with variables
    pass

# inherit a subclass of BaseAction
class IndexOpAction(VarOpAction):
    # x[start:stop]
    names = ('slice', 'index')   # register the names of tokens
    def __init__(self, instring='', loc=0, tokens=[]):
        # add names or handle with tokens advancedly
        super(IndexOpAction, self).__init__(instring, loc, tokens)
        if 'slice' in self:
            slc = tokens.slice
            self.start = slc.start if 'start' in slc else None
            self.stop = slc.stop if 'stop' in slc else None
            self.step = slc.step if 'step' in slc else None
        else:
            self.index = tokens.index

    def eval(self, calculator):
        # define eval method, define the semantics of the token
        if 'slice' in self:
            return slice(self.start.eval(calculator), self.stop.eval(calculator), self.step.eval(calculator))
        else:
            return self.index.eval(calculator)
```


Functions::

```python
keyRange(s)
ordRange(s)
chrRange(s)
CJK # for matching Chinese Japanese Korean
enumeratedItems
delimitedMatrix # delimitedList with two seps
```

Example
=========

```python
w = Wordx(lambda x: x in {'a', 'b', 'c', 'd'}) # == Word('abcd')

M = delimitedMatrix(w, ch1=' ', ch2=pp.Regex('\n+').leaveWhitespace())
p = M.parseString('a b\n c d')
print(p.asList())

s = '''
[1]hello, world
[2]hello, kitty
'''
print(enumeratedItems().parseString(s))

cjk = ordRange(0x4E00, 0x9FD5)
cjk.parseString('我爱你, I love you') # => ['我爱你']

cjk = ordRanges((0x4E00, 0x9FD5, 0, 256))
cjk.parseString('我爱你 I love you') # => ['我爱你 I love you']

import pyparsing as pp
integer = pp.pyparsing_common.signed_integer
varname = pp.pyparsing_common.identifier

arithOplist = [('-', 1, pp.opAssoc.RIGHT),
    (pp.oneOf('* /'), 2, pp.opAssoc.LEFT),
    (pp.oneOf('+ -'), 2, pp.opAssoc.LEFT)]

def func(EXP):
    return pp.Group('<' + EXP + pp.Suppress(',') + EXP +'>')| pp.Group('||' + EXP + '||') | pp.Group('|' + EXP + '|') | pp.Group(IDEN + '(' + pp.delimitedList(EXP) + ')')
baseExpr = integer | varname
EXP = mixedExpression(baseExpr, func=func, opList=arithOplist)

a = EXP.parseString('5*g(|-3|)+<4,5> + f(6)')
print(a)
# [[[5, '*', ['g', '(', ['|', ['-', 3], '|'], ')']], '+', ['<', 4, 5, '>'], '+', ['f', '(', 6, ')']]]
```



## build your own languages

run `example1.py` for a simple example

output:
```C
Example 1:
|-1| -> ('|', '|')(-(1))
Example 2:
parse source code:
 
x=|-1|;  # absolute value
y=x*2+1;
if x == 1
{z=[3.3_]; # the floor value
}
print "z =", z;
 
result:
z = 3 
see the dictionary of variables:
{'x': Decimal('1'), 'y': Decimal('3'), 'z': 3}
```

In example2.py, we create a programming language, "Small Python".
run `example2.py` for a complicated example, to parse a text file `test.spy`

`example2.smallpy.cmdline()`  # in mode of command line





## Log

The following method in base class of actions may lead error! just delete it in the latest version

```python
    # def __getitem__(self, key):
    #     if isinstance(key, int):
    #         return self.tokens[key]
    #     else:
    #         return getattr(self.tokens, key)
```

