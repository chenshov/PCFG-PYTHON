# -*- coding: utf-8 -*-
"""
Created on Sat May 26 20:37:37 2018

@author: Chensho
"""

from __future__ import division
import sys
from collections import defaultdict



def strNext(a):
    return ' (' + str(a[0])  +',' + str(a[1]) + ',' + str(a[2]) + ')'


class CKYDecoder:
    def set_text(self, text):
        self.text = text  # the list of words
        self.origText = list(text)  # list of words, not mutated, to replace "unk" later
        multiWords = [word.strip() for word in self.g.terminalSymbols]

        for i, word in enumerate(self.text):
            if word not in multiWords:
                self.text[i] = "<unk>"

        self.n = len(self.text)
        self.success = True


    def __init__(self,g):
        self.nonTerms = set()            #set of non terminals
        self.allProds = set()            #set of all productions
        self.P = defaultdict(float)      #probabilities of productions
        self.score = defaultdict(float)  #n^2|G| matrix to store DP results
        self.backPointers = {}           #to back track
        self.terminals = {}              #maps best non terminal to terminal ("word")

        self.g = g
        self.unaryRules = dict()
        self.leftKeyUnary = dict()
        for r in g.rulesCount:
            prob = r.minusLogProb
            a = str(r.eLHS).strip()
            b = str(r.eRHS).strip()
            self.allProds.add((a,b))
            self.P[(a,b)] = prob
            if len(r.eRHS.symbols) == 1 and not r.isLexical:  # unary rule
                if r.eRHS not in self.unaryRules and r.eRHS not in self.terminals:
                    self.unaryRules[r.eRHS.symbols[0]] = set()
                if r.eLHS not in self.leftKeyUnary:
                    self.leftKeyUnary[r.eLHS.symbols[0]] = set()
                setOfRHS = self.leftKeyUnary[r.eLHS.symbols[0]]
                setOfLHS = self.unaryRules[r.eRHS.symbols[0]]
                setOfLHS.add(r.eLHS.symbols[0])
                setOfRHS.add(r.eRHS.symbols[0])




    def addUnary(self,begin, end):
        possible = []
        '''
        Adds unary productions A -> B. These need to be handled differently, since the algo splits B,C in A->BC
        '''
        for A in self.nonTerms:
            for B in self.nonTerms:
                if (A,B) in self.allProds:
                    possible.append((A,B))
                    prob = self.P[(A,B)] * self.score[(begin,end,B)]
        
                    if prob > self.score[(begin,end,A)]:
                        self.score[(begin, end, A)] = prob
                        self.backPointers[(begin, end, A)] = (B,)

        #print ("ds")

    def addMinimizeUnary(self, begin, end, possibleNonTerminals, additionalSymbols):
        my_list = list(possibleNonTerminals)
        for nonTer in my_list:
            if nonTer in self.unaryRules and additionalSymbols[nonTer] == 0:
                setOfAllLHS = self.unaryRules[nonTer]
                for LHS in setOfAllLHS:
                    if (LHS, nonTer) in self.allProds:
                        if LHS not in additionalSymbols:
                            additionalSymbols[LHS] = 0
                            my_list.append(LHS)
                            prob = self.P[(LHS, nonTer)] * self.score[(begin, end, nonTer)]

                            if prob > self.score[(begin, end, LHS)]:
                                self.score[(begin, end, LHS)] = prob
                                self.backPointers[(begin, end, LHS)] = (nonTer,)
                additionalSymbols[nonTer] = 1


    def addUnaryTakeTwo(self, begin, end):
        for A in self.nonTerms:
            if A in self.leftKeyUnary:
                for B in self.leftKeyUnary[A]:
                    prob = self.P[(A, B)] * self.score[(begin, end, B)]

                    if prob > self.score[(begin, end, A)]:
                        self.score[(begin, end, A)] = prob
                        self.backPointers[(begin, end, A)] = (B,)

    
    def backtrack(self, n):
        if (0,n,'S') not in self.backPointers:
            return None

        node = self._backtrack((0,n,'S'))
        return node

    def stack_backtrack(self, n):
        if (0,n,'S') not in self.backPointers:
            #print "NONE"
            return None
        top = Node('TOP', True, None, [])
        stack = [((0,n,'S'), top)]

        while not stack == []:
            current, root = stack.pop()
            low = current[0]
            high = current[1]
            label = current[2]

            if current not in self.backPointers:
                if current in self.terminals:
                    # print('in terminals with ' + label)
                    word = self.origText[current[0]]
                    n2 = Node(word, False, root, [])
                    root.setChildren([n2])
                    continue
                root.setChildren([None])
                continue


            branches = self.backPointers[current]
            if len(branches) == 1:
                next = (low, high, branches[0])
                # print('singularNext' + strNext(next))
                ch = Node(branches[0], False, root, [])
                stack.append((next, ch))
                root.setChildren([ch])
                continue

            elif len(current) == 3:
                (split, left, right) = branches
                next1 = (low, split, left)
                next2 = (split, high, right)

                # print('leftNext' + strNext(next1))
                # print('rightNext' + strNext(next2))
                ch1 = Node(left, False, root, [])
                ch2 = Node(right, False, root, [])
                root.setChildren([ch1, ch2])
                stack.append((next2, ch2))
                stack.append((next1, ch1))
                continue

        if top.isLegal():
            return top
        else:
            None

    def _backtrack(self, next):

        low = next[0]
        high = next[1]
        label = next[2]
        # print('start'+ strNext(next))
        # If this doesn't map to anything, then the search has ended, and it should map to a terminal
        # create a tree node and return the terminal
        if next not in self.backPointers:
            if next in self.terminals:
                #print('in terminals with ' + label)
                word = self.origText[next[0]]
                n2 = Node(word, False, None, [])
                p = Node(label,False,None,[n2])
                n2.parent = p
                return p
            return None
        
        #branches is of the form (split_location, Left nonterm, Right nonterm)
        branches = self.backPointers[next]        
        #backtracking Unary productions A->B is different. Next maps to (B,)
        #so provide the same low and high for B and send it off to next prodction 
        if len(branches) == 1:
            next = (low, high, branches[0])
            #print('singularNext' + strNext(next))
            singleChild = self._backtrack(next)
            p = Node(label,False,None, [singleChild])
            singleChild.parent = p
            return p

        elif len(next) == 3:
            (split, left, right) = branches
            next1 = (low, split, left)
            next2 = (split, high, right)

            #print('leftNext' + strNext(next1))
            #print('rightNext' + strNext(next2))
            n1 = self._backtrack(next1)    #left side    
            n2 = self._backtrack(next2) #right side
            p = Node(label,False,None,[n1,n2])
            n1.parent = p
            n2.parent = p
            return p


    def GetTree(self):
        self.nonTerms = self.g.nonTerminalSymbols

        self.nonTerms = sorted(list(self.nonTerms))

        n = self.n

        for i in range(0,n):
            begin = i
            end = i + 1
            possible_nonTerminals = set()
            additional_symbols = dict()
            for A in self.nonTerms:
                word = self.text[begin]

                if (A,word) in self.allProds:
                    self.score[(begin,end,A)] = self.P[(A, word)]
                    self.terminals[(begin,end,A)] = word
                    #possible_nonTerminals.add(A)
                    #additional_symbols[A] = 0


            #self.addMinimizeUnary(begin,end, possible_nonTerminals, additional_symbols)
            self.addUnary(begin, end)
            #self.addUnaryTakeTwo(begin, end)

        for span in range(2,n+1):
            for begin in range(0,n-span+1):
                end = begin + span
                #possible_nonTerminals = set()
                #additional_symbols = dict()
                for split in range(begin+1,end):


                    for A,X in self.allProds:
                        #possible_nonTerminals.add(A)
                        #additional_symbols[A] = 0
                        rhs = X.split()
                        if len(rhs) == 2:
                            B = rhs[0].strip()
                            C = rhs[1].strip()

                            prob = self.score[(begin,split,B)] * self.score[(split, end, C)] * self.P[(A, X)]

                            if prob > self.score[(begin, end,  A)]:
                                self.score[(begin, end, A)] = prob
                                self.backPointers[(begin, end, A)] = (split, B, C)


                #self.addMinimizeUnary(begin,end, possible_nonTerminals, additional_symbols)
                self.addUnary(begin, end)

        print('Done')
        return self.backtrack(len(self.text))
        
