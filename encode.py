import sys
import chardet
import heapq
import operator
import math
from collections import Counter
import os

DEPTH = -1
MAX_DEPTH = 0
ENCODING = 'ascii'
ENCODE_MAP = {
    'ascii': '00000',
    'utf-8': '00001',
    'UTF-16': '00010',
    'UTF-8-SIG': '00011'
}


class Node:
    '''A Class representing a Node within the decode tree. Explained in
    greater detail in the report'''

    def __init__(self, frequency=0, char='-1', lNode=None, rNode=None,
                 depth=0, code=''):
        self.frequency = frequency
        self.lNode = lNode
        self.rNode = rNode
        self.char = char
        self.depth = depth
        self.code = code

    def __lt__(self, other):
        return operator.lt(self.frequency, other.frequency)


def main():
    '''The main function that handles the program execution'''

    if(len(sys.argv) < 2):
        printUsage()
        sys.exit()
    else:
        detect(sys.argv[1])
        file = openFile(sys.argv[1])
        text = file.read()

        frequencies = countFrequency(text)

        nodes, nodeList = createNodes(frequencies)

        tree, root = buildTree(nodes, nodeList)
        findDepths(root)

        leaves = removeInternalNodes(tree)
        sortLeaves(leaves)
        codes, decodes = generateCodes(leaves)

        levels, leavesAtLevel = findLevelsAndLeaves(tree)
        treeShape, characterList = buildDecodeTable(levels, leavesAtLevel)
        encodedText = encodeText(text, codes)

        writeToFile(treeShape, characterList, encodedText)


def createNodes(frequencies):
    '''Creates a Node for every distinct character in the list of
    characters

    args:
        frequencies: A dictionary of characters to their respective
        frequencies within the inputted document

    returns:
        nodes: A heapq priority queue containing every node
        nodeList: A simple list containing every node'''

    nodes = []
    nodeList = []

    for character in frequencies:
        node = Node(char=character[0], frequency=character[1])
        heapq.heappush(nodes, node)
        nodeList.append(node)

    return nodes, nodeList


def encodeText(text, codes):
    '''Iterates through a given text, building an encoded message based
    on a coding dictionary provided

    args:
        text: The string to encode
        codes: The character to code dictionary

    returns:
        message: The encoded string'''
    message = ''

    for character in text:
        message += codes[character]

    return message


def writeToFile(treeShape, characterList, encodedText):
    '''Writes the decode table and encoded text to a .hc file

    args:
        treeShape: A binary string representation of the tree
        characterList: An ordered list of characters relating to the
        leaves of the tree
        encodedText: The encoded text to write to the file'''

    encodingString = ""
    characterString = ""

    encodingString = ENCODE_MAP[ENCODING]

    for char in characterList:
        characterString += textToBits(char)

    prePad = encodingString + '000' + treeShape + characterString + encodedText
    paddingLength = (8 - (len(prePad) % 8)) % 8

    paddingString = bin(paddingLength)[2:].zfill(3)
    padding = '0' * paddingLength

    data = encodingString + paddingString + treeShape + \
        characterString + encodedText + padding

    byteList = [int(data[8 * i:8 * (i + 1)].ljust(8, '0'), 2)
                for i in range(math.ceil(len(data) / 8))]

    output = bytes(byteList)

    if(len(sys.argv) > 2):
        outputFilename = sys.argv[2]

        if outputFilename[-3:] == '.hc':
            file = openCarefully(outputFilename)
        else:
            print('[-] Incorrect output file extension. Please use .hc')
            sys.exit()
    else:
        file = openCarefully('encode.hc')

    file.write(output)


def openCarefully(filename):
    '''Opens a .hc file to write to, ensuring overwrites are handled

    args:
        filename: The .hc file to open

    returns:
        The opened file'''

    if os.path.exists(filename):
        overwrite = ''
        while overwrite != 'n' and overwrite != 'y':
            print()
            overwrite = input(
                "[*] " + filename + " already exists! Overwrite (y/n)? ")
            overwrite.lower()

        if overwrite == 'y':
            file = open(filename, 'wb+')
        else:
            print("[-] Program exiting.")
            sys.exit()

    else:
        file = open(filename, 'wb+')

    return file


