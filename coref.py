import spacy
import coreferee

nlp = spacy.load('en_core_web_sm')
nlp.add_pipe('coreferee')

doc = nlp('The cat loves the mouse that is delicious.')

doc._.coref_chains.print()
