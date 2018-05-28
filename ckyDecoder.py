# -*- coding: utf-8 -*-
"""
Created on Sat May 26 20:37:37 2018

@author: Chensho
"""

from __future__ import division
import sys
from collections import defaultdict
import re
import itertools
import PCFG

def strNext(a):
    return ' (' + str(a[0])  +',' + str(a[1]) + ',' + str(a[2]) + ')'
class CKYDecoder:
    def __init__(self, text,g):
        self.nonTerms = set()            #set of non terminals
        self.allProds = set()            #set of all productions
        self.P = defaultdict(float)      #probabilities of productions
        self.score = defaultdict(float)  #n^2|G| matrix to store DP results
        self.backPointers = {}           #to back track
        self.terminals = {}              #maps best non terminal to terminal ("word")
        self.text = text       	 #the list of words
        self.origText = list(text)  #list of words, not mutated, to replace "unk" later

        #if we know the list of words that occur multiple times, then replace single occurrences with "<unk>"
        #but keep track of words that we replace, so that final tree has original words
        multiWords = [word.strip() for word in g.terminalSymbols]

        for i,word in enumerate(self.text):
            if word not in multiWords:
                self.text[i] = "<unk>"

        self.n = len(self.text)



    def addUnary(self,begin, end):
        '''
        Adds unary productions A -> B. These need to be handled differently, since the algo splits B,C in A->BC
        '''
        for A in self.nonTerms:
            for B in self.nonTerms:
                if (A,B) in self.allProds:
                    prob = self.P[(A,B)] + self.score[(begin,end,B)]
        
                    if prob < self.score[(begin,end,A)]:
                        self.score[(begin, end, A)] = prob
                        self.backPointers[(begin, end, A)] = (B,)
        
    
    def backtrack(self, n):
        if (0,n,'S') not in self.backPointers:
            #print "NONE"
            return None

        node = self._backtrack((0,n,'S'))
        return node


    def _backtrack(self, next):

        low = next[0]
        high = next[1]
        label = next[2]
        print('start'+ strNext(next))
        # If this doesn't map to anything, then the search has ended, and it should map to a terminal
        # create a tree node and return the terminal
        if next not in self.backPointers:
            if next in self.terminals:
                print('in terminals with ' + label)
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
            print('singularNext' + strNext(next))
            singleChild = self._backtrack(next)
            p = Node(label,False,None [singleChild])
            singleChild.parent = p
            return p

        elif len(next) == 3:
            (split, left, right) = branches
            next1 = (low, split, left)
            next2 = (split, high, right)

            print('leftNext' + strNext(next1))
            print('rightNext' + strNext(next2))
            n1 = self._backtrack(next1)    #left side    
            n2 = self._backtrack(next2) #right side

            p = Node(label,False,None,[n1,n2])
            return p
        



    def GetTree(self):
        self.nonTerms = g.nonTerminalSymbols
        for r in g.rulesCount:
            prob = r.minusLogProb    
            a = str(r.eLHS).strip()
            b = str(r.eRHS).strip()
            self.allProds.add((a,b))
            self.P[(a,b)] = prob
        
        self.nonTerms = sorted(list(self.nonTerms))

        n = self.n

        for i in range(0,n):
            begin = i
            end = i + 1

            for A in self.nonTerms:
                word = self.text[begin]

                if (A,word) in self.allProds:
                    self.score[(begin,end,A)] = self.P[(A, word)]
                    self.terminals[(begin,end,A)] = word


            self.addUnary(begin,end)

        for span in range(2,n+1):
            for begin in range(0,n-span+1):
                end = begin + span
                for split in range(begin+1,end):

                    for A,X in self.allProds:
                        rhs = X.split()
                        if len(rhs) == 2:
                            B = rhs[0].strip()
                            C = rhs[1].strip()

                            prob = self.score[(begin,split,B)] + self.score[(split, end, C)] + self.P[(A, X)]

                            if prob < self.score[(begin, end,  A)]:
                                self.score[(begin, end, A)] = prob
                                self.backPointers[(begin, end, A)] = (split, B, C)


                self.addUnary(begin,end)

        print('Done')
        s = self.backtrack(len(self.text))
        if s is not None:
            return Node("TOP", True, None, [s])
        else:
            None
        



if __name__ == "__main__":
    
    for line in sys.stdin:
        s = CKYSolver(line.strip())
        s.compute()