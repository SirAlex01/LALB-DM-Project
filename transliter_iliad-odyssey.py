from greek_accentuation.syllabify import syllabify, display_word
#from cltk.stem.lemma import LemmaReplacer, BackoffGreekLemmatizer
#from cltk.tokenize.greek.sentence import SentenceTokenizer
#from cltk.tokenize.sentence import TokenizeSentence
from nltk.tokenize.punkt import PunktLanguageVars
#from cltk.stop.greek.stops import STOPS_LIST
from cltk.phonology.grc.transcription import Transcriber
import pandas as pd
import unicodedata
import spacy
from IPython.display import display


def transliteration_iliad_and_odyssey(path, path2):

	#lemmatizer = BackoffGreekLemmatizer()
	#sent_tokenizer = SentenceTokenizer()
	#p = PunktLanguageVars()
	transcriber = Transcriber(dialect="Attic", reconstruction="Probert")
	
	df = pd.read_csv(path)
	df = df.drop("KEY", axis=1)
	
	#For df2 we duplicate column of greek text rename it and remove the others
	df2 = pd.read_csv(path2)
	df2 = df2.drop("book",  axis=1).drop("line start",axis=1).drop("line end", axis=1).drop("english text", axis=1)
	df2['TRANSLIT'] = df2.loc[:, 'greek text']
	df2['OGTXT'] = df2.loc[:, 'greek text']
	df2 = df2.drop('greek text', axis=1)
	
	dictionary = set()
	
	res = pd.DataFrame(columns=['word', 'transliteration'])
	
	#Transcribe df1 (ILIAD)
	for index, row in df.iterrows():
		original = row["TRANSLIT"]
		
		if isinstance(original, str) and not original.strip()=="":
			doc = nlp(original)
			words = [token.text for token in doc if not token.is_punct]

			for word in words:
				if  word not in dictionary:
					dictionary.add(word)
					#word = unicodedata.normalize("NFC", word) #need to remove diacritics (dieresis) otherwise it gives error
					#word = elision_dict.get(word, word) #we need to remove contracted forms otherwise it again fails the transcription
					transcribed_word = transcriber.transcribe(word)
					print(word, transcribed_word)
					res.loc[len(res)] = [word, transcribed_word]

	
	#Transcribe df2 (ODYSSEY)
	for index, row in df2.iterrows():
		original = row["TRANSLIT"]
		
		if isinstance(original, str) and not original.strip()=="":
			doc = nlp(original)
			words = [token.text for token in doc if not token.is_punct]

			for word in words:
				if  word not in dictionary:
					dictionary.add(word)
					transcribed_word = transcriber.transcribe(word)
					print(word, transcribed_word)
					res.loc[len(res)] = [word, transcribed_word]

	return res

nlp = spacy.load("grc_odycy_joint_trf")
path1 = './ILIADKEY.csv'
path2 ='./gr_eng_text.csv'

elision_dict = { #need to remove elisions to be processed correctly
    "δ'": "δέ",
    "θ'": "τε",
    "γ'": "γε",
    "ἀπ'": "ἀπό",
    "καθ'": "κατά"
}

res = transliteration_iliad_and_odyssey(path1, path2)
res.to_csv('./transliteration_homeric_greek. csv', index=False)
