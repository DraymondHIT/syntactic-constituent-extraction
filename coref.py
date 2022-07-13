import spacy
import coreferee

nlp = spacy.load('en_core_web_sm')
nlp.add_pipe('coreferee')
