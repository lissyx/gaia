# -*- coding: utf-8 -*-

from array import array
from optparse import OptionParser 
from xml.dom.minidom import parseString
from io import BytesIO
from StringIO import StringIO
from collections import defaultdict
import sys, struct, operator, heapq

_NodeCounter = 0
_NodeRemoveCounter = 0

# Data Structure for TST Tree
class TSTNode:
    # Constructor for creating a new TSTNode
    def __init__(self, ch):
        global _NodeCounter
        self.id = _NodeCounter
        _NodeCounter += 1
        self.ch = ch
        self.left = self.center = self.right = None
        self.frequency = 0 # frequency != 0 indicates the end of a word
        # we need to store the offset for writing the TST into a file
        self.leftOffset = self.centerOffset = self.rightOffset = 0
        # store the count for balancing the tst
        self.count = 0
        # store has for creating the DAG
        self.hash = 0
        # we set an offset of -1 as default, because the offset can never be -1
        self.offset = -1

class Ptr:
    def __init__(self, obj): self.obj = obj
    def get(self): return self.obj
    def set(self, obj): self.obj = obj

class TSTTree:
    # Constructor for creating a TST Tree
    def __init__(self):
        self.tableSize = 1048576
        self.table = [None] * self.tableSize

    # Insert a word into the TSTTree
    def insert(self, node, word, freq):
        ch = word[0]

        if not node:
            node = TSTNode(ch)
        if ch < node.ch:
            node.left = self.insert(node.left, word, freq)
        elif ch > node.ch:
            node.right = self.insert(node.right, word, freq)
        else:
            if len(word) == 1:
                # make sure do not enter duplicate entries
                assert (node.frequency == 0)
                node.frequency = freq
            else:
                node.center = self.insert(node.center, word[1:], freq)
        return node

    # Balance the TST
    # set the number of children nodes
    def setCount(self, node):
        if not node:
            return 0
        node.count = self.setCount(node.left) + self.setCount(node.right) + 1
        self.setCount(node.center)
        return node.count

    def rotateRight(self, node):
        tmp = node.left
        # move the subtree between tmp and node
        node.left = tmp.right
        # swap tmp and node
        tmp.right = node
        # restore count field
        node.count = (node.left.count if node.left else 0) + (node.right.count if node.right else 0) + 1
        tmp.count = (tmp.left.count if tmp.left else 0) + tmp.right.count + 1
        return tmp

    def rotateLeft(self, node):
        tmp = node.right
        # move the subtree between tmp and node
        node.right = tmp.left
        # swap tmp and node
        tmp.left = node
        # restore count field
        node.count = (node.left.count if node.left else 0) + (node.right.count if node.right else 0) + 1
        tmp.count = tmp.left.count + (tmp.right.count if tmp.right else 0) + 1
        return tmp

    def divide(self, node, divCount):
        leftCount = (node.left.count if node.left else 0)
        # if the dividing node is in the left subtree, got down to it
        if divCount < leftCount:
            node.left = self.divide(node.left, divCount)
            # on the way back from the dividing node to the root, do right rotations
            node = self.rotateRight(node)
        elif divCount > leftCount:
            node.right = self.divide(node.right, divCount - leftCount - 1)
            node = self.rotateLeft(node)
        return node

    # balance level of TST
    def balanceLevel(self, node):
        if not node or node.count == 1:
            return node
         
        # make center node the root
        node = self.divide(node, node.count / 2)
        # balance subtrbalanceLevelees recursively
        node.left = self.balanceLevel(node.left)
        node.right = self.balanceLevel(node.right)
        return node

    # balance the whole TST
    def balanceTree(self, node):
        if not node:
            return
        node.center = self.balanceLevel(node.center)
        self.balanceTree(node.center)
        self.balanceTree(node.left)
        self.balanceTree(node.right)

    def balance(self, root):
        self.setCount(root)
        root = self.balanceLevel(root)
        self.balanceTree(root)
        return root

    # Compress the TST
    def equal(self, nodeA, nodeB):
        if not nodeA or not nodeB:
            return nodeA == None and nodeB == None
        # two nodes are equal if their characters and their
        # children are equal
        return ((nodeA.ch == nodeB.ch) and 
                (nodeA.frequency == nodeB.frequency) and
                (self.equal(nodeA.left, nodeB.left)) and
                (self.equal(nodeA.center, nodeB.center)) and
                (self.equal(nodeA.right, nodeB.right)))

    def calculateHash(self, node):
        if not node:
            return 0
        assert (len(node.ch) == 1)
        node.hash = (ord(node.ch) - ord('a')) + 31 * self.calculateHash(node.center)
        node.hash ^= self.calculateHash(node.left)
        node.hash ^= self.calculateHash(node.right)
        node.hash ^= (node.hash >> 16)
        # hash must be unsigned for correct modulo calculation
        node.hash %= self.tableSize
        return node.hash

    def freeNode(self, node):
        global _NodeRemoveCounter
        if not node:
            return
        self.freeNode(node.left)
        self.freeNode(node.center)
        self.freeNode(node.right)
        _NodeRemoveCounter += 1
        node = None

    # find the node in the hash table. if it does not exist,
    # add a new one and return true, if not, return false
    def checkAndRemoveDuplicate(self, nodePtr):
        global _NodeRemoveCounter

        node = nodePtr.get()
        hash = node.hash
        while (self.table[hash] != None):
            if self.equal(self.table[hash], node):
                # this node already exists in the table.
                # remove the duplicate
                self.freeNode(node)
                nodePtr.set(self.table[hash])
                return False
            hash = (hash + 1) % self.tableSize
        self.table[hash] = node
        return True

    # remove duplicates suffixes starting from the longest one
    def removeDuplicates(self, node):
        if node.left:
            # if the node already exists in the table
            # (checkAndRemoveDuplicate returns false),
            # its children were checked for duplicates already
            # avoid duplicate checking
            lPtr = Ptr(node.left)
            lHelp = self.checkAndRemoveDuplicate(lPtr)
            node.left = lPtr.get()
            if lHelp:
                self.removeDuplicates(node.left)
        if node.right:
            rPtr = Ptr(node.right)
            rHelp = self.checkAndRemoveDuplicate(rPtr)
            node.right = rPtr.get()
            if rHelp:
                self.removeDuplicates(node.right)
        if node.center:
            cPtr = Ptr(node.center)
            cHelp = self.checkAndRemoveDuplicate(cPtr)
            node.center = cPtr.get()
            if cHelp:
                self.removeDuplicates(node.center)
        return node

    # # traverse the tree using DFS to find all possible candidates
    # # starting with the given prefix
    # def findPredictions(self, node, match, suggestions):

    #     if node.frequency != 0:
    #         suggestions.append([match, node.frequency])

    #     if not node.center and not node.left and not node.right:
    #         return

    #     if node.center:
    #         self.findPredictions(node.center, match + node.center.ch, suggestions)

    #     if node.right:
    #         self.findPredictions(node.right, match[:-1] + node.right.ch, suggestions)

    #     if node.left:
    #         self.findPredictions(node.left, match[:-1] + node.left.ch, suggestions)

    # def predict(self, node, prefix, match, suggestions):
    #     if len(prefix) <= 0:
    #         return

    #     ch = prefix[0]

    #     if ch < node.ch:
    #         if not node.left:
    #             return
    #         self.predict(node.left, prefix, match, suggestions)
    #     elif ch > node.ch:
    #         if not node.right:
    #             return
    #         self.predict(node.right, prefix, match, suggestions)
    #     else:
    #         if (len(prefix) == 1):
    #             if node.frequency != 0:
    #                 suggestions.append([match, node.frequency])
    #             if node.center:
    #                 self.findPredictions(node.center, match+node.ch+node.center.ch, suggestions)
    #             return
    #         self.predict(node.center, prefix[1:], match+ch, suggestions)

