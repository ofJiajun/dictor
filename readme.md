# Dictor

This is a simple dictionary add-on for NVDA. It allows you to look up definitions for the word located under the review cursor within the current navigator object.

The concept is inspired by NVDA’s built-in feature that provides short descriptions for characters, but this add-on applies that logic to full English words. It enables users to get a quick explanation for a word without needing to switch windows to look it up. Because the add-on relies on a local database, the lookup speed is instantaneous.

The add-on supports two levels of detail: short and long. In short mode, NVDA simply speaks the English definitions for the word. In long mode, a browsable document pops up, providing more comprehensive details about the target word.

## Operation

Press NVDA + W:

- Once: Reports the definition of the word under the current navigator object.
- Twice: Opens a browsable message displaying the full details.

This gesture can be customized in  
`Preferences > Input gestures > Dictor`.

## About the Dictionary

The dictionary data is sourced from the [ECDICT project](https://github.com/skywind3000/ECDICT).

To accommodate different user needs, I have prepared two versions of the database:

- Basic Version: Approximately 182MB, containing over 700,000 entries.
- Complete Version: Approximately 790MB, supporting queries for over 3 million entries.

Due to the large file sizes, these databases are not included in the standard code base. If you need to manually package the plugin, please download the data separately and place it in the following directory:  
`addon/globalPlugins/Dictor/dicts`

Minor modifications have been made to the original database for better compatibility:

1. Phonetic Symbols: Some phonetic symbols (e.g., 'ә') have been adjusted to be more friendly for common speech synthesizers.
2. Error Correction: A few character errors were corrected during my usage, though this is not a comprehensive fix. Given the massive size of the data, I believe minor errors are unavoidable.
