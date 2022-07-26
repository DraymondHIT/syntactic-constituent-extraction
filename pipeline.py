from extract import findSVOs, findSMs, findVMs, nlp
from coref import coref_chains
from causal_extractor import cause_effect_extraction


class pipeline:
    def __init__(self, text):
        self.text = text
        tokens = nlp(text)
        self.doc = coref_chains(text)
        self.svos = findSVOs(tokens, self.doc)
        self.sms = findSMs(tokens, self.doc)
        self.vms = findVMs(tokens)
        self.ce = cause_effect_extraction(text)

    def __str__(self):
        return f"text: {self.text}\n" + f"SVO:  {self.svos}\n" + f"SM:   {self.sms}\n" + f"VM:   {self.vms}\n" + f"CE:   {self.ce}"
