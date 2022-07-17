from transformers import AutoTokenizer, AutoModelForTokenClassification
from causal_classifier import get_label
import torch

tokenizer = AutoTokenizer.from_pretrained("noahjadallah/cause-effect-detection")
model = AutoModelForTokenClassification.from_pretrained("noahjadallah/cause-effect-detection")
# label_list = ['O', 'B-CAUSE', 'I-CAUSE', 'B-EFFECT', 'I-EFFECT']


def cause_effect_detection(text):
    if get_label(text) == 0:
        return None

    tokens = tokenizer.tokenize(tokenizer.decode(tokenizer.encode(text)))
    inputs = tokenizer.encode(text, return_tensors="pt")

    outputs = model(inputs).logits
    predictions = torch.argmax(outputs, dim=2)

    cause_tokens = []
    effect_tokens = []
    for i in range(len(tokens)):
        if predictions[0].numpy()[i] in {1, 2}:
            cause_tokens.append(tokens[i])
        elif predictions[0].numpy()[i] in {3, 4}:
            effect_tokens.append(tokens[i])

    if len(cause_tokens) == 0 or len(effect_tokens) == 0:
        return None
    else:
        cause_text = tokenizer.convert_tokens_to_string(cause_tokens)
        effect_text = tokenizer.convert_tokens_to_string(effect_tokens)
        result = {"cause": cause_text, "effect": effect_text}

    return result

