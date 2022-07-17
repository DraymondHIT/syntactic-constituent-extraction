# syntactic-constituent-extraction

- Extract (subject, verb, object) , (subject, mod) and (verb, mod) relations from a sentence using Spacy.
- Detect and extract (if exists) cause-and-effect relationship from a sentence using  [CiRA](https://github.com/fischJan/CiRA) and [cause-effect-detection](https://huggingface.co/noahjadallah/cause-effect-detection).

## Installation

Uses Python 3.5+ and Spacy for its parser.

```bash
pip install -r requirements

# use spacy to download its small model
python -m spacy download en_core_web_sm
```

## Parameters Download

 [cause-effect-detection](https://huggingface.co/noahjadallah/cause-effect-detection) is a pretrained model, so there is no need to download parameters manually. However, for  [CiRA](https://github.com/fischJan/CiRA), the authors did not supply model parameters. Of course, you could train the model by yourself, but if you would like to run the following demo quickly, you can download parameters for [CiRA](https://github.com/fischJan/CiRA) by this [link](https://drive.google.com/file/d/1yNUSmFVjscanJ36dTz1NkOeV6huykfSM/view?usp=sharing). After download parameters, you had better to put it under the `./models/` directory.

## Run the Demo

```
python demo.py
```

## Example

For the sentence below as an example.

```
For the third straight season, the number one seeds from both conferences met in the Super Bowl. 
```

Outputs includes the original sentence, a list of SVO tuples, a list of SM tuples, a list of VM tuples and cause-and-effect relationship if it exists.

```
text: For the third straight season, the number one seeds from both conferences met in the Super Bowl. 
SVO:  [('the number one seeds from both conferences', 'met')]
SM:   [('the number one seeds', 'from both conferences')]
VM:   [('met', 'in the Super Bowl')]
CE:   None
```

## Notes

- When there is no object, the program will return just SV parts.
- When there is no mod for subject or object, the program will return (subject, '') or (object, '').
- When there is no cause-and-effect relationship in the sentence, the program will return None. Otherwise, a dictionary contains keys named `cause` and `effect` will be returned.

## TODO

- Realize batch processing
