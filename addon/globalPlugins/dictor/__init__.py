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

from .dictTool import INFLECTION, POSITION, Dictionary, Lemmatizer
from .generalTool import cleanWord, splitWord

addonHandler.initTranslation()

# Constants
ABSENCE: str = "Absence"
NO_RESULT: str = "No result"


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		try:
			self.dict: Dictionary | None = Dictionary()
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
		description="Spell the last spoken text. Press once, spell the last speech; twice, include character short description.",
		# Translators: Category
		category="Dictor",
		gestures=("kb:NVDA+shift+/",),
		speakOnDemand=True,
	)
	def script_SpellLastSpokenText(self, gesture: "inputCore.InputGesture"):
		lastSpeechText = self.getLastSpeechText()
		if not lastSpeechText:
			return
		scriptCount = scriptHandler.getLastScriptRepeatCount()
		speech.speech.speakSpelling(lastSpeechText, useCharacterDescriptions=scriptCount > 0)

	@script(
		# Translators: Description
		description="Get details about the current spoken word. Press once, get the short definition of the word; twice, open a document which contains more information about it.",
		# Translators: Category
		category="Dictor",
		gestures=("kb:NVDA+/",),
		speakOnDemand=True,
	)
	def script_translateLastSpeechWord(self, gesture: "inputCore.InputGesture"):
		lastSpeechText = self.getLastSpeechText()
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

	def getLastSpeechText(self) -> str:
		lastSpeech = speech.speech._lastSpeech
		if lastSpeech is None:
			return ""

		lastSpeechSeq, symbolLevel = lastSpeech
		lastSpeechText = " ".join(i for i in lastSpeechSeq if isinstance(i, str))
		return lastSpeechText if lastSpeechText else ""

	def getDefinition(self, keyword: str) -> tuple[str | None, str | None]:
		keyword: str = cleanWord(keyword)
		if not keyword:
			return (None, None)

		result: dict[str, any] = self.dict.query(keyword)
		if not result:
			stem: list[str] = self.lemma.word_stem(keyword)
			if not stem:
				return (None, None)
			result = self.dict.query(stem[0])

		return self.getFinalResult(result)

	def getFinalResult(self, item: dict[str, any]) -> tuple[str, str]:
		word: str = item["word"]

		phonetic: str = f"/{item['phonetic']}/" if item["phonetic"] else ABSENCE

		definition: list[str] = item["definition"].split("\n") if item["definition"] else [ABSENCE]
		definitionPlain: list[str] = []
		for i, d in enumerate(definition):
			if d.startswith("s."):
				definition[i] = f"a.{d[2:]}"
				d = definition[i]
			definitionPlain.append(d)
			definition[i] = f"<li>{d}</li>"

		translation: list[str] = item["translation"].split("\n") if item["translation"] else [ABSENCE]
		translationPlain: list[str] = []
		for i, t in enumerate(translation):
			translation[i] = f"<li>{t}</li>"
			translationPlain.append(t)

		pos: list[str] = item["pos"].split("/") if item["pos"] else []
		position: list[str] = []
		if pos:
			for p in pos:
				c, d = p.split(":")
				c = POSITION[c]
				d = d + "%"
				position.append(f"<li>{c}: {d}</li>")
		else:
			position.append("Absence.")

		infl: list[str] = item["transformation"].split("/") if item["transformation"] else []
		inflection: list[str] = []
		if infl:
			for e in infl:
				c, f = e.split(":")
				c = INFLECTION[c]
				inflection.append(f"<li>{c}: {f}</li>")
		else:
			inflection.append(ABSENCE)

		coca: str = f"<li>COCA: {item['coca']}</li>"
		bnc: str = f"<li>BNC: {item['bnc']}</li>"

		oxfordLevel: str = f"<li>Oxford: {item['oxford']}</li>"
		collinsLevel: str = f"<li>Collins: {item['collins']}</li>"

		simplification: str = f"{word}: {'; '.join(definitionPlain)}\n {'; '.join(translationPlain)}"
		detail: str = f"""
			<h2>{word}</h2>
			<p>
			{phonetic}
			</p>
			<h3>Forms</h3>
			<ul>
			{" ".join(inflection)}
			</ul>
			<h3>Definition</h3>
			<ul>
			{" ".join(definition)}
			</ul>
			<h3>中文释义</h3>
			<ul>
			{" ".join(translation)}
			</ul>
			<h3>Position Distribution</h3>
			<ul>
			{" ".join(position)}
			</ul>
			<h3>Word Frequency</h3>
			<ul>
			{coca}
			{bnc}
			</ul>
			<h3>Level</h3>
			<ul>
			{oxfordLevel}
			{collinsLevel}
			</ul>
"""
		return (simplification, detail)