def textToBits(text, errors='surrogatepass'):
    '''Converts a given string of text to a string of binary bits, based on
    a given encoding type

    args:
        text: The character to encode

    returns:
        The encoded character as a string of bits'''

    if(ENCODING == 'UTF-8-SIG'):
        bits = bin(int.from_bytes(text.encode('utf-8', errors), 'big'))[2:]
    else:
        bits = bin(int.from_bytes(text.encode(ENCODING, errors), 'big'))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))


def buildTree(nodes, nodeList):
    '''Uses a priority queue to construct the Huffman tree

    args:
        nodes: The heapq priority queue of Nodes
        nodeList: A list containing all the Nodes

    returns:
        nodeList: The updated nodeList, which now contains all
        the internal Nodes too
        heapq.heapop(nodes): The root node'''

    length = len(nodes) - 1

    for i in range(0, length):
        node1 = heapq.heappop(nodes)
        node2 = heapq.heappop(nodes)

        newFrequency = node1.frequency + node2.frequency
        newNode = Node(char='-1', frequency=newFrequency, lNode=node1,
                       rNode=node2)

        heapq.heappush(nodes, newNode)
        nodeList.append(newNode)

    return nodeList, heapq.heappop(nodes)


def findDepths(node):
    '''A recursive function that performs a depth first search of the
    decode tree, allocating each Node within the tree its correct depth.

    args:
        node: The current node the function is at within the tree

    returns:
        If the function is at a leaf within the tree, nothing. Otherwise
        it calls itself again on its two children nodes'''

    global DEPTH, MAX_DEPTH

    DEPTH += 1

    node.depth = DEPTH

    if (node.lNode is None) and (node.rNode is None):
        if DEPTH > MAX_DEPTH:
            MAX_DEPTH = DEPTH
        return

    findDepths(node.lNode)
    DEPTH -= 1
    findDepths(node.rNode)
    DEPTH -= 1


def sortLeaves(leaves):
    '''Sort the list of leaves first by their depth attribute, and then
    alphabetically by their character attribute, so canonical Huffman
    codes can be generated

    args:
        leaves: The list of leaves (i.e Node objects) to sort'''

    leaves.sort(key=operator.attrgetter('depth', 'char'))


def generateCodes(leaves):
    '''Generates the canonical codes for the leaves of the tree, based on
    their depth within their tree, and their alphabetical order

    args:
        leaves: A sorted list of leaves

    returns:
        codes: A character to code dictionary
        decodes: A code to character dictionary

    n.b - both dictionaries are returned as this function is used by both the
    encoder and decoder'''

    currentDepth = leaves[0].depth
    counter = -1
    codes = {}
    decodes = {}

    for node in leaves:
        if node.char != '-1':
            counter += 1
            if node.depth > currentDepth:
                counter = counter * 2**(node.depth - currentDepth)
                currentDepth = node.depth

            code = str(bin(counter))[2:]

            if len(code) < currentDepth:
                code = ("0" * (currentDepth - len(code))) + \
                    code
            node.code = code
            codes[node.char] = code
            decodes[code] = node.char

    return codes, decodes


def removeInternalNodes(tree):
    '''Removes the internal nodes from the list of Nodes in the tree. (This
    list must have been sorted before hand for this function to operate
    correctly)

    args:
        tree: A list of all the Nodes within the tree

    returns:
        A list of leaves within the tree'''

    return tree[:int(len(tree) / 2) + 1]


