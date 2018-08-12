import sys
import math
from encode import Node, sortLeaves, generateCodes
import os

ENCODING = 'ascii'
ENCODE_MAP = {
    '00000': 'ascii',
    '00001': 'utf-8',
    '00010': 'UTF-16',
    '00011': 'UTF-8-SIG'
}


def main():
    '''The main function that handles the program execution'''

    if(len(sys.argv) < 2):
        printUsage()
        sys.exit()
    else:
        file = openFile(sys.argv[1])
        binary = convertToBinary(file.read())

        binary, padding = detectEncodingAndPadding(binary)
        binary, leaves, root = buildTree(binary)

        encodedText = allocateChars(binary, leaves)

        sortLeaves(leaves)
        codes, decodes = generateCodes(leaves)

        output = decodeText(encodedText, decodes, padding)

        writeFile(output)


def writeFile(output):
    '''Handles writing the decoded output to a text file

    args:
        output: The output string to write to a file'''

    if(len(sys.argv) > 2):
        outputFilename = sys.argv[2]

        if outputFilename[-4:] == '.txt':
            file = openCarefully(outputFilename)
        else:
            print('[-] Incorrect output file extension. Please use .txt')
            sys.exit()
    else:
        file = openCarefully('decode.txt')

    file.write(output)


def openCarefully(filename):
    '''Opens a text file to write to, ensuring overwrites are handled

    args:
        filename: The .txt file to open

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
            file = open(filename, 'w+', encoding=ENCODING)
        else:
            print("[-] Program exiting.")
            sys.exit()

    else:
        file = open(filename, 'w+', encoding=ENCODING)

    return file


def decodeText(encodedText, decodes, padding):
    '''Iterates through the binary string, decoding the Huffman codes

    args:
        encodedText: The string of 1s and 0s to decode
        decodes: A code to character dictionary
        padding: The amount of padding added to the encodedText string

    returns:
        The decoded text, as a string'''

    decodedText = ''
    i, j = 0, 0

    while i < len(encodedText) - padding:

        while encodedText[i:i + j] not in decodes:
            j += 1

        decodedText += decodes[encodedText[i:i + j]]

        i += j
        j = 0

    return decodedText


def detectEncodingAndPadding(binary):
    '''Reads the first byte of the binary string, detecting the encoding
    and amount of padding added by the encoder

    args:
        binary: The entire binary string representation of the encoded file

    returns:
        binary[8:0]: The binary string with the first byte removed
        padding: The amount of padding added by the encoder'''

    global ENCODING, ENCODE_MAP

    ENCODING = ENCODE_MAP[binary[0:5]]
    padding = int(binary[5:8], 2)

    return binary[8:], padding


def buildTree(binary):
    '''Builds the Huffman tree from the decode table appended to the encoded
    file

    args:
        binary: The binary string representation of the [Tree Shape] [Charact-
        er String] [Encoded Text] [Padding]

    returns:
        binary: The binary string with the [Tree Shape] removed
        leaves: An ordered list of the leaves of the tree
        rootNode: The root Node of the tree'''

    leaves = []
    depth = 1

    lNode = Node()
    rNode = Node()

    lNode.depth = depth
    rNode.depth = depth

    rootNode = Node(lNode=lNode, rNode=rNode)

    nodesAtLevel = [lNode, rNode]
    numNodesAtLevel = len(nodesAtLevel)

    while numNodesAtLevel > 0:
        nodesAtNextLevel = []

        numBitsToRead = int(math.ceil(math.log(numNodesAtLevel, 2)))

        bits = binary[0: numBitsToRead]

        if bits == len(bits) * '1':

            if binary[numBitsToRead] == '1':
                numLeavesAtLevel = numNodesAtLevel
            else:
                numLeavesAtLevel = numNodesAtLevel - 1

            binary = binary[numBitsToRead + 1:]
        else:
            numLeavesAtLevel = int(bits, 2)
            binary = binary[numBitsToRead:]

        leaves.extend(nodesAtLevel[0:numLeavesAtLevel])

        depth += 1

        for internalNode in nodesAtLevel[numLeavesAtLevel:]:
            lNode = Node()
            rNode = Node()

            internalNode.lNode = lNode
            internalNode.rNode = rNode

            lNode.depth = depth
            rNode.depth = depth

            nodesAtNextLevel.append(lNode)
            nodesAtNextLevel.append(rNode)

        nodesAtLevel = nodesAtNextLevel
        numNodesAtLevel = len(nodesAtLevel)

    return binary, leaves, rootNode


def allocateChars(binary, leaves):
    '''Allocates the characters in the character list to the leaves of the
    tree

    args:
        binary: The binary string representation of [Character String]
        [Encoded Text] [Padding]
        leaves: An ordered list of the leaves of the tree

    returns:
        binary[8 * pos:]: The binary string with the [Character String]
        removed'''

    numLeaves = len(leaves)

    pos = 0
    for i in range(0, numLeaves):

        if ENCODING == 'utf-8' or ENCODING == 'UTF-8-SIG':
            bits = binary[pos * 8: (pos * 8) + 4]
            if bits == '1111':
                leaves[i].char = bitsToText(binary[pos * 8: (pos + 4) * 8])
                pos += 4
            elif bits[0:3] == '111':
                leaves[i].char = bitsToText(binary[pos * 8: (pos + 3) * 8])
                pos += 3
            elif bits[0:2] == '11':
                leaves[i].char = bitsToText(binary[pos * 8: (pos + 2) * 8])
                pos += 2
            else:
                leaves[i].char = bitsToText(binary[pos * 8: (pos + 1) * 8])
                pos += 1
        elif ENCODING == 'UTF-16':
            leaves[i].char = bitsToText(binary[pos * 8: (pos + 4) * 8])
            pos += 4
        else:
            leaves[i].char = bitsToText(binary[pos * 8: (pos + 1) * 8])
            pos += 1

    return binary[8 * pos:]


def bitsToText(bits, errors='surrogatepass'):
    '''Converts a string of binary bits into characters, based on the given
    encoding type

    args:
        bits: The string of bits to decode

    returns:
        The decoded character'''

    global ENCODING
    n = int(bits, 2)

    if(ENCODING == 'UTF-8-SIG'):
        return n.to_bytes((
            n.bit_length() + 7) // 8, 'big').decode('utf-8', errors) or '\0'
    else:
        return n.to_bytes((
            n.bit_length() + 7) // 8, 'big').decode(ENCODING, errors) or '\0'


def convertToBinary(data):
    '''Converts the file, read as a stream of byte objects, into a single
    string of binary bits

    returns:
        A binary string representation of the entire encoded file'''

    binaryList = [bin(data[i])[2:].zfill(8)
                  for i in range(math.ceil(len(data)))]
    return ''.join(binaryList)


def openFile(filename):
    '''Opens the encoded file in binary mode, ensuring the correct file extension
    has been given

    args:
        filename: The .hc file to decode

    returns:
        file: The opened file'''

    try:
        if(filename[-2:].lower() == 'hc'):
            file = open(filename, 'rb')
        else:
            print("[-] Unknown format type for " + filename)
            sys.exit()
    except OSError:
        print("[-] " + filename + ": File Not Found")
        sys.exit()

    return file


def printUsage():
    '''Prints the usage message if an incorrect number of arguments were
    passed'''

    print("""[*] Usage:
        python decode.py [input] [output]

        Args:
            [input]: Filename of .hc file to decode
            (output): Filename of the .txt file the decoded
                                       .hc should be saved to

        If no output filename given, then the default value of 'decode.txt'
        will be used. Please include file extensions on arguments.""")


if __name__ == '__main__':
    main()
