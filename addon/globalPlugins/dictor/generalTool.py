import re


separator = re.compile(r"[\u4e00-\uf95a]+|[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z])|[0-9]+|[A-Z]+(?![A-Z])")
clean = re.compile(r"^[^a-zA-Z]*|[^a-zA-Z]*$")


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


def cleanWord(word: str):
	cleaned = re.sub(clean, "", word)
	return cleaned
