"""
The module based on the project ECDICT -- a Free English to Chinese Dictionary Database.
Github: https://github.com/skywind3000/ECDICT
"""

import sys
from pathlib import Path
from typing import Any, Optional

# Use sqlite to query words
sys.path.append(str(Path(__file__).parent / "libs"))
import sqlite3


INFLECTION: dict[str, str] = {
	"p": "Past tense",
	"d": "Past participle",
	"i": "Present participle",
	"3": "Third person singular",
	"r": "Comparative form ",
	"t": "Superlative form",
	"s": "Plural form",
	"0": "lemma",
	"1": "Variants of the lemma",
}


POSITION: dict[str, str] = {
	"n": "Noun",
	"j": "Adjective",
	"v": "Verb",
	"r": "Adverb",
	"m": "Numeral",
	"p": "Pronoun",
	"a": "Article",
	"i": "Preposition",
	"c": "Conjunction",
	"u": "Interjection",
	"d": "Determiner",
	"t": "The infinitive marker",
	"s": "Adjective",
}

# Data path
DICT = r"C:\Users\celer\AppData\Roaming\nvda\scratchpad\dicts\dictor.db"
LEMMA = r"C:\Users\celer\AppData\Roaming\nvda\scratchpad\dicts\lemma.txt"

unicode = str
long = int


def stripword(word: str) -> str:
	return ("".join([n for n in word if n.isalnum()])).lower()


class Dictionary(object):
	def __init__(self, filename: str = DICT):
		self.__dbname = filename
		self.__conn = None
		self.__fields = None
		self.__enable = None
		self.__names = {}
		self.__open()

	def __open(self) -> bool:
		self.__conn = sqlite3.connect(self.__dbname, isolation_level="IMMEDIATE")

		fields = (
			"id",
			"word",
			"sw",
			"phonetic",
			"definition",
			"translation",
			"pos",
			"collins",
			"oxford",
			"bnc",
			"coca",
			"transformation",
		)
		self.__fields = tuple([(fields[i], i) for i in range(len(fields))])
		for k, v in self.__fields:
			self.__names[k] = v
		self.__enable = self.__fields[3:]
		return True

	def __record2obj(self, record: Any) -> dict[str, Any] | None:
		if record is None:
			return None
		word = {}
		for k, v in self.__fields:
			word[k] = record[v]
		return word

	def close(self):
		if self.__conn:
			self.__conn.close()
		self.__conn = None

	def __del__(self):
		self.close()

	def query(self, key: str) -> dict[str, Any]:
		c = self.__conn.cursor()
		record = None
		if isinstance(key, int) or isinstance(key, long):
			c.execute("select * from dictor where id = ?;", (key,))
		elif isinstance(key, str) or isinstance(key, unicode):
			c.execute("select * from dictor where word = ?", (key,))
		else:
			return None
		record = c.fetchone()
		return self.__record2obj(record)

	def match(self, word: str, limit: int = 10, strip: bool = False) -> list[tuple[int, str]]:
		c = self.__conn.cursor()
		if not strip:
			sql = "select id, word from dictor where word >= ? "
			sql += "order by word collate nocase limit ?;"
			c.execute(sql, (word, limit))
		else:
			sql = "select id, word from dictor where sw >= ? "
			sql += "order by sw, word collate nocase limit ?;"
			c.execute(sql, (stripword(word), limit))
		records = c.fetchall()
		result = []
		for record in records:
			result.append(tuple(record))
		return result

	def query_batch(self, keys: list[str]) -> tuple[dict[str, Any]]:
		sql = "select * from dictor where "
		if keys is None:
			return None
		if not keys:
			return []
		querys = []
		for key in keys:
			if isinstance(key, int) or isinstance(key, long):
				querys.append("id = ?")
			elif key is not None:
				querys.append("word = ?")
		sql = sql + " or ".join(querys) + ";"
		query_word = {}
		query_id = {}
		c = self.__conn.cursor()
		c.execute(sql, tuple(keys))
		for row in c:
			obj = self.__record2obj(row)
			query_word[obj["word"].lower()] = obj
			query_id[obj["id"]] = obj
		results = []
		for key in keys:
			if isinstance(key, int) or isinstance(key, long):
				results.append(query_id.get(key, None))
			elif key is not None:
				results.append(query_word.get(key.lower(), None))
			else:
				results.append(None)
		return tuple(results)

	def count(self) -> int:
		c = self.__conn.cursor()
		c.execute("select count(*) from dictor;")
		record = c.fetchone()
		return record[0]

	def register(self, word: str, items: dict, commit: bool = True) -> bool:
		sql = "INSERT INTO dictor(word, sw) VALUES(?, ?);"
		try:
			self.__conn.execute(sql, (word, stripword(word)))
		except sqlite3.IntegrityError as e:
			self.out(str(e))
			return False
		except sqlite3.Error as e:
			self.out(str(e))
			return False
		self.update(word, items, commit)
		return True

	def remove(self, key: str, commit: bool = True) -> bool:
		if isinstance(key, int) or isinstance(key, long):
			sql = "DELETE FROM dictor WHERE id=?;"
		else:
			sql = "DELETE FROM dictor WHERE word=?;"
		try:
			self.__conn.execute(sql, (key,))
			if commit:
				self.__conn.commit()
		except sqlite3.IntegrityError:
			return False
		return True

	def delete_all(self, reset_id: bool = False) -> bool:
		sql1 = "DELETE FROM dictor;"
		sql2 = "UPDATE sqlite_sequence SET seq = 0 WHERE name = 'dictor';"
		try:
			self.__conn.execute(sql1)
			if reset_id:
				self.__conn.execute(sql2)
			self.__conn.commit()
		except sqlite3.IntegrityError as e:
			self.out(str(e))
			return False
		except sqlite3.Error as e:
			self.out(str(e))
			return False
		return True

	def update(self, key: str, items: dict, commit: bool = True) -> bool:
		names = []
		values = []
		for name, id in self.__enable:
			if name in items:
				names.append(name)
				value = items[name]
				values.append(value)
		if len(names) == 0:
			if commit:
				try:
					self.__conn.commit()
				except sqlite3.IntegrityError:
					return False
			return False
		sql = "UPDATE dictor SET " + ", ".join(["%s=?" % n for n in names])
		if isinstance(key, str) or isinstance(key, unicode):
			sql += " WHERE word=?;"
		else:
			sql += " WHERE id=?;"
		try:
			self.__conn.execute(sql, tuple(values + [key]))
			if commit:
				self.__conn.commit()
		except sqlite3.IntegrityError:
			return False
		return True

	def __iter__(self):
		c = self.__conn.cursor()
		sql = 'select "id", "word" from "dictor"'
		sql += ' order by "word" collate nocase;'
		c.execute(sql)
		return c.__iter__()

	def __len__(self):
		return self.count()

	def __contains__(self, key):
		return self.query(key) is not None

	def __getitem__(self, key):
		return self.query(key)

	def commit(self) -> bool:
		try:
			self.__conn.commit()
		except sqlite3.IntegrityError:
			self.__conn.rollback()
			return False
		return True

	def dumps(self) -> list[str]:
		return [n for _, n in self.__iter__()]


