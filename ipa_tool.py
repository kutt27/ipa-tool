#!/usr/bin/env python3
import sys
import re
import argparse
import nltk
nltk.download('cmudict'); 
nltk.download('averaged_perceptron_tagger_eng')

# Ensure necessary NLTK components are present
try:
    d = nltk.corpus.cmudict.dict()
    # averaged_perceptron_tagger is used for POS tagging
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("[Error] Missing NLTK resources. Please run this in Python first:")
    print("    import nltk; nltk.download('cmudict'); nltk.download('averaged_perceptron_tagger')")
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

# A map to resolve common heteronyms based on NLTK Penn Treebank POS tags
HETERONYM_MAP = {
    "read": {
        "VBD": ['R', 'EH1', 'D'],  # Past tense: /ɹɛd/
        "VBN": ['R', 'EH1', 'D'],  # Past participle: /ɹɛd/
        "VBP": ['R', 'IY1', 'D'],  # Present tense: /ɹid/
        "VB":  ['R', 'IY1', 'D'],  # Base form: /ɹid/
    },
    "wind": {
        "NN":  ['W', 'IH1', 'N', 'D'], # Noun (air): /wɪnd/
        "VB":  ['W', 'AY1', 'N', 'D'], # Verb (to turn): /waɪnd/
        "VBP": ['W', 'AY1', 'N', 'D'],
    },
    "tear": {
        "NN":  ['T', 'IH1', 'R'],      # Noun (cry): /tɪɹ/
        "VB":  ['T', 'EH1', 'R'],      # Verb (rip): /tɛɹ/
        "VBP": ['T', 'EH1', 'R'],
    }
}

def fallback_syllable_count(word):
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    if len(word) == 0: return 0
    if word[0] in vowels: count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"): count -= 1
    if count == 0: count = 1
    return count

def clean_token(token):
    match = re.match(r"^([^\w]*)(.*?)([^\w]*)$", token)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return "", token, ""

def phonemes_to_ipa(phonemes):
    ipa_phones = []
    for p in phonemes:
        clean_phone = p[:-1] if p[-1].isdigit() else p
        ipa_phones.append(ARPABET_TO_IPA.get(clean_phone, clean_phone))
    return f"/{''.join(ipa_phones)}/"

def process_word(word, pos_tag):
    word_lower = word.lower()
    
    if word_lower not in d:
        return f"[{word}?]", fallback_syllable_count(word_lower), True, "OOV"

    # Rule 1: Check our contextual heteronym rules first
    if word_lower in HETERONYM_MAP and pos_tag in HETERONYM_MAP[word_lower]:
        phonemes = HETERONYM_MAP[word_lower][pos_tag]
        syllables = sum(1 for p in phonemes if p[-1].isdigit())
        return phonemes_to_ipa(phonemes), syllables, False, "Resolved via POS"

    # Rule 2: Fall back to standard dictionary retrieval
    variants = d[word_lower]
    phonemes = variants[0]
    syllables = sum(1 for p in phonemes if p[-1].isdigit())
    
    ipa_str = phonemes_to_ipa(phonemes)
    status = "Standard"
    if len(variants) > 1:
        ipa_str += "*"
        status = "Ambiguous Heteronym"
        
    return ipa_str, syllables, False, status

def process_text(text, verbose=False):
    raw_tokens = text.split()
    
    # Isolate pure words for the tagger to avoid punctuation parsing errors
    cleaned_words = [clean_token(t)[1] for t in raw_tokens]
    pos_tags = nltk.pos_tag(cleaned_words) # Returns list of (word, tag)
    
    output_ipa = []
    total_syllables = 0
    resolved_count = 0
    
    for i, token in enumerate(raw_tokens):
        prefix, word, suffix = clean_token(token)
        if not word:
            output_ipa.append(prefix)
            continue
            
        tag = pos_tags[i][1]
        ipa, syllables, is_oov, status = process_word(word, tag)
        total_syllables += syllables
        
        if status == "Resolved via POS":
            resolved_count += 1
            
        output_ipa.append(f"{prefix}{ipa}{suffix}")
        
    print("\n=== Context-Aware Phonetic Analysis ===")
    print(f"Original: {text}")
    print(f"IPA:      {' '.join(output_ipa)}")
    print(f"Syllables: {total_syllables}")
    
    if verbose:
        print("\n--- Diagnostic Footnotes ---")
        print(f" * Handled {resolved_count} heteronyms natively using syntax rules.")
        if "*" in "".join(output_ipa):
            print(" * Asterisk highlights remaining untreated heteronyms.")

def main():
    parser = argparse.ArgumentParser(description="Context-Aware CLI Phonetic Transcription")
    parser.add_argument("text", type=str, help="The English sentence to transcribe")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display diagnostic notes")
    
    args = parser.parse_args()
    process_text(args.text, args.verbose)

if __name__ == "__main__":
    main()
