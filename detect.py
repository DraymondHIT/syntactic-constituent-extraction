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
    cause_index = -1
    effect_index = -1
    for i in range(len(tokens)):
        if predictions[0].numpy()[i] == 1:
            cause_tokens.append([tokens[i]])
            cause_index = i
        elif predictions[0].numpy()[i] == 2:
            if len(cause_tokens) == 0 or cause_index + 1 != i:
                continue
            cause_tokens[-1].append(tokens[i])
            cause_index = i
        elif predictions[0].numpy()[i] == 3:
            effect_tokens.append([tokens[i]])
            effect_index = i
        elif predictions[0].numpy()[i] == 4:
            if len(effect_tokens) == 0 or effect_index + 1 != i:
                continue
            effect_tokens[-1].append(tokens[i])
            effect_index = i

    if len(cause_tokens) == 0 or len(effect_tokens) == 0:
        return None
    else:
        cause_text = [tokenizer.convert_tokens_to_string(tokens) for tokens in cause_tokens]
        effect_text = [tokenizer.convert_tokens_to_string(tokens) for tokens in effect_tokens]
        result = {"cause": cause_text, "effect": effect_text}

    return result
