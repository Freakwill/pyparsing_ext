#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import operator

from pyparsing_ext import *
from pyparsing_ext.pylang import *


arithOpTable = [{'token':'^','assoc':'right'}, {'token':pp.oneOf('+ -'),'arity':1}, pp.oneOf('* /'), pp.oneOf('+ -'), {'token':pp.oneOf('== != < > <= >='), 'action': CompareAction}]
logicOpTable = [{'token':'~', 'arity':1, 'action':UnaryOperatorAction}, {'token':'&', 'action':BinaryOperatorAction}, {'token':'|', 'action':BinaryOperatorAction}]

arithDict = {'True':True, 'False':False, '+': {1:operator.pos, 2:operator.add}, '*': operator.mul, '-':{1:operator.neg, 2:operator.sub}, '/':operator.truediv, '^':operator.pow, '==':operator.eq, '!=':operator.ne, '<':operator.lt, '>':operator.gt, '<=':operator.le, '>=':operator.ge}


class LogicSyntaxParser(StandardParser):
    # Grammar of Logic Language
    def __init__(self, constants=[{'token':NUMBER, 'action':NumberAction}, {'token':pp.quotedString, 'action':StringAction}],
        variables=[{'token':IDEN, 'action':VariableAction}], quantifier=pp.Keyword('forall') | pp.Keyword('exist')):
        atomicProposition = expression + pp.oneOf('= < > <= >=') + expression
        operators = arithOpTable \
        + [{'token':quantifier('quantifier') + pp.delimitedList(variable)('variables'), 'arity':1, 'action':QuantifierAction}] \
        + logicOpTable
        super().__init__(constants, variables, functions=[], operators=operators)
        self.quantifier = quantifier


commonKeywords = {'if':pp.Keyword('if'), 'elif':pp.Keyword('elif'), 'else':pp.Keyword('else'), 'while':pp.Keyword('while'), 'break':pp.Keyword('break'), 'continue':pp.Keyword('continue'), 'return':pp.Keyword('return'), 'pass':pp.Keyword('pass'), 'def':pp.Keyword('def'), 'print':pp.Keyword('print')}