def findLevelsAndLeaves(leaves):
    '''Finds the number of leaves at each level, and generates a dictionary
    of levels to a list of leaves at that level

    args:
        leaves: a list of all the leaves (i.e Node objects) within the tree

    returns:
        levels: A dictionary linking each level to a list of leaves at that
        level
        leavesAtLevel: A list containing the number of leaves at each level'''

    global MAX_DEPTH

    levels = {}
    leavesAtLevel = [0 for i in range(0, MAX_DEPTH + 1)]

    for node in leaves:
        if node.depth in levels:
            level = levels[node.depth]
            level.append(node)

        else:
            level = [node]

        levels[node.depth] = level

        if node.char != '-1':
            leavesAtLevel[node.depth] += 1

    return levels, leavesAtLevel


def buildDecodeTable(levels, leavesAtLevel):
    '''Builds the decode table that is prepended to the encoded file,
    which is composed of the tree shape and a character list. This function
    is explained in more thorough detail in the report

    args:
        levels: A dictionary linking each level to a list of leaves at that
        level
        leavesAtLevel: A list containing the number of leaves at each level

    returns:
        treeShape: A binary string representation of the shape of the tree
        characterList: An ordered list of characters relating to the leaves
        of the tree'''

    global MAX_DEPTH

    treeShape = ""
    characterList = []

    for i in range(1, MAX_DEPTH + 1):
        numberOfNodes = len(levels[i])
        numberOfLeaves = leavesAtLevel[i]

        if not (numberOfNodes & (numberOfNodes - 1)) and (
                numberOfLeaves == numberOfNodes):
            binaryCode = str(bin(numberOfLeaves - 1))[2:] + '1'
        elif not (numberOfNodes & (numberOfNodes - 1)) and (
                numberOfLeaves == numberOfNodes - 1):
            binaryCode = str(bin(numberOfLeaves))[2:] + '0'
        else:
            binaryCode = str(bin(numberOfLeaves))[2:]

        length = math.ceil(math.log(numberOfNodes, 2))

        if len(binaryCode) < length:
            binaryCode = ("0" * (
                length - len(binaryCode))) + binaryCode

        treeShape += binaryCode

        for j in range(0, numberOfLeaves):
            level = levels[i]
            characterList.append(level[j].char)

    return treeShape, characterList


def detect(filename):
    '''Detect the encoding of the text file

    args:
        filename: The file whose encoding is to be checked

    returns:
        A dictionary of results, detailing the encoding type,
        the confidence the program has that it is that encoding type,
        and the language the program believes it's in:

        {'encoding': string, 'confidence': int, 'language': string}
    '''

    global ENCODING

    try:
        with open(sys.argv[1], 'rb') as detectEncoding:
            ENCODING = chardet.detect(detectEncoding.read())['encoding']
    except OSError:
        print("[-] " + filename + ": File Not Found")
        sys.exit()


def openFile(filename):
    '''Opens the specified file with the correct encoding codec detected
    by the chardet library

    args:
        filename: The .txt file to open

    returns:
        file: The opened text file'''

    global ENCODING

    try:
        if((ENCODING) == 'ascii'):
            file = open(filename, 'r', encoding="ascii")
        elif((ENCODING) == 'utf-8'):
            file = open(filename, 'r', encoding="UTF-8")
        elif((ENCODING) == 'UTF-16'):
            file = open(filename, 'r', encoding="UTF-16")
        elif((ENCODING) == 'UTF-8-SIG'):
            file = open(filename, 'r', encoding="UTF-8-SIG")
        else:
            print("[-] Unknown encoding type for " + filename)
            sys.exit()
    except OSError:
        print("[-] " + filename + ": File Not Found")
        sys.exit()

    return file


def countFrequency(text):
    '''Efficiently counts the frequency of every distinct character
    found within the text

    args:
        text: The string to count the character frequency of

    returns:
        A counter object/dictionary mapping every character to its
        frequency'''

    return Counter(text).most_common()


def printUsage():
    '''Prints the usage message if an incorrect number of arguments were
    passed'''

    print("""[*] Usage:
        python encode.py [input] (output)

        Args:
            [input]: Filename of .txt file to encode
            (output): Optional filename of .hc file to write encoded output to.
                      If no (output) is specified, "encode.hc" is used.

        Please include .txt and .hc file extensions.""")


if __name__ == '__main__':
    main()
