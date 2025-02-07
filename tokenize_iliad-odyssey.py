from greek_accentuation.syllabify import syllabify, display_word
#from cltk.stem.lemma import LemmaReplacer, BackoffGreekLemmatizer
#from cltk.tokenize.greek.sentence import SentenceTokenizer
#from cltk.tokenize.sentence import TokenizeSentence
from nltk.tokenize.punkt import PunktLanguageVars
#from cltk.stop.greek.stops import STOPS_LIST
from cltk.phonology.greek.transcription import Transcriber
import pandas as pd
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
	
	dictionary = ()
	
	res = pd.DataFrame(columns=['word', 'transliteration'])
	
	#Lemmatize df1
	for index, row in df.iterrows():
		original = row["TRANSLIT"]
		
		if isinstance(original, str) and not original.strip()=="":
			doc = nlp(original)
			words = [token.text for token in doc if not token.is_punct]
			for word in words:
				if  word not in dictionary:
					dictionary.add(word)
					transcribed_word = transcriber.transcribe(word)
					res.loc[len(res)] = [word, transcribed_word]
			display(res)

	#Lemmatize df2
	for index, row in df2.iterrows():
		original = row["TRANSLIT"]

		if isinstance(original, str) and not original.strip()=="":
			doc=nlp(original)
			words = [token.text for token in doc if not token.is_punct]
			for word in words:
				if  word not in dictionary:
					dictionary.add(word)
					transcribed_word = transcriber.transcribe(word)
					res.loc[len(res)] = [word, transcribed_word]


	return res


path1 = './ILIADKEY.csv'
path2 ='./gr_eng_text.csv'

