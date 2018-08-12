# Text-Encoder
A text file encoder that uses the lossless Huffman encoding algorithm

## Prerequisites
To use these programs, the latest version of **Python 2** needs to be installed, along with **CharDet** package. This package can be installed by issuing the following command (assuming the PIP package manager is installed):

```
pip install chardet
```

## Installation
Click 'Clone or download' above and then 'Download ZIP', or alternatively run the following command from the command line:

```
git clone https://github.com/mattingram0/Text-Encoder.git
```

## Running
Make sure to include both the .txt and .hc file extensions when running both the encode and decode programs. If the optional output filename is not given, the name of the input file will be used. If the output file already exists, the user will be prompted. Currently, the supported encoding types of the inputted text file are: ascii, UTF-8, UTF-8-SIG and UTF-16.

### Encoding
To encode a file, issue the following command:

```
python encode.py [input] (output)
```

where:
*[input] is .txt file to encode, and
*(output) is the optional .hc output file name

### Decoding
To encode a file, issue the following command:

```
python decode.py [input] (output)
```

where:
*\[input\] is .hc file to decode, and
*\(output\) is the optional .txt output file name

## Report
Included in this project is a detailed report on the time and compression efficiency of the encode.py program. The report also includes a thorough discussion of the implementation details, as well as some closing remarks on some areas of improvement.

## Example Text Files
Included also in this project are several folders containing text files of various sizes. These were used heavily in my analysis of the efficiency of the program.
