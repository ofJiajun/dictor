import re
from typing import override

import api
import addonHandler
import globalPluginHandler
import inputCore
import scriptHandler
import speech
import ui
from logHandler import log
from scriptHandler import script

from .ecdictor import INFLECTION, POSITION, Ecdictor, Lemmatizer

addonHandler.initTranslation()

ABSENCE: str = "Absence"
NO_RESULT: str = "No result"
separator = re.compile(r"[\u4e00-\uf95a]+|[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z])|[0-9]+|[A-Z]+(?![A-Z])")


def splitWord(text: str):
	words = []
	positions = []
	for word in separator.finditer(text):
		start = word.start()
		end = word.end()
		words.append(word.string[start:end])
		positions.append(start)
	if not words:
		words.append(text)
		positions.append(0)
	return words, positions


clean = re.compile(r"^[^a-zA-Z]*|[^a-zA-Z]*$")


def clean_word(word: str):
	cleaned = re.sub(clean, "", word)
	return cleaned


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		try:
			self.dict: Ecdictor | None = Ecdictor()
			self.lemma: Lemmatizer | None = Lemmatizer()
		except IOError as e:
			log.error("Fail to load dict database.")
			log.debug(e)
			self.terminate()

	@override
	def terminate(self):
		super().terminate()
		if self.dict:
			self.dict.close()
		self.dict = None
		self.lemma = None

	@script(
		# Translators: Description
		description="Get the short definition of the  word of the current navigator object where the review cursor is situated.",
		# Translators: Category
		category="Dictor",
		gestures=("kb:NVDA+w", "kb(laptop):NVDA+w"),
		speakOnDemand=True,
	)
	def script_translateLastSpeechWord(self, gesture: "inputCore.InputGesture"):
		lastSpeech = speech.speech._lastSpeech
		if lastSpeech is None:
			return

		lastSpeechSeq, symbolLevel = lastSpeech
		lastSpeechText = " ".join(i for i in lastSpeechSeq if isinstance(i, str))
		words, position = splitWord(lastSpeechText)
		if not words:
			return

		try:
			simplification, detail = self.getDefinition(words[0])
		except Exception as e:
			ui.message(NO_RESULT)
			log.error("Error occured when getting definition.")
			log.debug(e)
			return

		if simplification is None or detail is None:
			ui.message(lastSpeechText)
			return

		scriptCount = scriptHandler.getLastScriptRepeatCount()
		if scriptCount == 0:
			ui.message(simplification)
		else:
			ui.browseableMessage(detail, title=words[0], isHtml=True)

	def getDefinition(self, keyword: str) -> tuple[str, str]:
		keyword: str = clean_word(keyword)
		result: dict[str] = self.dict.query(keyword)
		if not result:
			stem: list[str] = self.lemma.word_stem(keyword)
			if not stem:
				return (None, None)
			result = self.dict.query(stem[0])

		word: str = result["word"]
		phonetic: str = f"/{result['phonetic']}/" if result["phonetic"] else ABSENCE
		definition: list[str] = result["definition"].split("\n") if result["definition"] else [ABSENCE]
		for i, d in enumerate(definition):
			if d.startswith("s."):
				definition[i] = f"a.{d[2:]}"
		translation: list[str] = result["translation"].split("\n") if result["translation"] else [ABSENCE]
		pos: list[str] = result["pos"].split("/") if result["pos"] else []
		position: list[str] = []
		if pos:
			for p in pos:
				c, d = p.split(":")
				c = POSITION[c]
				d = d + "%"
				position.append(f"<li>{c}: {d}</li>")
		else:
			position.append("Absence.")

		exch: list[str] = result["exchange"].split("/") if result["exchange"] else []
		exchange: list[str] = []
		if exch:
			for e in exch:
				c, f = e.split(":")
				c = INFLECTION[c]
				exchange.append(f"<li>{c}: {f}</li>")
		else:
			exchange.append(ABSENCE)

		frq: int = result["frq"]
		bnc: int = result["bnc"]

		simplification: str = f"{word}: {'; '.join(definition)}\n {'; '.join(translation)}"
		detail: str = f"""
			<h2>{word}</h2>
			<p>
			{phonetic}
			</p>
			<h3>Forms</h3>
			<ul>
			{" ".join(exchange)}
			</ul>
			<h3>Definition</h3>
			<ul>
			{" ".join([f"<li>{d}</li>" for d in definition])}
			</ul>
			<h3>中文释义</h3>
			<ul>
			{" ".join([f"<li>{t}</li" for t in translation])}
			</ul>
			<h3>Position Distribution</h3>
			<ul>
			{" ".join(position)}
			</ul>
			<h3>Word Frequency</h3>
			<ul>
			<li>COCA: {frq}</li>
			<li>BNC: {bnc}</li>
			</ul
		"""

		return (simplification, detail)
