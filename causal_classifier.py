from transformers import BertModel, BertTokenizer
import torch
from torch import nn

PRE_TRAINED_MODEL_NAME = "bert-base-cased"


class CausalClassifier(nn.Module):

    def __init__(self, n_classes):
        super(CausalClassifier, self).__init__()
        self.bert = BertModel.from_pretrained(PRE_TRAINED_MODEL_NAME)
        self.drop = nn.Dropout(p=0.3)
        self.out = nn.Linear(self.bert.config.hidden_size, n_classes)

    def forward(self, inputs):
        _, pooled_output = self.bert(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            return_dict=False
        )
        output = self.drop(pooled_output)
        return self.out(output)


def get_label(text):
    tokenizer = BertTokenizer.from_pretrained(PRE_TRAINED_MODEL_NAME)

    model = CausalClassifier(2)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.load_state_dict(torch.load("./models/causal_classifier.bin"))
    model.eval()

    inputs = tokenizer(text, return_tensors="pt")
    inputs = inputs.to(device)
    outputs = model(inputs)
    _, preds = torch.max(outputs, dim=1)
    label = preds.item()

    return label

