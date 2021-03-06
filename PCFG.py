# -*- coding: utf-8 -*-
"""
Created on Fri May 25 16:48:18 2018

@author: Chensho
"""

from ckyDecoder import *
import math
import sys

# Treebank class


class TreeBank():
    def __init__(self, trees):
        self.trees = trees
        
    def __str__(self):
        s = ""
        for t in self.trees:
            s += str(t)
        return s
    
    def binarize(self, order):
        for t in self.trees:
            t.binarize(order)
        
    def deBinarize(self):
        for t in self.trees:
            t.deBinarize()


#class event        
class Event():
    def __init__(self,symbols):
        self.symbols = symbols   
        
    def __str__(self):
        s = ""
        for symbols in self.symbols:
            s += symbols + " "
        return s
#class rule
class Rule():
       
    def __init__(self, eLHS, eRHS):           
        self.eLHS = eLHS    
        self.eRHS = eRHS
        self.isLexical = False        
        self.isTop = False
        self.minusLogProb = float('inf')

    def __hash__(self):
        s = str(self)
        return hash(str(self))
           
    def __str__(self):
        s1 = str(self.eLHS)
        s2 = str(self.eRHS)
        return s1 + "--> " + s2

    def __eq__(self, other):
        return str(self) == str(other)
               
# class grammar
class Grammar():
    def __init__(self,treeBank):
        self.treeBank = treeBank
        self.lexicalRules = set()
        self.syntacticRules = set()
        self.nonTerminalSymbols = set()
        self.terminalSymbols = set()
        self.lexicalEntries = dict()
        self.startSymbols = set()
        self.rulesCount = dict()
        i = 1
        for t in treeBank.trees:
            rules = self.getRules(t)
            self.addAll(rules)
            i += 1
                
    def getRules(self, tree):
        rules = []
        nodes = tree.root.getNodes()
        for n in nodes:            
            if n.isInternal():                
                eLHS = Event([n.id])                
                innerChildren = n.children
                rhsIds = []
                for n2 in innerChildren:
                    rhsIds.append(n2.id)
                
                eRHS = Event(rhsIds)                 
                rule = Rule(eLHS, eRHS)
                if n.isPreTerminal():
                    rule.isLexical = True
                if n.parent is not None and n.parent.id == 'TOP': #root rule
                    rule.isTopRule = True
                rules.append(rule)
         
        return rules
    
    def addAll(self,rules):
        for rule in rules:
            self.addRule(rule)
            
    def addRule(self,rule):
       eLHS = rule.eLHS
       eRHS = rule.eRHS
       
       if rule.isLexical:
           self.lexicalRules.add(rule)
           for symbol in eLHS.symbols:
               self.nonTerminalSymbols.add(symbol)
               
           for symbol in eRHS.symbols:
               self.terminalSymbols.add(symbol)
                          
           key = " ".join(eRHS.symbols)
           if key not in self.lexicalEntries.keys():
               self.lexicalEntries[key] = set()
           self.lexicalEntries[key].add(rule)
           
       else:
           self.syntacticRules.add(rule)
           for symbol in eLHS.symbols:
               self.nonTerminalSymbols.add(symbol)
               
           for symbol in eRHS.symbols:
               self.nonTerminalSymbols.add(symbol)
               
       if rule.isTop:
           self.startSymbols.add(eLHS)

       if rule not  in self.rulesCount:
           self.rulesCount[rule] = 0
       
       counter = self.rulesCount[rule]
       counter = counter + 1
       self.rulesCount[rule] = counter


    def calc_denominators(self):
        denomMap = dict()
        for nonTerm in self.nonTerminalSymbols:
            denom = 0
            for rule in self.rulesCount:
                if rule.eLHS.symbols[0] == nonTerm:
                    if rule in denomMap:
                        denom = denomMap[rule.eLHS.symbols[0]]
                    denom += self.rulesCount[rule]
                    denomMap[rule.eLHS.symbols[0]] = denom
        return denomMap


    def CalcRulesProbs(self, debug = False):
        denomMap = self.calc_denominators()
        if debug: 
            for key in denomMap.keys():
                print(key)
                print(denomMap[key])
        for rule in self.rulesCount:
                nomi = 1.0 * self.rulesCount[rule]
                denomi = 1.0 * denomMap[rule.eLHS.symbols[0]]
                rule.minusLogProb = -math.log(nomi / denomi)

    def calc_nr_values(self):
        nrCounts = dict()
        for rule, count in self.rulesCount.items():
            if count in nrCounts:
                nrCounts[count] = nrCounts[count] + count
            else:
                nrCounts[count] = count
        return nrCounts


    def allCount(self, rulesCount):
        allCountSum = 0
        for rule, value in rulesCount.items():
            allCountSum += value
        return allCountSum


    def getNRValueOrDefault(self, nr_values, nrCount, default = 1.0):
        if nrCount in nr_values:
            return 1.0 * nr_values[nrCount]
        else:
            return default


    def CalcRulesProbsWithSmoothing(self):
        denomMap = self.calc_denominators()
        # calc Nr map (the number of n-grams that occur exactly r times)
        nr_values = self.calc_nr_values()
        # calc N values
        sum = self.allCount(self.rulesCount)
        # calc r* / N:
        for rule, rCount in self.rulesCount.items():
            rStar = (rCount + 1) * self.getNRValueOrDefault(nr_values, rCount + 1) / self.getNRValueOrDefault(nr_values, rCount)
            logProb = (1.0 * rStar / sum)#-math.log(1.0 * rStar / sum)
            rule.minusLogProb = logProb

                
