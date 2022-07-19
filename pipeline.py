from extract import findSVOs, findSMs, findVMs, nlp
from coref import nlp as coref_model
from detect import cause_effect_detection


class pipeline:
    def __init__(self, text):
        self.text = text
        token = nlp(text)
        self.doc = coref_model(text)
        self.svos = findSVOs(token, self.doc)
        self.sms = findSMs(token, self.doc)
        self.vms = findVMs(token)
        self.ce = cause_effect_detection(text)

    def __str__(self):
        return f"text: {self.text}\n" + f"SVO:  {self.svos}\n" + f"SM:   {self.sms}\n" + f"VM:   {self.vms}\n" + f"CE:   {self.ce}"
