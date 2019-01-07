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
    PrecededBy: as FollowedBy
    MeanWhile:
    LinenStart:
    
    Actions:
    BaseAction: Base Class of Actions
    BifixAction: action for bifix operators such as <x,y>
    ...


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

```python
import pyparsing_ext.pylang
pyparsing_ext.pylang.example

pyparsing_ext.pylang.example.smallpy.cmdline()  # in mode of command line
```
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