#dummyParser class
class DummyParser():
    def __init__(self,sentence):      
        self.sentence = sentence
    
    def GetTree(self):       
        root = Node("TOP",True,None,[])
        for word in self.sentence:
            n2 = Node(word,False,None,[])
            n = Node("NN",False,root,[n2])
            n2.parent = n
            root.addChild(n)
        return Tree(root)
            
            
        

#print Trees for debug
def printTreeDebug(root, level):
    print(root.id,level)
    for n in root.children:
        printTreeDebug(n, level + 1)
        
#parse pme tree according to reut
def parseTree(treeLine, debug = False):
    s = []
    root = Node("TOP",True,None,[])
    s.insert(0,root)
    treeLine = treeLine[4:] # cutting the (TOP
    tokensList = treeLine.split(" ")    
    tokensList = list(filter(lambda x : x != '',tokensList))
    tokensList = list(map(lambda x : x.replace("\n",""),tokensList))
    for token in tokensList :
        if(token.startswith("(")):
            n = s.pop(0)
            n2 = Node(token[1:],False,n,[])
            n.addChild(n2)
            s.insert(0,n)
            s.insert(0,n2)
            if debug:
                print('(')
                print(n.id)
                print(n2.id)
            continue
        if(token.endswith(")")):
            t,t2 = token[:token.index(")")] ,token[token.index(')'):]
            n2 = Node(t,False,n,[])
            n = s.pop(0)
            n.addChild(n2)
            for c in t2[1:]:
                s.pop(0)
            if debug:
                print(')')
                print(n.id)
                print(n2.id)            
            continue
        n = s.pop(0)
        n.addChild(Node(token,False,n,[]), span=(-1, -1))
        s.insert(0,n) 
        if debug:
            print('space')
            print(n.id)
            print(n2.id)
    return Tree(root)
            
#parse Trees according to reut
def parseTrees(treeFile):
    trees = []
    with open(treeFile) as f:
        lines = f.readlines()
    for line in lines:
        t = parseTree(line)
        trees.append(t)
    return TreeBank(trees)

def parse(goldFile, trainFile, outputFile, debug = False):
    goldTrees = parseTrees(goldFile)
    trainTrees = parseTrees(trainFile)
    if debug :
        print('gold trees len is -',len(goldTrees))
        print('train trees len is -',len(trainTrees))
    return goldTrees, trainTrees
    
            
def train(binaryTreeBank):
    grammar = Grammar(binaryTreeBank)
    grammar.CalcRulesProbs()
    # grammar.CalcRulesProbsWithSmoothing()
    return grammar

def decode(sentence, grammar):   
    ckyDecoder = CKYDecoder(sentence, grammar)
    if ckyDecoder.success:
        return ckyDecoder.GetTree(grammar)
    
    return DummyParser(sentence).GetTree()

def output(treeBank, outputFile):
     with open(outputFile,'w') as f:
         treeBank.deBinarize()
         for t in TreeBank:
             f.write(str(t))
    
def PCFG(goldFile, trainFile, outputFile, markovOrder):
    gts,tts = parse(goldFile, trainFile, outputFile)
    print ("done parse")
    tts.binarize(markovOrder)
    print ("start train")
    grammar = train(tts)
    print ("done binarization")
    outputTreeBank = TreeBank([])
    for t in tts.trees:
        outputTreeBank.trees.append(decode(t.root.getYield(),grammar))
    output(outputTreeBank, outputFile)


if __name__ == "__main__":
    PCFG(sys.argv[1], sys.argv[2], "output.txt", 0)