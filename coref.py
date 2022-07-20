import sys
sys.path.append('fast_coref/')
from fast_coref.inference.model_inference import Inference
import string


inference_model = Inference("./models", encoder_name="shtoshni/longformer_coreference_ontonotes")

PRON = {"he", "him", "she", "her", "it", "they", "them", "i", "me", "we", "us"}


class coref_chains:
    def __init__(self, text):
        self.output = inference_model.perform_coreference(text)
        self.clusters = []
        for cluster in self.output["subtoken_idx_clusters"]:
            temp = set()
            for element in cluster:
                possible_index = self.output["tokenized_doc"]["subtoken_map"][element[-1]]
                while self.output["tokenized_doc"]["orig_tokens"][possible_index] in string.punctuation:
                    possible_index -= 1
                temp.add(possible_index)
            self.clusters.append(temp)

    def resolve(self, item):
        for i in range(len(self.clusters)):
            if item.i in self.clusters[i]:
                for index in self.clusters[i]:
                    if self.output["tokenized_doc"]["orig_tokens"][index].lower() not in PRON:
                        return index
        return None
