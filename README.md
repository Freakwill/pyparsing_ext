Introduction
=============

Abstract
----------
Extension of pyparsing. You can easily build your own languages. :v:

Keywords
----------
* PEG

* parser


## Awesome Feature:

    1. mixedExpression
    2. build languages (see example)

Requirements
-----------
pyparsing



## Download

`pip install pyparsing_ext`



## Structure

core: basic token classes

actions: classes for parsing actions

utils: some useful tools

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
w = Wordx(lambda x: x in {'a', 'b', 'c', 'd'})
M = delimitedMatrix(w, ch1=' ', ch2=pp.Regex('\n+').leaveWhitespace())
p = M.parseString('a b\n c d')
print(p.asList())

s = '''
[1]hello, world
[2]hello, kitty
'''
print(enumeratedItems().parseString(s))
```



## build your own languages

```python
import pyparsing_ext.pylang.example
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
