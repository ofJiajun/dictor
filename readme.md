# Dictor

Dictor is a lightweight dictionary add-on for NVDA that provides instant definitions for the last spoken word.

The concept is inspired by NVDA's built-in character description feature, which delivers short definitions for individual characters. Dictor extends this idea to full English words, allowing users to obtain a quick explanation without switching windows or opening a browser. Because the add-on relies on a local database, lookups are instantaneous.

Two levels of detail are supported: **short** and **long**. In short mode, NVDA simply reads aloud the English and Chinese definitions of the word. In long mode, a browsable window pops up, presenting more comprehensive information about the target word.

## Operation

### NVDA + /

- **Press once**: Reports the definition of the last spoken word. If the utterance contains more than one word, Dictor isolates the first word and looks it up.
- **Press twice**: Opens a browsable message window displaying the full entry details.

### NVDA + Shift + /

- **Press once**: Spells out the last spoken word letter by letter.
- **Press twice**: Spells out the last spoken word and provides a character description for each letter.

These gestures can be remapped in  
`Preferences > Input gestures > Dictor`.

## About the Dictionary

The dictionary data is sourced from the [ECDICT project](https://github.com/skywind3000/ECDICT).

A few filtering decisions were made during preprocessing. Only entries that include an English definition, a part-of-speech label, or inflectional forms are retained, resulting in a curated set of 672,014 entries. This covers the vast majority of everyday use cases.

Certain characters have been replaced to improve speech synthesis compatibility. For example, phonetic symbols may render correctly on screen but are not recognized by the speech synthesizer, so they have been substituted with their spoken equivalents.

Additional minor errors have also been corrected along the way. The result is a clean, reliable dictionary database well suited for use with this add-on.

**Note**: that these dictionary files are not included in the source code, but provided along with the [released add-on package](https://github.com/ofJiajun/dictor/releases).

All preprocessing utilities are available in `dictTool.py`. Feel free to adapt them to your own needs.
