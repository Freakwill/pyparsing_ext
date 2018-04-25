Introduction
=============

Abstract
----------
extension of pyparsing.

Keywords
----------
Functional Programming, Type Testing

Feature:

    1. mixedExpression

Requirements
-----------
pyparsing

Content
=========

Classes::

    Tokens:
    
    Wordx: powerful Word
    CharsNot: powerful CharsNotIn
    LeadedBy: as FollowedBy
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