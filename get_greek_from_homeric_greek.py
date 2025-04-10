import pandas as pd
import string
from brute_cognates import latinize_greek
def has_digit(string): #this function helped me  prove that the only words having digits are a '9', so we can remove them
    digits = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
    for letter in string:
        if letter in digits:
            return True
    return False

df = pd.read_csv('./lemmatized_homeric_greek.csv')

words_set = set()

translator = str.maketrans('', '', string.punctuation)

alphabet = {
    'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ',
    'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π',
    'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω',
    'ς', 
    'Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ζ', 'Η', 'Θ',
    'Ι', 'Κ', 'Λ', 'Μ', 'Ν', 'Ξ', 'Ο', 'Π',
    'Ρ', 'Σ', 'Τ', 'Υ', 'Φ', 'Χ', 'Ψ', 'Ω'
}

diacritic_to_base = {
    # Lowercase
    'ἀ': 'α', 'ἁ': 'α', 'ἂ': 'α', 'ἃ': 'α', 'ἄ': 'α', 'ἅ': 'α', 'ἆ': 'α', 'ἇ': 'α',
    'ὰ': 'α', 'ά': 'α', 'ᾀ': 'α', 'ᾁ': 'α', 'ᾂ': 'α', 'ᾃ': 'α', 'ᾄ': 'α', 'ᾅ': 'α', 'ᾆ': 'α', 'ᾇ': 'α',
    'ᾰ': 'α', 'ᾱ': 'α', 'ά' : 'α', 'ᾶ': 'α', 'ᾷ': 'α', 'ᾳ': 'α','ᾴ': 'α',

    'ἐ': 'ε', 'ἑ': 'ε', 'ἒ': 'ε', 'ἓ': 'ε', 'ἔ': 'ε', 'ἕ': 'ε', 'ὲ': 'ε', 'έ': 'ε', 'έ': 'ε',

    'ἠ': 'η', 'ἡ': 'η', 'ἢ': 'η', 'ἣ': 'η', 'ἤ': 'η', 'ἥ': 'η', 'ἦ': 'η', 'ἧ': 'η',
    'ὴ': 'η', 'ή': 'η', 'ῂ': 'η', 'ῃ': 'η', 'ῄ': 'η', 'ῆ': 'η', 'ῇ': 'η', 'ή': 'η', 'ᾔ': 'η', 'ᾐ': 'η', 'ᾖ': 'η',

    'ἰ': 'ι', 'ἱ': 'ι', 'ἲ': 'ι', 'ἳ': 'ι', 'ἴ': 'ι', 'ἵ': 'ι', 'ἶ': 'ι', 'ἷ': 'ι',
    'ὶ': 'ι', 'ί': 'ι', 'ϊ': 'ι', 'ΐ': 'ι', 'ῐ': 'ι', 'ῑ': 'ι', 'ῒ': 'ι', 'ΐ': 'ι', 'ῖ': 'ι', 'ῗ': 'ι', 'ί': 'ι',

    'ὀ': 'ο', 'ὁ': 'ο', 'ὂ': 'ο', 'ὃ': 'ο', 'ὄ': 'ο', 'ὅ': 'ο', 'ὸ': 'ο', 'ό': 'ο', 'ό': 'ο', 'o':'ο',

    'ὐ': 'υ', 'ὑ': 'υ', 'ὒ': 'υ', 'ὓ': 'υ', 'ὔ': 'υ', 'ὕ': 'υ', 'ὖ': 'υ', 'ὗ': 'υ',
    'ὺ': 'υ', 'ύ': 'υ', 'ϋ': 'υ', 'ΰ': 'υ', 'ῠ': 'υ', 'ῡ': 'υ', 'ῢ': 'υ', 'ΰ': 'υ', 'ῦ': 'υ', 'ῧ': 'υ', 'ύ': 'υ',

    'ὠ': 'ω', 'ὡ': 'ω', 'ὢ': 'ω', 'ὣ': 'ω', 'ὤ': 'ω', 'ὥ': 'ω', 'ὦ': 'ω', 'ὧ': 'ω',
    'ῲ': 'ω', 'ώ': 'ω', 'ῳ': 'ω', 'ῴ': 'ω', 'ῶ': 'ω', 'ῷ': 'ω', 'ώ': 'ω', 'ᾠ': 'ω', 'ᾤ': 'ω', 'ὼ': 'ω',

    'ῤ': 'ρ', 'ῥ': 'ρ',

    # Uppercase
    'Ἀ': 'Α', 'Ἁ': 'Α', 'Ἄ': 'Α', 'Ἅ': 'Α', 'Ἂ': 'Α', 'Ἃ': 'Α', 'Ἆ': 'Α', 'Ἇ': 'Α', 'ᾍ': 'Α',

    'Ἐ': 'Ε', 'Ἑ': 'Ε', 'Ἒ': 'Ε', 'Ἓ': 'Ε', 'Ἔ': 'Ε', 'Ἕ': 'Ε',

    'Ἠ': 'Η', 'Ἡ': 'Η', 'Ἢ': 'Η', 'Ἣ': 'Η', 'Ἤ': 'Η', 'Ἥ': 'Η', 'Ἦ': 'Η', 'Ἧ': 'Η',

    'Ἰ': 'Ι', 'Ἱ': 'Ι', 'Ἲ': 'Ι', 'Ἳ': 'Ι', 'Ἴ': 'Ι', 'Ἵ': 'Ι', 'Ἶ': 'Ι', 'Ἷ': 'Ι',
    'Ί': 'Ι', 'Ϊ': 'Ι',

    'Ὀ': 'Ο', 'Ὁ': 'Ο', 'Ὂ': 'Ο', 'Ὃ': 'Ο', 'Ὄ': 'Ο', 'Ὅ': 'Ο',

    'Ὠ': 'Ω', 'Ὡ': 'Ω', 'Ὢ': 'Ω', 'Ὣ': 'Ω', 'Ὤ': 'Ω', 'Ὥ': 'Ω', 'Ὦ': 'Ω', 'Ὧ': 'Ω', 'Ώ': 'Ω',

    'Ῥ': 'Ρ', 'Ύ': 'Υ', 'Ϋ': 'Υ', "Ὑ": 'Υ', 'Ὕ': 'Υ',

    #Other characters to remove (the word itself is good)
    '\u0308': '', '.' : '', '\u0313': '', '?': '', '῀': '', '—': '',
}


for text in df['TRANSLIT']:
    if pd.isna(text):
        continue

    words = text.strip().split(" ")
    for word in words:
        if has_digit(word):
            print(word)
        if not ("'" in word or '`' in word or 'ʽ' in word or '~' in word or 'i' in word or 'v' in word or '\n' in word or "᾽" in word or "-" in word or '9' in word or '\xa0' in word): #don't consider malformed words
            normalized = ''
            for char in word:
                if char not in alphabet and char not in diacritic_to_base.keys():
                    print(word)
                    raise KeyError(f"Unexpected character: {char}")

                normalized += diacritic_to_base.get(char, char) 
            print(f"Original: {word} Normalized: {normalized}")
            words_set.add(normalized)

    

df = pd.DataFrame(sorted(words_set), columns=["word"]) 
df.to_csv("./homeric_greek_words_normalized.csv", index=True)
print("Words successfully normalized, now converting into latin text...")

latinize_greek("./homeric_greek_words_normalized.csv", "./latinized_homeric_greek_words.tsv")

