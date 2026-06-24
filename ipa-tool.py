#!/usr/bin/env python3
import sys
import re
import argparse
import nltk
nltk.download('cmudict')
from nltk.corpus import cmudict

# moving into try catch due to circulat import
try:
    d = cmudict.dict()
except LookupError:
    print("[Error] CMUdict not found. Please run the following in Python first:")
    print("    import nltk; nltk.download('cmudict')")
    sys.exit(1)

ARPABET_TO_IPA = {
    'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ', 'AX': 'ə',
    'AY': 'aɪ', 'EH': 'ɛ', 'ER': 'ɜr', 'EY': 'eɪ', 'IH': 'ɪ', 'IX': 'ɨ',
    'IY': 'i', 'OW': 'oʊ', 'OY': 'ɔɪ', 'UH': 'ʊ', 'UW': 'u', 'UX': 'ʉ',
    'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð', 'EL': 'l̩', 'EM': 'm̩',
    'EN': 'n̩', 'F': 'f', 'G': 'ɡ', 'HH': 'h', 'JH': 'dʒ', 'K': 'k',
    'L': 'l', 'M': 'm', 'N': 'n', 'NX': 'ɾ̃', 'NG': 'ŋ', 'P': 'p',
    'Q': 'ʔ', 'R': 'ɹ', 'S': 's', 'SH': 'ʃ', 'T': 't', 'TH': 'θ',
    'V': 'v', 'W': 'w', 'WH': 'ʍ', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ',
    'DX': 'ɾ'
}

def fallback_syllable_count(word):
    """
    A heuristic algorithm (Sonnenschein's rule variant) to estimate syllables
    when a word is missing from the dictionary.
    """
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    if len(word) == 0:
        return 0
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count == 0:
        count = 1
    return count

def clean_token(token):
    """Separates punctuation from the core word."""
    match = re.match(r"^([^\w]*)(.*?)([^\w]*)$", token)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return "", token, ""

def process_word(word):
    """Processes a clean word to find its IPA mapping and syllable count."""
    word_lower = word.lower()

    if word_lower not in d:
        # Edge Case 1: OOV fallback
        return f"[{word}?]", fallback_syllable_count(word_lower), True

    # Fetch all variants to spot heteronyms (Edge Case 3)
    variants = d[word_lower]
    has_variants = len(variants) > 1

    # Process the primary pronunciation variant
    phonemes = variants[0]
    syllables = sum(1 for p in phonemes if p[-1].isdigit())

    ipa_phones = []
    for p in phonemes:
        clean_phone = p[:-1] if p[-1].isdigit() else p
        ipa_phones.append(ARPABET_TO_IPA.get(clean_phone, clean_phone))

    ipa_str = f"/{''.join(ipa_phones)}/"
    if has_variants:
        ipa_str += "*" # Mark with asterisk to denote alternate pronunciations exist

    return ipa_str, syllables, False

def process_text(text, verbose=False):
    tokens = text.split()
    output_ipa = []
    total_syllables = 0
    oov_count = 0

    for token in tokens:
        prefix, word, suffix = clean_token(token)
        if not word:  # Just pure punctuation
            output_ipa.append(prefix)
            continue

        ipa, syllables, is_oov = process_word(word)
        total_syllables += syllables
        if is_oov:
            oov_count += 1

        output_ipa.append(f"{prefix}{ipa}{suffix}")

    result_str = " ".join(output_ipa)

    print("\n=== Phonetic Analysis ===")
    print(f"Original: {text}")
    print(f"IPA:      {result_str}")
    print(f"Syllables: {total_syllables}")

    if verbose:
        print("\n--- Diagnostic Footnotes ---")
        if "*" in result_str:
            print(" * Asterisk indicates words with multiple valid pronunciations (heteronyms).")
        if oov_count > 0:
            print(" [Word?] indicates Out-Of-Vocabulary words approximated via backup rule engine.")

def main():
    parser = argparse.ArgumentParser(description="CLI Phonetic Transcription & Syllable Counter")
    parser.add_argument("text", type=str, help="The English sentence or phrase to transcribe")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display linguistic edge-case footnotes")

    args = parser.parse_args()
    process_text(args.text, args.verbose)

if __name__ == "__main__":
    main()
