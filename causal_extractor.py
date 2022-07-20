from causal_classifier import get_label

import pytorch_lightning as pl
import torch
from transformers import RobertaModel, RobertaTokenizer, BatchEncoding
from transformers.modeling_outputs import TokenClassifierOutput
from torch import nn
from torch.nn import BCEWithLogitsLoss
import abc

# Configuration variables
CHECKPOINTS_PATH = '/github/syntactic-constituent-extraction/models/'
MODEL_NAME = 'roberta_dropout_linear_layer_multilabel'
USE_GPU = True
MODEL_PATH = CHECKPOINTS_PATH + MODEL_NAME + '.ckpt'


class CustomModel(pl.LightningModule):

    def __init__(self, hyperparams, labels, model_to_use):
        super().__init__()
        self.hyperparams = hyperparams
        self.labels = labels
        self.label2idx = {t: i for i, t in enumerate(labels)}
        self.define_model(model_to_use, len(labels))

    @abc.abstractmethod
    def define_model(self, model_to_use, num_labels):
        raise NotImplementedError

    @abc.abstractmethod
    def forward(self, input_ids, attention_mask, token_type_ids, targets):
        raise NotImplementedError

    @abc.abstractmethod
    def get_predictions_from_logits(self, logits):
        raise NotImplementedError


class MultiLabelRoBERTaCustomModel(CustomModel):

    def get_predictions_from_logits(self, logits):
        sigmoid_outputs = torch.sigmoid(logits)
        predictions = (sigmoid_outputs >= 0.5).int()

        return predictions

    def define_model(self, model_to_use, num_labels):
        self.num_labels = num_labels
        self.bert = RobertaModel.from_pretrained(model_to_use)
        self.dropout = nn.Dropout(self.hyperparams["dropout"])
        self.classifier = nn.Linear(self.bert.config.hidden_size, self.num_labels)

    def forward(self, input_ids, attention_mask, token_type_ids, labels):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        sequence_output = outputs[0]

        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)

        loss = None
        if labels is not None:
            loss_fct = BCEWithLogitsLoss()
            # Only keep active parts of the loss
            if attention_mask is not None:
                active_logits = logits[attention_mask == 1]

                active_labels = labels[attention_mask == 1].type_as(active_logits)

                loss = loss_fct(active_logits, active_labels)
            else:
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

        return TokenClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )


# Dataset configuration variables
LABEL_IDS = [
    'NOT_RELEVANT',
    'CAUSE_1',
    'CAUSE_2',
    'CAUSE_3',
    # 'CAUSE_4',
    'EFFECT_1',
    'EFFECT_2',
    'EFFECT_3',
    # 'EFFECT_4',
    'AND',
    'OR',
    'VARIABLE',
    'CONDITION',
    # 'KEYWORD',
    'NEGATION',
]

MAX_LEN = 80

MODEL_NAME = 'roberta_dropout_linear_layer_multilabel'
DROPOUT = 0.13780087432114646

############## Parameters related to the BERT model type ###################
MODEL_TO_USE = 'roberta-base'
TOKENIZER = RobertaTokenizer.from_pretrained(MODEL_TO_USE)
MODEL_CLASS = MultiLabelRoBERTaCustomModel
###########################################################################


MODEL_PARAMS = {'dropout': DROPOUT}

model = MODEL_CLASS.load_from_checkpoint(hyperparams=MODEL_PARAMS,
                                         labels=LABEL_IDS,
                                         model_to_use=MODEL_TO_USE,
                                         checkpoint_path=CHECKPOINTS_PATH + MODEL_NAME + '.ckpt')

if USE_GPU:
    model.cuda()

model.eval()


def convert_tokens_to_string(tokens):
    output = ''
    for token in tokens:
        if token.startswith('Ġ'):
            output += ' ' + token.replace('Ġ', '')
        else:
            output += token
    return output.strip()


def cause_effect_extraction(text):
    if get_label(text) == 0:
        return None

    tokens = TOKENIZER.tokenize(text)
    inputs = TOKENIZER(text)

    input_ids = torch.tensor([inputs["input_ids"]], dtype=torch.long)
    attention_mask = torch.tensor([inputs["attention_mask"]], dtype=torch.long)

    if USE_GPU:
        input_ids = input_ids.cuda()
        attention_mask = attention_mask.cuda()

    outputs = model(input_ids=input_ids,
                    attention_mask=attention_mask,
                    token_type_ids=None,
                    labels=None
                    )

    logits = outputs.logits
    predictions = model.get_predictions_from_logits(logits).cpu()

    cause_tokens = []
    effect_tokens = []
    cause_index = [False, False, False]
    effect_index = [False, False, False]
    for token_prediction_idx, token_prediction in enumerate(predictions[0][1:-1]):
        token_predicted_labels = []
        token = tokens[token_prediction_idx]
        for label_prediction_idx, label_prediction in enumerate(token_prediction):
            if label_prediction == 1:
                token_predicted_labels.append(LABEL_IDS[label_prediction_idx])
        # token = token.replace("Ġ", "")
        if token in TOKENIZER.all_special_tokens or len(token_predicted_labels) == 0:
            continue
        index = token_predicted_labels[0][-1]
        if index not in {'1', '2', '3'}:
            continue
        index = eval(index)
        if token_predicted_labels[0].startswith("CAUSE"):
            if not cause_index[index-1]:
                cause_tokens.append([token])
                cause_index[index-1] = True
            else:
                cause_tokens[-1].append(token)
        elif token_predicted_labels[0].startswith("EFFECT"):
            if not effect_index[index-1]:
                effect_tokens.append([token])
                effect_index[index-1] = True
            else:
                effect_tokens[-1].append(token)

    if len(cause_tokens) == 0 or len(effect_tokens) == 0:
        return None
    cause_tokens = [convert_tokens_to_string(tokens) for tokens in cause_tokens]
    effect_tokens = [convert_tokens_to_string(tokens) for tokens in effect_tokens]

    return {"cause": cause_tokens, "effect": effect_tokens}


cause_effect_extraction("Chloroplasts are highly dynamic, they circulate and move around within plant cells, and occasionally pinch in two to reproduce.")
