#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyparsing_ext.pylang import *

arithOpTable = [{'token':'^','assoc':'right'}, {'token':pp.oneOf('+ -'),'arity':1}, pp.oneOf('* /'), pp.oneOf('+ -'), {'token':pp.oneOf('== != < > <= >='), 'action': CompareAction}]
logicOpTable = [{'token':'~', 'arity':1, 'action':UnaryOperatorAction}, {'token':'&', 'action':BinaryOperatorAction}, {'token':'|', 'action':BinaryOperatorAction}]
arithDict = {'True':True, 'False':False, '+': {1:operator.pos, 2:operator.add}, '*': operator.mul, '-':{1:operator.neg, 2:operator.sub}, '/':operator.truediv, '^':operator.pow, '==':operator.eq, '!=':operator.ne, '<':operator.lt, '>':operator.gt, '<=':operator.le, '>=':operator.ge}


class LogicGrammarParser(GrammarParser):
    # Grammar of Logic Language
    def __init__(self, constants=[{'token':NUMBER, 'action':NumberAction}, {'token':pp.quotedString, 'action':StringAction}], variables=[{'token':IDEN, 'action':VariableAction}], quantifier=pp.Keyword('forall') | pp.Keyword('exist')):
        atomicProposition = expression + pp.oneOf('= < > <= >=') + expression
        operators = arithOpTable \
        + [{'token':quantifier('quantifier') + pp.delimitedList(variable)('variables'), 'arity':1, 'action':QuantifierAction}] \
        + logicOpTable
        grammar = GrammarParser(constants, variables, functions=[], operators=operators)
        super(LogicLanguage, self).__init__(grammar)
        self.quantifier = quantifier

commonKeywords = {'if':pp.Keyword('if'), 'elif':pp.Keyword('elif'), 'else':pp.Keyword('else'), 'while':pp.Keyword('while'), 'break':pp.Keyword('break'), 'continue':pp.Keyword('continue'), 'return':pp.Keyword('return'), 'pass':pp.Keyword('pass'), 'def':pp.Keyword('def'), 'print':pp.Keyword('print')}

class ProgrammingGrammarParser(GrammarParser):
    '''programming Language
    '''

    def make_parser(self):
        super(ProgrammingGrammarParser, self).make_parser()
        variable = self.variables[0]['token']
        expression = self.expression
        # parser for program
        self.program = pp.Forward()
        programWithControl = pp.Forward()
        expressionStatement = expression + SEMICOLON
        assignmentStatement = variable('variable') + pp.Suppress('=') + expression('expression') + SEMICOLON
        assignmentStatement.setParseAction(AssignmentAction)
        # define if while break pass statements
        # Keywords = {'if':'if', 'while':'while', 'break':'break', 'pass':'pass', 'def':'def'}
        breakStatement = self.keywords['break']('keyword') + SEMICOLON
        breakStatement.setParseAction(BreakAction)
        continueStatement = self.keywords['continue']('keyword') + SEMICOLON
        continueStatement.setParseAction(ContinueAction)
        passStatement = self.keywords['pass']('keyword') + SEMICOLON
        passStatement.setParseAction(PassAction)
        printStatement = self.keywords['print']('keyword') + pp.delimitedList(expression)('args') + SEMICOLON
        printStatement.setParseAction(PrintAction)
        returnStatement = self.keywords['return']('keyword') + expression('retval') + SEMICOLON
        returnStatement.setParseAction(ReturnAction)

        # atomicStatement = assignmentStatement | breakStatement | continueStatement | passStatement | printStatement | returnStatement
        # block = atomicStatement | LBRACE + self.program + RBRACE

        ifStatement = self.keywords['if']('keyword') + expression('condition') + LBRACE + self.program('program') + RBRACE
        ifStatement.setParseAction(IfAction)
        ifStatementWithControl = self.keywords['if']('keyword') + expression('condition') + LBRACE + programWithControl('program') + RBRACE
        ifStatementWithControl.setParseAction(IfAction)
        # if condition {program} pp.ZeroOrMore(elif condition {program}) else {program}
        # IfelseAction
        whileStatement = self.keywords['while']('keyword') + expression('condition') + LBRACE + programWithControl('program') + RBRACE
        whileStatement.setParseAction(WhileAction)       
        defStatement = self.keywords['def']('keyword') + (variable('function') + LPAREN + pp.delimitedList(variable)('args') + RPAREN | PUNC('left') + pp.delimitedList(variable)('args') + PUNC('right')) + LBRACE + self.program('program') + RBRACE
        defStatement.setParseAction(DefAction)
        self.statements = [ifStatement, whileStatement, defStatement, returnStatement, passStatement, printStatement, assignmentStatement, expressionStatement, LBRACE + self.program + RBRACE]
        statement = pp.MatchFirst(self.statements)
        controlStatements = [breakStatement, continueStatement, ifStatementWithControl, LBRACE + programWithControl + RBRACE]
        statementWithControl = pp.MatchFirst(self.statements + controlStatements)
        programWithControl <<= pp.OneOrMore(statementWithControl).setParseAction(ProgramSequenceAction)
        loadStatement = pp.Keyword('load')('keyword').suppress() + pp.restOfLine('path')
        self.program <<= pp.ZeroOrMore(loadStatement)('loading') + pp.OneOrMore(statement).setParseAction(ProgramSequenceAction)
        self.comment = pp.pythonStyleComment
        self.program.ignore(self.comment)

    def setComment(self, commentStyle='Python'):
        if not hasattr(self, 'program'):
            self.make_parser()
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
            self.make_parser()
        return self.program.parseString(s, parseAll=True)[0]


class ProgrammingLanguage(Language):
    '''programming Language
    '''
    def __init__(self, name='Toy', version='0.0', *args, **kwargs):
        super(ProgrammingLanguage, self).__init__(*args, **kwargs)
        self.version = version

    def make(self):
        grammar = ProgrammingGrammarParser()
        calculator = None
        return ProgrammingLanguage(name=name, grammar=grammar, calculator=calculator)

    def execute(self, s):
        ret = self.parse(s)
        if 'loading' in ret:
            for path in ret.loading:
                self.executeFile(path.strip())
        ret.execute(self.calculator)

    def executeFile(self, filename):
        ret = self.parseFile(filename)
        if 'loading' in ret:
            for path in ret.loading:
                self.executeFile(path.strip())
        ret = ret[-1]
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