def buildTST(tree):
    root = None
    count = 0
    for word, freq in TSTIndex.iteritems():
        root = tree.insert(root, word, freq)
    return root

def writeInt32(output, int32):
    output.write(struct.pack("i", int32))

def writeChar(output, ch):
    writeInt32(output, ord(ch))

# offset is a byteoffset, so we have to calculate
# the correct index for an Int32Array
def emitOffset(output, offset):
    writeInt32(output, offset/4)

def emitNode(output, verboseOutput, node):
    fixup = 0
    writeChar(output, node.ch)
    offset = output.tell()
    # set the default
    # node.offset = gettAttr(node, "offset", -1)
    if node.offset != offset:
        node.offset = offset
        fixup += 1
    verboseOutput.write("["+ str((node.offset-1)/4) +"] { ch: " + node.ch)

    # emit the left child
    if node.left:
        if node.leftOffset != node.left.offset:
            fixup += 1
            node.leftOffset = node.left.offset
    emitOffset(output, (node.leftOffset - node.offset) if node.left else 0)
    verboseOutput.write(", l: " + str(max(node.leftOffset-1,0)/4))
    
    # emit the center child
    if node.center:
        if node.centerOffset != node.center.offset:
            fixup += 1
            node.centerOffset = node.center.offset
    emitOffset(output, (node.centerOffset - node.offset) if node.center else 0)
    verboseOutput.write(", c: " + str(max(node.centerOffset-1,0)/4))
 
    # emit the right child
    if node.right:
        if node.rightOffset != node.right.offset:
            fixup += 1
            node.rightOffset = node.right.offset
    emitOffset(output, (node.rightOffset - node.offset) if node.right else 0)
    verboseOutput.write(", r: " + str(max(node.rightOffset-1,0)/4))

    # emit the frequency of the node
    writeInt32(output, node.frequency)
    verboseOutput.write(", f: " + str(node.frequency) + "}\n")
    return fixup