class Lemmatizer(object):
	def __init__(self, filename: str = LEMMA, encoding: str = None):
		self._stems = {}
		self._words = {}
		self._frqs = {}
		self.load(filename, encoding)

	def load(self, filename: str, encoding: str = None):
		content = open(filename, "rb").read()
		if content[:3] == b"\xef\xbb\xbf":
			content = content[3:].decode("utf-8", "ignore")
		elif encoding is not None:
			text = content.decode(encoding, "ignore")
		else:
			text = None
			match = ["utf-8", sys.getdefaultencoding(), "ascii"]
			for encoding in match + ["gbk", "latin1"]:
				try:
					text = content.decode(encoding)
					break
				except Exception:
					pass
			if text is None:
				text = content.decode("utf-8", "ignore")
		number = 0
		for line in text.split("\n"):
			number += 1
			line = line.strip("\r\n ")
			if (not line) or (line[:1] == ";"):
				continue
			pos = line.find("->")
			if not pos:
				continue
			stem = line[:pos].strip()
			p1 = stem.find("/")
			frq = 0
			if p1 >= 0:
				frq = int(stem[p1 + 1 :].strip())
				stem = stem[:p1].strip()
			if not stem:
				continue
			if frq > 0:
				self._frqs[stem] = frq
			for word in line[pos + 2 :].strip().split(","):
				p1 = word.find("/")
				if p1 >= 0:
					word = word[:p1].strip()
				if not word:
					continue
				self.add(stem, word.strip())
		return True

	def save(self, filename: str, encoding: str = "utf-8") -> bool:
		stems = list(self._stems.keys())
		stems.sort(key=lambda x: x.lower())
		import codecs

		fp = codecs.open(filename, "w", encoding)
		output = []
		for stem in stems:
			words = self.get(stem)
			if not words:
				continue
			frq = self._frqs.get(stem, 0)
			if frq > 0:
				stem = "%s/%d" % (stem, frq)
			output.append((-frq, "%s -> %s" % (stem, ",".join(words))))
		output.sort()
		for _, text in output:
			fp.write(text + "\n")
		fp.close()
		return True

	def add(self, stem: str, word: str) -> bool:
		if stem not in self._stems:
			self._stems[stem] = {}
		if word not in self._stems[stem]:
			self._stems[stem][word] = len(self._stems[stem])
		if word not in self._words:
			self._words[word] = {}
		if stem not in self._words[word]:
			self._words[word][stem] = len(self._words[word])
		return True

	def remove(self, stem: str, word: str) -> bool:
		count = 0
		if stem in self._stems:
			if word in self._stems[stem]:
				del self._stems[stem][word]
				count += 1
			if not self._stems[stem]:
				del self._stems[stem]
		if word in self._words:
			if stem in self._words[word]:
				del self._words[word][stem]
				count += 1
			if not self._words[word]:
				del self._words[word]
		return (count > 0) and True or False

	def reset(self) -> bool:
		self._stems = {}
		self._words = {}
		return True

	def get(self, word: str, reverse: bool = False) -> Optional[list[str]]:
		if not reverse:
			if word not in self._stems:
				if word in self._words:
					return [word]
				return None
			words = [(v, k) for (k, v) in self._stems[word].items()]
		else:
			if word not in self._words:
				if word in self._stems:
					return [word]
				return None
			words = [(v, k) for (k, v) in self._words[word].items()]
		words.sort()
		return [k for (v, k) in words]

	def word_stem(self, word: str) -> Optional[list[str]]:
		return self.get(word, reverse=True)

	def stem_size(self) -> int:
		return len(self._stems)

	def word_size(self) -> int:
		return len(self._words)

	def dump(self, what: str = "ALL") -> dict[str, int]:
		words = {}
		what = what.lower()
		if what in ("all", "stem"):
			for word in self._stems:
				words[word] = 1
		if what in ("all", "word"):
			for word in self._words:
				words[word] = 1
		return words

	def __len__(self):
		return len(self._stems)

	def __getitem__(self, stem):
		return self.get(stem)

	def __contains__(self, stem):
		return stem in self._stems

	def __iter__(self):
		return self._stems.__iter__()
