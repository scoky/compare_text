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

# Dictionary with a limited capacity and least recently used keys are evicted
class LRU(object):
    class Node(object):
        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.next = None
            self.prev = None

    def __init__(self, limit):
        self.limit = limit
        self.dict = {}
        self.head = None
        self.tail = None
        
    def put(self, key, value):
        while len(self.dict) >= self.limit:
            self._rm()
        node = LRU.Node(key, value)
        self.dict[key] = node
        self._moveup(node)
        
    def get(self, key):
        node = self.dict[key]
        self._moveup(node)
        return node.value
        
    def _moveup(self, node):
        p = node.prev
        n = node.next
        if p:
            p.next = n
        if n:
            n.prev = p
        node.next = None
        node.prev = self.tail
        if self.tail:
            self.tail.next = node
        self.tail = node
        if self.head is node:
            self.head = n
        elif not self.head:
            self.head = node
        
    def _rm(self):
        del self.dict[self.head.key]
        n = self.head.next
        if n:
            n.prev = None
        if self.tail is self.head:
            self.tail = n
        self.head = n

def cached(func):
    cache = LRU(10000)
    @wraps(func)
    def wrapper(*args):
        key = (func, )+args
        try:
            ret = cache.get(key)
        except KeyError:
            ret = func(*args)
            cache.put(key, ret)
        return ret
    return wrapper

@cached
def LCS(list1, list2):
    if len(list1)==0 or len(list2)==0:
        return tuple()
    if list1[0].clean == list2[0].clean:
        return ((list1[0],list2[0]),)+LCS(list1[1:], list2[1:])
    else:
        lhs = LCS(list1[1:], list2)
        rhs = LCS(list1, list2[1:])
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
        self.valid = self.clean not in Word.COMMON_WORDS[:args.exclude+1]
        self.line = line
        self.index = None

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
    
    i1 = 0
    while i1 <= len(valid_text1)-args.range:
        for i2 in range(len(valid_text2)):
            word1 = valid_text1[i1]
            word2 = valid_text2[i2]
            # Word match, explore forward to see if there is a phrase match
            if word1.clean == word2.clean:
                seq1 = valid_text1[i1:i1+args.range]
                seq2 = valid_text2[i2:i2+args.range]
                match = LCS(seq1, seq2)
                if len(match) >= args.threshold:
                    args.outfile.write(format_sequence(match, text1, text2))
                    i1+=args.range-1
                    break
        i1+=1