# emit the tree BFS
def emitTST(output, verboseOutput, root):
    fixup = 0
    queue = []
    visited = []
    queue.append(root)

    while queue:
        node = queue.pop(0)
        if node.id in visited:
            continue;
        visited.append(node.id)

        #print ("visiting: " + str(node.id) + " : " + str(node.offset))

        fixup += emitNode(output, verboseOutput, node)
        
        if node.left:
            queue.append(node.left)
        if node.center:
            queue.append(node.center)
        if node.right:
            queue.append(node.right)

    return fixup

# Parse command line arguments.
#
# Syntax: python xml2dict.py [-v] -o output-file input-file
#
use = "Usage: %prog [options] dictionary.xml"
parser = OptionParser(usage = use)
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="Set mode to verbose.")
parser.add_option("-o", "--output", dest="output", metavar="FILE", help="write output to FILE")
options, args = parser.parse_args()

# We expect the dictionary name to be present on the command line.
if len(args) < 1:
    print("Missing dictionary name.")
    exit(-1)
if options.output == None:
    print("Missing output file.")
    exit(-1)

# Read the input dictionary file into memory. We use dictionary files in XML
# format as defined by Android 4.1 (Jellybean).
file = open(args[0])
data = file.read()
file.close()

# print some status statements to the console
print ("[0/6] Creating dictionary ... (this might take a long time)" )
print ("[1/6] Reading XML wordlist ..." )

# TST insertion
TSTIndex = {}

# Parse the XML input file and build the trie.
dom = parseString(data)
wordlist = dom.getElementsByTagName("wordlist")[0]
words = wordlist.getElementsByTagName("w")

for word in words:
    attr = word.attributes
    flags = attr.get("flags")
    if flags != None:
        flags = flags.nodeValue
    else:
        flags = ""
    freq = int(attr.get("f").nodeValue)
    if flags == "abbreviation" or freq <= 1:
        continue
    text = word.childNodes[0].nodeValue
    if len(text) <= 1:
        continue;
    TSTIndex[text] = freq

print ("[2/6] Creating Ternary Search Tree for " + str(len(TSTIndex)) + " words ...")

tree = TSTTree()
tstRoot = buildTST(tree)

print ("[3/6] Balancing Ternary Search Tree ...")
tstRoot = tree.balance(tstRoot)

print ("[4/6] Compressing TST to DAG ...")
tree.calculateHash(tstRoot)
tstRoot = tree.removeDuplicates(tstRoot)

print ("[5/6] Emitting TST (" +
       str(_NodeCounter) + " - " + str(_NodeRemoveCounter) + " = " +
       str(_NodeCounter - _NodeRemoveCounter) + " nodes).")

while True:
    output = BytesIO()
    verboseOutput = StringIO()
    fixup = emitTST(output, verboseOutput, tstRoot)
    print("[5/6] Emitting TST (forwarding pointer fixups remaining: " + str(fixup))
    if fixup == 0:
        break

# Actually write the output data to disk.
output.seek(0)
f = open(options.output, "w")
f.write(output.read())
f.close()

if options.verbose:
    verboseOutput.seek(0)
    f = open(options.output + ".tst", "w")
    f.write(verboseOutput.read().encode("utf-8"))
    f.close()

print ("[6/6] Successfully created Dictionary")
