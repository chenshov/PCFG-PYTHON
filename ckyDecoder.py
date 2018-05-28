# -*- coding: utf-8 -*-
"""
Created on Sat May 26 20:37:37 2018

@author: Chensho
"""


class CKYDecoder():
     def __init__(self,sentence,grammar):
         self.success = False
         self.sentence = sentence
         self.g = grammar
         self.n = len(sentence)
         self.allRules = set()
         self.P = dict()      
         self.score = dict()
         self.terminals = {} 
         self.origText = list(self.sentence)  #list of words, not mutated, to replace "unk" later
         
         for rule in self.g.rulesCount.keys():
             lhs = str(rule.eLHS).strip()
             rhs = str(rule.eRHS).strip()
             self.allRules.add((lhs,rhs))
             self.P[(lhs,rhs)] = rule.minusLogProb

         for index in range(0,self.n):
            begin = index
            end = index + 1

            for A in self.g.nonTerminalSymbols:
                word = self.sentence[begin]
                if (A.strip(),word.strip()) in self.allRules:
                    self.score[(begin,end,A)] = self.P[(A, word)]                    
                    self.terminals[(begin,end,A)] = word
                    self.addUnary2(begin,end,A,word)
            
         
     def GetTree(self):
        for span in range(2,self.n+1):
            for begin in range(0,self.n-span+1):
                end = begin + span
                for split in range(begin+1,end):

                    print(begin)
                    print(end)
                    for A,X in self.allRules:
                        # X is a pair of prodcutions, A -> X where X = L R
                        rhs = X.split(' ')
                        print(rhs)
                        if len(rhs) == 2:
                            B = rhs[0].strip()
                            C = rhs[1].strip()

                            prob = self.score[(begin,split,B)] * self.score[(split, end, C)] * self.P[(A, X)]
                            
                            if prob < self.score[(begin, end,  A)]:
                                self.score[(begin, end, A)] = prob
                                self.backPointers[(begin, end, A)] = (split, B, C)


                self.addUnary(begin,end)

        #finished DP algo, now back track and find best tree
        t = self.backtrack(len(self.text))
        if t is not None:
            print(t)
        else:
            print("NONE")
            
     def addUnary2(self,begin, end, A, B):
        if (A,B) in self.allRules:
            prob = self.P[(A,B)] * self.score[(begin,end,B)]

        if prob < self.score[(begin,end,A)]:
            self.score[(begin, end, A)] = prob
            self.backPointers[(begin, end, A)] = (B,)
                        
     def addUnary(self,begin, end):
        for A in self.g.nonTerminalSymbols:
            for B in self.g.nonTerminalSymbols:
                if (A,B) in self.allRules:
                    prob = self.P[(A,B)] * self.score[(begin,end,B)]
        
                    if prob < self.score[(begin,end,A)]:
                        self.score[(begin, end, A)] = prob
                        self.backPointers[(begin, end, A)] = (B,)
        

     def backtrack(self, n):
        
        if (0,n,'TOP') not in self.backPointers:
            #print "NONE"
            return None

        t = self._backtrack((0,n,'TOP'))

        t.deBinarize()
        return t


     def _backtrack(self, next):

        low = next[0]
        high = next[1]
        label = next[2]

        # If this doesn't map to anything, then the search has ended, and it should map to a terminal
        # create a tree node and return the terminal
        if next not in self.backPointers:
            if next in self.g.terminalSymbols:
        
                word = self.origText[next[0]]
                t = Tree(label=label, subs = None, wrd=word, span=(low, high))
        
            return t
        
        #branches is of the form (split_location, Left nonterm, Right nonterm)
        branches = self.backPointers[next]

        #backtracking Unary productions A->B is different. Next maps to (B,)
        #so provide the same low and high for B and send it off to next prodction 
        if len(branches) == 1:
            next = (low, high, branches[0])

            t1 = self._backtrack(next)
            t = Tree(label=label, subs = [t1], wrd=None, span=t1.span)
            return t

        #spans for L,R in X->LR are such that L gets the entire left side, so low to split, and R gets split to high
        elif len(next) == 3:
            (split, left, right) = branches
            next1 = (low, split, left)
            next2 = (split, high, right)

            t1 = self._backtrack(next1)    #left side    
            t2 = self._backtrack(next2) #right side

            #this is the span of X, not L or R. Need it for the tree
            spanLow = t1.span[0]
            spanHigh = t2.span[1]
            t = Tree(label=label, subs = [t1,t2], wrd=None, span=(spanLow, spanHigh))
            return t