class ProgrammingParser(StandardParser):
    '''parser for programming Language
    '''

    def make(self, *args, **kwargs):
        super().make(*args, **kwargs)
        variable = self.variable
        expression = self.expression
        # parser for program
        END = SEMICOLON | pp.LineEnd()
        program = pp.Forward()
        expressionStatement = expression + END
        assignmentStatement = variable('variable') + pp.Suppress('=') + (self.nakeTupleExpr('args') | self.expression('arg')) + pp.Optional(':' + IDEN('type')) + END
        assignmentStatement.setParseAction(AssignmentAction)
        # define if while break pass statements
        # Keywords = {'if':'if', 'while':'while', 'break':'break', 'pass':'pass', 'def':'def'}
        breakStatement = self.keywords['break']('keyword') + END
        breakStatement.setParseAction(BreakAction)
        continueStatement = self.keywords['continue']('keyword') + END
        continueStatement.setParseAction(ContinueAction)
        passStatement = self.keywords['pass']('keyword') + END
        passStatement.setParseAction(PassAction)
        printStatement = self.keywords['print']('keyword') + pp.delimitedList(expression)('args') + END
        printStatement.setParseAction(PrintAction)
        returnStatement = self.keywords['return']('keyword') + (self.nakeTupleExpr | self.expression)('arg') + END
        returnStatement.setParseAction(ReturnAction)

        # atomicStatement = assignmentStatement | breakStatement | continueStatement | passStatement | printStatement | returnStatement
        # block = atomicStatement | LBRACE + self.program + RBRACE

        ifStatement = self.keywords['if']('keyword') + expression('condition') + LBRACE + program('program') + RBRACE
        ifStatement.setParseAction(IfAction)
        # if condition {program} pp.ZeroOrMore(elif condition {program}) else {program}
        # IfelseAction
        whileStatement = self.keywords['while']('keyword') + expression('condition') + LBRACE + program('program') + RBRACE
        whileStatement.setParseAction(WhileAction)

        PARAM = variable('name') + pp.Optional(pp.Suppress('=') + expression('default'))
        PARAM.setParseAction(ParameterAction)
        defStatement = self.keywords['def']('keyword') + (variable('function') + LPAREN + pp.delimitedList(PARAM)('parameters') + RPAREN
          | PUNC('left') + pp.delimitedList(PARAM)('parameters') + PUNC('right')
          | PARAM('parameter1') + PUNC('operator') + PARAM('parameter2')) + LBRACE + program('program') + RBRACE
        defStatement.setParseAction(DefAction)

        self.statements = [ifStatement, whileStatement, defStatement, returnStatement, passStatement, printStatement, assignmentStatement,
        breakStatement, continueStatement, expressionStatement, LBRACE + program + RBRACE]

        statement = pp.MatchFirst(self.statements)
        program <<= pp.OneOrMore(statement).setParseAction(ProgramSequenceAction)
        loadStatement = pp.Keyword('load')('keyword').suppress() + pp.restOfLine('path')
        self.program = pp.ZeroOrMore(loadStatement)('loading') + program
        self.comment = pp.pythonStyleComment
        self.program.ignore(self.comment)

    def setComment(self, commentStyle='Python'):
        if not hasattr(self, 'program'):
            self.make()
        if self.comment in self.program.ignoreExprs:
            self.program.ignoreExprs.remove(self.comment)
        if commentStyle in {'Python', 'python'}:
            self.comment = pp.pythonStyleComment
        elif commentStyle in {'c', 'C'}:
            self.comment = pp.cStyleComment
        elif commentStyle in {'c++', 'C++'}:
            self.comment = pp.cppStyleComment
        elif commentStyle in {'c\\c++','C\\C++','c\\C++','C\\c++'}:
            self.comment = pp.cppStyleComment | pp.cStyleComment
        else:
            matlabStyleComment = pp.Regex(r"%.*").setName("Matlab (Latex) style comment")
            self.comment = matlabStyleComment
        self.program.ignore(self.comment)

    def parse(self, s):
        if not hasattr(self, 'program'):
            self.make()
        try:
            return self.program.parseString(s, parseAll=True)[0]
        except pp.ParseException as pe:
            print(pp.ParseException.explain(pe))


class ProgrammingLanguage(Language):
    '''programming Language
    '''
    def __init__(self, name='Toy', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.info = {
            'version': '0.0',
            'paths': [],
            'suffix': '.toy'
        }

    # def make(self):
    #     grammar = ProgrammingParser()
    #     calculator = None
    #     return ProgrammingLanguage(name=name, grammar=grammar, calculator=calculator)

    def execute(self, s):
        ret = self.parse(s)
        if ret and 'loading' in ret:
            for path in ret.loading:
                self.executeFile(path.strip())
        ret.execute(self.calculator)

    def parseFile(self, filename):
        import pathlib
        filename = pathlib.Path(filename).with_suffix(self.info['suffix'])
        if filename.exists():
            return super(ProgrammingLanguage, self).parseFile(filename)
        else:
            for path in self.info['paths']:
                filename = pathlib.Path(path) / filename
                if filename.exists():
                    return super(ProgrammingLanguage, self).parseFile(filename)
            else:
                raise Exception('Could not find file %s' % filename)

    def executeFile(self, filename):
        ret = self.parseFile(filename)
        if ret:
            if 'loading' in ret:
                for path in ret.loading:
                    self.executeFile(path.strip())
            ret.execute(self.calculator)

    def __call__(self, s):
        self.execute(s)

    def cmdline(self):
        # command line for the programming language
        import time
        print('Welcome. I am %s v%s. It is %s now.'%(self.name, self.verion, time.ctime()))
        prompt = '>>> '
        newlinePrompt = '... '
        while True:
            s = input(prompt)
            if s == 'quit':
                self.calculator.reset()
                break
            if self.matches(s):
                try:
                    ret = self.eval(s)
                    print(ret)
                except Exception as ex:
                    print(ex)
            else:
                while not self.program.matches(s):
                    ss = input(newlinePrompt)
                    if ss == '':
                        raise Exception('command could not be executed!')
                    s += ss
                else:
                    try:
                        self.execute(s)
                    except Exception as ex:
                        print(ex)

    def view(self):
        for k, v in self.calculator.context.items():
            print("%s: %s"%(k, v))
