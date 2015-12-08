#!/usr/bin/python

import os
import sys
import argparse
import string
from functools import wraps

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def cached(func):
  cache = {}
  @wraps(func)
  def wrapper(*args):
    key = (func, )+args
    try:
      ret = cache[key]
    except KeyError:
      ret = func(*args)
      if len(cache) > 10000:
        cache.clear()
      cache[key] = ret
    return ret
  return wrapper

@cached
def LCS(list1, list2):
  if len(list1)==0 or len(list2)==0:
    return 0
  if list1[-1].clean == list2[-1].clean:
    return LCS(list1[:-1], list2[:-1])+1
  else:
    return max(LCS(list1, list2[:-1]), LCS(list1[:-1], list2))
        
class Word(object):
    exclude = ('',)
     #('of', 'the', 'a', 'an', 'and', 'in', '', 'dns', 'we')

    def __init__(self, word, line):
        self.word = word
        self.clean = word.translate(None, args.translator)
        self.valid = self.clean not in Word.exclude
        self.line = line
        self.index = None

def sequence(data, size):
    for i in range(0, len(data), size):
            yield data[i:i+size]
            
def parse_file(infile):            
    text = []
    for lineno,line in enumerate(infile):
        words = [Word(word, lineno+1) for word in line.strip().lower().split()]
        text.extend(words)
    index = 0
    for word in text:
        word.index = index
        index += 1
    return tuple(text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Compare two text files for similarities')
    parser.add_argument('infile1', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('infile2', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-t', '--threshold', type=int, default=6, help='minimum number of matching words to identify a similarity')
    args = parser.parse_args()

    args.translator = string.maketrans(string.ascii_lowercase, ' '*len(string.ascii_lowercase))

    text1 = parse_file(args.infile1)
    args.infile1.close()
    valid_text1 = tuple([word for word in text1 if word.valid])

    text2 = parse_file(args.infile2)
    args.infile2.close()
    valid_text2 = tuple([word for word in text2 if word.valid])    
    
    for seq1 in sequence(valid_text1, args.threshold+3):
        for seq2 in sequence(valid_text2, args.threshold+3):
            matching = LCS(seq1, seq2)
            if matching >= args.threshold:
                smin = max(0, seq1[0].index - args.threshold)
                smax = min(len(text1), seq1[-1].index + args.threshold)
                str1 = ' '.join(w.word for w in text1[smin:smax])
                smin = max(0, seq2[0].index - args.threshold)
                smax = min(len(text2), seq2[-1].index + args.threshold)
                str2 = ' '.join(w.word for w in text2[smin:smax])
                args.outfile.write("[FILE1-%d] %s\n[FILE2-%d] %s\n\n" %(seq1[0].line, str1, seq2[0].line, str2))
                break

