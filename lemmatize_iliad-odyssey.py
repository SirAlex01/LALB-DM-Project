import spacy
import pandas as pd
from IPython.display import display

def lemmatize_iliad_and_odyssey(path, path2):

	df = pd.read_csv(path)
	df = df.drop("KEY", axis=1)
	display(df)
	
	#For df2 we duplicate column of greek text rename it and remove the others
	df2 = pd.read_csv(path2)
	df2 = df2.drop("book",  axis=1).drop("line start",axis=1).drop("line end", axis=1).drop("english text", axis=1)
	df2['TRANSLIT'] = df2.loc[:, 'greek text']
	df2['OGTXT'] = df2.loc[:, 'greek text']
	df2 = df2.drop('greek text', axis=1)
	display(df2)
	
	#Lemmatize df1
	for index, row in df.iterrows():
		original = row["TRANSLIT"]
		
		if index % 50 == 0:
			print(f"Original line {index} is: {original}")
			
		lemmatized = ""
		
		if isinstance(original, str) and not original.strip()=="":
			doc = nlp(original)
			lemmatized = ' '.join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])
			
		if index % 50 == 0:
			print(f"Lemmatized line {index} is: {lemmatized}")
			
		df.at[index, 'TRANSLIT'] = lemmatized

	#Lemmatize df2
	for index, row in df2.iterrows():
		original = row["TRANSLIT"]

		if index % 50 == 0:
			print(f"Original line {index} is: {original}")

		lemmatized = ''

		if isinstance(original, str) and not original.strip()=="":
			doc=nlp(original)
			lemmatized = ' '.join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])

		if index % 50 == 0:
			print(f"Lemmatized line {index} is: {lemmatized}")

		df2.at[index, 'TRANSLIT'] = lemmatized

	
	df = pd.concat([df, df2], ignore_index=True)
	return df


nlp = spacy.load("grc_odycy_joint_trf")
path1 = './ILIADKEY.csv'
path2 ='./gr_eng_text.csv'
if "transformer" not in nlp.pipe_names:
    transformer = nlp.add_pipe("transformer", first=True)
 
df = lemmatize_iliad_and_odyssey(path1, path2)   
df.to_csv('./lemmatized_homeric_greek. csv', index=False)
