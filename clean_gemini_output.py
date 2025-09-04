import csv
import unicodedata
import re

# Allowed characters
allowed_chars = set("fhαβγδεζηθικλμνξοπρςστυφχψω|")

# Comprehensive correction dictionary
correction_dict = {
    # Greek uppercase to lowercase
    'Α': 'α', 'Β': 'β', 'Γ': 'γ', 'Δ': 'δ', 'Ε': 'ε', 'Ζ': 'ζ', 'Η': 'η', 'Θ': 'θ',
    'Ι': 'ι', 'Κ': 'κ', 'Λ': 'λ', 'Μ': 'μ', 'Ν': 'ν', 'Ξ': 'ξ', 'Ο': 'ο', 'Π': 'π',
    'Ρ': 'ρ', 'Σ': 'σ', 'Τ': 'τ', 'Υ': 'υ', 'Φ': 'φ', 'Χ': 'χ', 'Ψ': 'ψ', 'Ω': 'ω',
    
    # Common Latin uppercase that might appear
    'A': 'α', 'B': 'β', 'G': 'γ', 'D': 'δ', 'E': 'ε', 'Z': 'ζ', 'H': 'η', 'Q': 'θ',
    'I': 'ι', 'K': 'κ', 'L': 'λ', 'M': 'μ', 'N': 'ν', 'X': 'ξ', 'O': 'ο', 'P': 'π',
    'R': 'ρ', 'S': 'σ', 'T': 'τ', 'U': 'υ', 'F': 'φ', 'C': 'χ', 'Y': 'ψ', 'W': 'ω',
    
    # Accented/diacritic vowels to plain vowels
    'ά': 'α', 'ὰ': 'α', 'ᾶ': 'α', 'ἀ': 'α', 'ἁ': 'α', 'ἄ': 'α', 'ἅ': 'α', 'ἂ': 'α', 'ἃ': 'α',
    'ἆ': 'α', 'ἇ': 'α', 'ᾳ': 'α', 'ᾴ': 'α', 'ᾲ': 'α', 'ᾷ': 'α', 'ᾀ': 'α', 'ᾁ': 'α', 'ᾄ': 'α',
    'ᾅ': 'α', 'ᾂ': 'α', 'ᾃ': 'α', 'ᾆ': 'α', 'ᾇ': 'α',
    
    'έ': 'ε', 'ὲ': 'ε', 'ἐ': 'ε', 'ἑ': 'ε', 'ἔ': 'ε', 'ἕ': 'ε', 'ἒ': 'ε', 'ἓ': 'ε',
    
    'ή': 'η', 'ὴ': 'η', 'ῆ': 'η', 'ἠ': 'η', 'ἡ': 'η', 'ἤ': 'η', 'ἥ': 'η', 'ἢ': 'η', 'ἣ': 'η',
    'ἦ': 'η', 'ἧ': 'η', 'ῃ': 'η', 'ῄ': 'η', 'ῂ': 'η', 'ῇ': 'η', 'ᾐ': 'η', 'ᾑ': 'η', 'ᾔ': 'η',
    'ᾕ': 'η', 'ᾒ': 'η', 'ᾓ': 'η', 'ᾖ': 'η', 'ᾗ': 'η',
    
    'ί': 'ι', 'ὶ': 'ι', 'ῖ': 'ι', 'ἰ': 'ι', 'ἱ': 'ι', 'ἴ': 'ι', 'ἵ': 'ι', 'ἲ': 'ι', 'ἳ': 'ι',
    'ἶ': 'ι', 'ἷ': 'ι', 'ϊ': 'ι', 'ΐ': 'ι', 'ῒ': 'ι', 'ῗ': 'ι',
    
    'ό': 'ο', 'ὸ': 'ο', 'ὀ': 'ο', 'ὁ': 'ο', 'ὄ': 'ο', 'ὅ': 'ο', 'ὂ': 'ο', 'ὃ': 'ο',
    
    'ύ': 'υ', 'ὺ': 'υ', 'ῦ': 'υ', 'ὐ': 'υ', 'ὑ': 'υ', 'ὔ': 'υ', 'ὕ': 'υ', 'ὒ': 'υ', 'ὓ': 'υ',
    'ὖ': 'υ', 'ὗ': 'υ', 'ϋ': 'υ', 'ΰ': 'υ', 'ῢ': 'υ', 'ῧ': 'υ', 'ῠ': 'υ', 'ῡ': 'υ',
    
    'ώ': 'ω', 'ὼ': 'ω', 'ῶ': 'ω', 'ὠ': 'ω', 'ὡ': 'ω', 'ὤ': 'ω', 'ὥ': 'ω', 'ὢ': 'ω', 'ὣ': 'ω',
    'ὦ': 'ω', 'ὧ': 'ω', 'ῳ': 'ω', 'ῴ': 'ω', 'ῲ': 'ω', 'ῷ': 'ω', 'ᾠ': 'ω', 'ᾡ': 'ω', 'ᾤ': 'ω',
    'ᾥ': 'ω', 'ᾢ': 'ω', 'ᾣ': 'ω', 'ᾦ': 'ω', 'ᾧ': 'ω',
    
    # Rough breathing marks on consonants
    'ῥ': 'ρ', 'Ῥ': 'ρ',
    
    # Remove spaces, hyphens, commas
    ' ': '', '-': '', ',': '',
    
    # Latin characters that might appear
    'i': 'ι', 'a': 'α', 'o': 'ο'
}

