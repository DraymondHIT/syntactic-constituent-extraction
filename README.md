# syntactic-constituent-extraction

Extract (subject, verb, object) and (subject, modifiers) relations from a sentence using Spacy.

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
The fight scene finale between Sharon and the character played by Ali Larter, from the movie, won the 2010 MTV Movie Award for Best Fight.
```

Outputs includes the original sentence, a list of SVO tuples and a list of SM tuples.

```
The fight scene finale between Sharon and the character played by Ali Larter, from the movie, won the 2010 MTV Movie Award for Best Fight.
[('Ali Larter', 'play', 'the character'), ('The fight scene finale between Sharon and character played by Ali Larter , from the movie', 'won', 'the 2010 MTV Movie Award for Best Fight')]
[('Ali Larter', ''), ('The fight scene finale', 'between Sharon and character played by Ali Larter , from the movie')]
```

