# syntactic-constituent-extraction

- Extract (subject, verb, object) , (subject, mod) and (verb, mod) relations from a sentence using Spacy.
- Detect and extract (if exists) cause-and-effect relationship from a sentence using  [CiRA](https://github.com/fischJan/CiRA) and [Multilabel Models](https://zenodo.org/record/5550387#.YtQElnZBxPZ).

## Installation

Uses Python 3.5+ and Spacy for its parser.

```bash
pip install -r requirements

# use spacy to download its small model
python -m spacy download en_core_web_sm
```

## Parameters Download

For  [CiRA](https://github.com/fischJan/CiRA), the authors did not supply model parameters. Of course, you could train the model by yourself, but if you would like to run the following demo quickly, you can download parameters for [CiRA](https://github.com/fischJan/CiRA) by this [link](https://drive.google.com/file/d/1RSCnCMlgnP4z0cBsESILilhFZ1YQ0Az7/view?usp=sharing). After download parameters, you can put them under the `./models/` directory. For  [Multilabel Models](https://zenodo.org/record/5550387#.YtQElnZBxPZ), you can download parameters by run

```bash
gdown --id 1NizNkSdah8Jcs8wtDTD5dEnxUWrCP4Zi -O roberta_dropout_linear_layer_multilabel.ckpt
```

After that, you can also put the parameters under the same directory.

## Run the Demo

```
python demo.py
```

## Example

For the sentence below as an example.

```
If a user signs up, he will receive a confirmation email.
```

Outputs includes the original sentence, a list of SVO tuples, a list of SM tuples, a list of VM tuples and cause-and-effect relationship if it exists.

```
text: If a user signs up, he will receive a confirmation email.
SVO:  [('a user', 'receive', 'a confirmation email')]
SM:   [('a user', '')]
VM:   [('receive', '')]
CE:   {'cause': ['a user signs up'], 'effect': ['he will receive a confirmation email']}
```

## Notes

- When there is no object, the program will return just SV parts.
- When there is no mod for subject or object, the program will return (subject, '') or (object, '').
- When there is no cause-and-effect relationship in the sentence, the program will return None. Otherwise, a dictionary containing keys named `cause` and `effect` will be returned.

## TODO

- [ ] Realize batch processing

- [ ] Improve the accuracy of cause-and-effect relationship extraction
