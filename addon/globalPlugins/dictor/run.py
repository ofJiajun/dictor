import re
import os
from dictTool import Dictionary
from collections import namedtuple

class Word:
	def __init__(self,word, items):
		self.word = word
		self.items = items

d1 = Dictionary()
all = d1.dumps()
filters = set()

for a in all:
	r = d1.query(a)
	ph = r['phonetic']
	defi = r['definition']
	trans = r['transformation']
	if not ph and not defi and not trans:
		continue
	filters.add(Word(a, r))

d2 = Dictionary('./new.db')

x = list(filters)

count = 0
for a in x:
	d2.register(a.word, a.items)
	count +=1


print("len(filters): " + len(filters))
print("register count: " + count)


