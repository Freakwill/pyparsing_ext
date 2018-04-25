Introduction
=============

Abstract
----------
extension of pyparsing.

Keywords
----------
Text Process

Feature:

    1. mixedExpression


Content
=========

Classes::

    Wordx: powerful Word
    CharsNot: powerful CharsNotIn
    LeadedBy: as FollowedBy
    MeanWhile:
    LinenStart:

    BaseAction: Base Class of Actions

Functions::

    keyRange(s)
    ordRange(s)
    chrRange(s)
    CJK: for matching Chinese Japanese Korean
    enumeratedItems
    delimitedMatrix: delimitedList with two seps


Example
=========

    w = Wordx(lambda x: x in {'a', 'b', 'c', 'd'})
    M = delimitedMatrix(w, ch1=' ', ch2=pp.Regex('\n+').leaveWhitespace())
    p = M.parseString('a b\nc d')
    print(p.asList())

    s = '''[1]hehe
    [2]hehe'''
    print(enumeratedItems().parseString(s))