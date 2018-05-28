# -*- coding: utf-8 -*-
"""
Created on Fri May 25 16:48:18 2018

@author: Chensho
"""

import math
from ckyDecoder import CKYDecoder
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

#Tree class
class Tree():    
    def __init__(self,root):
        self.root = root
        
    def __str__(self):
        return str(self.root)
    
    def binarize(self, order):
        self.root.binarize(order)
        
    def deBinarize(self):
        self.root.deBinarize()
                  
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
            
    def __init__(self, id, isRoot, parent, children):
        self.children = children
        self.parent = parent
        self.isRoot = isRoot
        self.id = id
        
    def addChild(self,childNode):
        self.children.append(childNode)
        
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
            child.deBinarize()
     
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
        self.minusLogProb = math.inf

    def __hash__(self):
        s = str(self)
        return hash(str(self))
           
    def __str__(self):
        s1 = str(self.eLHS)
        s2 = str(self.eRHS)
        return s1 + "--> " + s2
               
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
        for t in treeBank.trees:
            rules = self.getRules(t)
            self.addAll(rules)
                
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
           
       if  not str(rule) in self.rulesCount:
           self.rulesCount[rule] = 0
       
       counter = self.rulesCount[rule]
       counter = counter + 1
       self.rulesCount[rule] = counter
    
    def CalcRulesProbs(self, debug = False):
        rulesMapCount = dict()
        denomMap = dict()        
        for nonTerm in self.nonTerminalSymbols:
            denom = 0
            for rule in self.rulesCount:
                if rule.eLHS.symbols[0] == nonTerm:
                    if rule in denomMap:
                        denom = denomMap[rule.eLHS.symbols[0]]
                    denom += self.rulesCount[rule]
                    denomMap[rule.eLHS.symbols[0]] = denom
        if debug: 
            for key in denomMap.keys():
                print(key)
                print(denomMap[key])
        for rule in self.rulesCount:
                nomi = self.rulesCount[rule]
                denomi = denomMap[rule.eLHS.symbols[0]]
                rule.minusLogProb = math.log(1.0 * (nomi / denomi))
                
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
        n.addChild(Node(token,False,n,[]))
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
    return grammar

def decode(sentence, grammar):   
    ckyDecoder = CKYDecoder(sentence, grammar)
    if ckyDecoder.success:
        return ckyDecoder.GetTree()
    
    return DummyParser(sentence).GetTree()

def output(TreeBank, outputFile):
     with open(outputFile,'rw') as f:
         treeBank.deBinarize()
         for t in TreeBank:
             f.write(str(t))
    
def PCFG(goldFile, trainFile, outputFile, markovOrder):
    gts,tts = parse(goldFile, trainFile, outputFile)
    grammar = train(tts)
    tts.binarize(markovOrder)
    outputTreeBank = TreeBank([])
    for t in tts:
        outputTreeBank.trees.append(decode(t.root.getYield(),grammar))
    
    output(outputTreeBank, outputFile)

            
    
    
    