def normalize_greek_word(word, linear_b_key=""):
    """Apply all normalizations to a Greek word"""
    # First apply character-by-character corrections
    corrected = ''.join(correction_dict.get(char, char) for char in word)
    
    # Remove any remaining diacritics using Unicode normalization
    normalized = unicodedata.normalize('NFD', corrected)
    without_diacritics = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    
    # Replace trailing "qe" with "τε" 
    if without_diacritics.endswith('qe'):
        without_diacritics = without_diacritics[:-2] + 'τε'
    # Only replace κε/γε with τε if the original Linear B key ended with "-qe"
    elif linear_b_key.endswith('-qe'):
        if without_diacritics.endswith('κε'):
            without_diacritics = without_diacritics[:-2] + 'τε'
        elif without_diacritics.endswith('γε'):
            without_diacritics = without_diacritics[:-2] + 'τε'
    
    # Replace middle ς with σ (but keep final ς)
    if len(without_diacritics) > 1:
        # Replace all ς with σ first, then put back final ς if it was there
        temp = without_diacritics.replace('ς', 'σ')
        if without_diacritics.endswith('ς'):
            temp = temp[:-1] + 'ς'
        without_diacritics = temp
    
    return without_diacritics

def check_greek_characters(path, delimiter="\t"):
    corrections_made = []
    words_with_bad_chars = 0
    still_problematic = 0
    
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if "gemini" not in reader.fieldnames:
            raise ValueError("File must have a 'gemini' column")

        for row in reader:
            gemini_field = row["gemini"]
            linear_b_key = row[reader.fieldnames[0]]  # First column is the Linear B key
            
            # Check if original field has bad characters
            original_bad_chars = {ch for ch in gemini_field if ch not in allowed_chars}
            if original_bad_chars:
                words_with_bad_chars += 1
            
            # Split by | to handle multiple words
            words = gemini_field.split('|')
            corrected_words = []
            
            for word in words:
                original_word = word
                corrected_word = normalize_greek_word(word, linear_b_key)
                corrected_words.append(corrected_word)
                
                # Check if correction was needed
                if original_word != corrected_word:
                    corrections_made.append((linear_b_key, original_word, corrected_word))
            
            # Check for any remaining bad characters after correction
            corrected_field = '|'.join(corrected_words)
            bad_chars = {ch for ch in corrected_field if ch not in allowed_chars}
            if bad_chars:
                still_problematic += 1
                print(f"⚠️ Still problematic in key {linear_b_key}: {''.join(sorted(bad_chars))} {corrected_field}")
    
    # Show statistics
    print(f"\n📊 STATISTICS:")
    print(f"Words with bad characters needing correction: {words_with_bad_chars}")
    print(f"Total corrections made: {len(corrections_made)}")
    print(f"Words still problematic after correction: {still_problematic}")
    
    # Compliance check
    if still_problematic == 0:
        print("✅ ALL WORDS NOW COMPLY WITH THE ALLOWED CHARACTER SET!")
    else:
        print(f"❌ {still_problematic} words still have compliance issues")
    
    # Show all corrections made
    if corrections_made:
        print("\n=== CORRECTIONS MADE ===")
        for key, before, after in corrections_made:
            if before != after:
                print(f"Key {key}: '{before}' → '{after}'")
    else:
        print("\n✅ No corrections needed!")

if __name__ == "__main__":
    check_greek_characters("cognates_translation.cog")