#Node class
class Node():
    def __init__(self):
        self.children = []
        self.parent = None
        self.isRoot = False
        self.id = None

    def __str__(self):
        if len(self.children) == 0:
            return self.id

        s = "(" + self.id + " "
        for n in self.children:
            s += str(n)
        s += ")"
        if s.startswith('(TOP'):
            s = s.replace(")(",") (")
        return s

    def isLegal(self):
        return self is not None and self.children is not None and self.children is not [] and len(self.children) > 0

    def __init__(self, id, isRoot, parent, children):
        self.children = children
        self.parent = parent
        self.isRoot = isRoot
        self.id = id

    def addChild(self,childNode):
        self.children.append(childNode)

    def setChildren(self, children):
        self.children = children

    def getYield(self):
        l = []
        if len(self.children) == 0:
            l.append(self.id)
        for child in self.children:
            childList = child.getYield()
            l += childList
        return l

    def getNodes(self):
        lst = [self]
        for n in self.children:
            lst2 = n.getNodes()
            lst = lst + lst2
        return lst

    def isInternal(self):
        return not self.isRoot and len(self.children) > 0

    def isPreTerminal(self):
        if len(self.children) == 0:
            return false
        return len(self.children[0].children) == 0

    def binarize(self,order):
        if order > -1:
            if len(self.children) > 2:
                markovOrderId = ""
                for i in range(0,order):
                    markovOrderId += self.children[i].id + "/"
                if order > 0:
                    if "@" not in self.id:
                        newId = self.id + "@/"  + markovOrderId
                    else:
                         newId = self.id + markovOrderId
                else:
                    if "@" not in self.id:
                        newId = self.id + "@//"
                    else:
                        newId = self.id

                n2 = Node(newId,False,self, self.children[1:])
                for child in self.children[1:]:
                    child.parent = n2
                self.children = [self.children[0], n2]


            for child in self.children:
                child.binarize(order)

    def deBinarize(self):
        if len(self.children) == 2:
            while "@" in self.children[-1].id:
                rightChild = self.children[-1]
                rightChildId = rightChild.id

                if "@" in rightChildId:
                    self.children.pop(-1)
                    self.children = self.children + rightChild.children
                    for innerChild in rightChild.children:
                        innerChild.parent = self
        for child in self.children:
            if child is not None:
                child.deBinarize()


# Tree class
class Tree():
    def __init__(self, root):
        self.root = root

    def __str__(self):
        return str(self.root)

    def binarize(self, order):
        self.root.binarize(order)

    def deBinarize(self):
        self.root.deBinarize()


