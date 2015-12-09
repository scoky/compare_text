#!/usr/bin/python

import os
import sys
import argparse
import string
from functools import wraps

# Output similarities in color
class color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def cached(func):
    cache = {}
    @wraps(func)
    def wrapper(*args):
        key = (func, )+args
        try:
            ret = cache[key]
        except KeyError:
            ret = func(*args)
            cache[key] = ret
        return ret
    return wrapper

class LCS(object):
    def __init__(self):
        self.lcs = cached(self.lcs)

    def lcs(self, list1, list2):
        if len(list1)==0 or len(list2)==0:
            return tuple()
        if list1[-1].clean == list2[-1].clean:
            return self.lcs(list1[:-1], list2[:-1])+((list1[-1],list2[-1]),)
        else:
            lhs = self.lcs(list1[:-1], list2)
            rhs = self.lcs(list1, list2[:-1])
            return lhs if len(lhs) > len(rhs) else rhs
        
class Word(object):
    # Most common words in English: https://en.wikipedia.org/wiki/Most_common_words_in_English
    COMMON_WORDS = ('', 'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as'
                    'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will',
                    'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which',
                    'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take')

    def __init__(self, word, line):
        self.word = word
        self.output = word
        self.clean = word.lower().translate(None, args.translator)
        self.valid = self.clean not in Word.COMMON_WORDS[:args.exclude]
        self.line = line
        self.index = None

def sequence(data, size):
    for i in range(0, len(data), size):
            yield data[i:i+size]
            
def parse_file(infile):            
    text = []
    for lineno,line in enumerate(infile):
        words = [Word(word, lineno+1) for word in line.strip().split()]
        text.extend(words)
    index = 0
    for word in text:
        word.index = index
        index += 1
    return tuple(text)
    
def format_sequence(match, text1, text2):
    rng1 = [max(0, match[0][0].index - args.threshold), min(len(text1), match[-1][0].index + args.threshold)]
    rng2 = [max(0, match[0][1].index - args.threshold), min(len(text2), match[-1][1].index + args.threshold)]
    if args.color:
        for m1,m2 in match:
            m1.output = color.YELLOW + m1.word + color.END
            m2.output = color.YELLOW + m2.word + color.END
    str1 = ' '.join(w.output for w in text1[rng1[0]:rng1[1]])
    str2 = ' '.join(w.output for w in text2[rng2[0]:rng2[1]])
    if args.color:
        for m1,m2 in match:
            m1.output = m1.word
            m2.output = m2.word
        return "%s[FILE1-%d]%s %s\n%s[FILE2-%d]%s %s\n\n" %(color.BLUE, match[0][0].line, color.END, str1, color.GREEN, match[0][1].line, color.END, str2)
    else:
        return "[FILE1-%d] %s\n[FILE2-%d] %s\n\n" %(match[0][0].line, str1, match[0][1].line, str2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Compare two text files for similarities')
    parser.add_argument('infile1', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('infile2', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-r', '--range', type=int, default=7, help='number of words to compare at a time')
    parser.add_argument('-t', '--threshold', type=int, default=6, help='minimum number of matching words to identify a similarity in a range')
    parser.add_argument('-e', '--exclude', type=int, default=0, help='exclude the e most common english words from similarity')
    parser.add_argument('-c', '--color', action='store_true', default=False, help='output similarities in color')
    args = parser.parse_args()

    args.translator = string.maketrans(string.ascii_lowercase, ' '*len(string.ascii_lowercase))

    text1 = parse_file(args.infile1)
    args.infile1.close()
    valid_text1 = tuple([word for word in text1 if word.valid])

    text2 = parse_file(args.infile2)
    args.infile2.close()
    valid_text2 = tuple([word for word in text2 if word.valid])    
    
    for seq1 in sequence(valid_text1, args.range):
        for seq2 in sequence(valid_text2, args.range):
            match = LCS().lcs(seq1, seq2)
            if len(match) >= args.threshold:
                args.outfile.write(format_sequence(match, text1, text2))
                break

