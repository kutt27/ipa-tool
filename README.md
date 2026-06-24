A simple phonetic transcription tool, or international phonetic alphabet converter

**Architecture**
![IPA Architecture]("layered-architecture.png")

*Problems with notebook implementation*:
- Out-of-Vocabulary (OOV) Words: What happens when a user types a word not in CMUdict (like a brand name, modern slang, or a typo)? We need a fallback regex-based heuristic syllable counter and a way to signal missing IPA data.
- Punctuation & Tokenization: Commas, periods, and em-dashes shouldn't break our lookups or get fused to the words.
- Homographs (The "Heteronym" Problem): Words like wind (blowing air) vs. wind (to clock a watch), or tear (cry) vs. tear (rip). CMUdict actually provides multiple pronunciations for these, and a truly robust CLI should let the user know when an ambiguity exists.

**Status**:
```
(.venv)    ipa-tool   git:(master)  ./ipa-tool.py "I read books in quixotify fashion." -v
[nltk_data] Downloading package cmudict to /home/kutt/nltk_data...
[nltk_data]   Unzipping corpora/cmudict.zip.

=== Phonetic Analysis ===
Original: I read books in quixotify fashion.
IPA:      /aɪ/ /ɹɛd/* /bʊks/ /ɪn/* [quixotify?] /fæʃʌn/.
Syllables: 10

--- Diagnostic Footnotes ---
 * Asterisk indicates words with multiple valid pronunciations (heteronyms).
 [Word?] indicates Out-Of-Vocabulary words approximated via backup rule engine.
```
