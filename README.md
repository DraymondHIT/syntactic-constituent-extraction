# syntactic-constituent-extraction

Extract (subject, verb, object) , (subject, mod) and (verb, mod) relations from a sentence using Spacy.

## Installation

Uses Python 3.5+ and Spacy for its parser.

```bash
pip install -r requirements

# use spacy to download its small model
python -m spacy download en_core_web_sm
```

## Run the Demo

```
python demo.py
```

## Example

For the sentence below as an example.

```
For the third straight season, the number one seeds from both conferences met in the Super Bowl. 
```

Outputs includes the original sentence, a list of SVO tuples, a list of SM tuples and a list of VM tuples.

```
For the third straight season, the number one seeds from both conferences met in the Super Bowl. 
[('the number one seeds from both conferences', 'met')]
[('the number one seeds', 'from both conferences')]
[('met', 'in the Super Bowl')]
```

## Notes

- When there is no object, the program will return just SV parts.
- When there is no mod for subject or object, the program will return (subject, '') or (object, '').
