import api
import globalPluginHandler
import inputCore
import addonHandler
from logHandler import log
import scriptHandler
from scriptHandler import script
import re
import textInfos
import ui


from .ecdictor import Ecdictor, Lemmatizer, EXCHANGE, POSITION


addonHandler.initTranslation()

ABSENCE: str = "Absence"


def clean_word(word):
	cleaned = re.sub(r"^[^a-zA-Z]*|[^a-zA-Z]*$", "", word)
	return cleaned


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		try:
			self.dict = Ecdictor()
			self.lemma = Lemmatizer()
		except Exception as e:
			log.error("Fail to load dict database.")
			log.debug(e)
			self.terminate()

	def terminate(self):
		super().terminate()
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
	def script_GetDictorDefinition(self, gesture: inputCore.InputGesture):
		info: textInfos.TextInfo = api.getReviewPosition().copy()
		info.expand(textInfos.UNIT_WORD)
		try:
			simplification, detail = self.getDefinition(info.text)
		except Exception as e:
			ui.message("No result")
			log.error("Error occured when getting definition.")
			log.debug(e)
			return

		scriptCount = scriptHandler.getLastScriptRepeatCount()
		if scriptCount == 0:
			ui.message(simplification)
		else:
			ui.browseableMessage(detail, title=info.text, isHtml=True)

	def getDefinition(self, keyword: str) -> tuple[str, str]:
		keyword: str = clean_word(keyword)
		result: dict[str] = self.dict.query(keyword)
		if not result:
			stem: list[str] = self.lemma.word_stem(keyword)
			if not stem:
				return ("No result", "No result")
			result = self.dict.query(stem[0])

		word: str = result["word"]
		phonetic: str = f"/{result['phonetic']}/" if result["phonetic"] else ABSENCE
		definition: list[str] = (
			result["definition"].split("\n") if result["definition"].split("\n") else [ABSENCE]
		)
		translation: list[str] = (
			result["translation"].split("\n") if result["translation"].split("\n") else [ABSENCE]
		)
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
				c = EXCHANGE[c]
				exchange.append(f"<li>{c}: {f}</li>")
		else:
			exchange.append(ABSENCE)

		frq: int = result["frq"]
		bnc: int = result["bnc"]

		simplification: str = f"{word}: {'; '.join(definition)}"
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
