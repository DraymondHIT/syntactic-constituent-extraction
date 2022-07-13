from extract import findSVOs, findSMs, findVMs, nlp, get_special_phrases
from coref import nlp as coref_model


class pipeline:
    def __init__(self, text):
        self.text = text
        special_phrases = get_special_phrases(text)
        if special_phrases != '':
            text = text.replace(special_phrases, '')
        token = nlp(text)
        self.doc = coref_model(text)
        self.svos = findSVOs(token, self.doc)
        self.sms = findSMs(token, self.doc)
        self.vms = findVMs(token)

    def __str__(self):
        return f"text: {self.text}\n" + f"SVO:  {self.svos}\n" + f"SM:   {self.sms}\n" + f"VM:   {self.vms}"
