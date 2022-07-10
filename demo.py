from extract import findSVOs, findSMs, nlp, get_special_phrases

with open("sample.txt", "r") as f:
    corpus = f.readlines()
f.close()

for index, text in enumerate(corpus):
    special_phrases = get_special_phrases(text)
    if special_phrases != '':
        text = text.replace(special_phrases, '')
    token = nlp(text)
    svos = findSVOs(token)
    sms = findSMs(token)
    print(f"========={index}=========")
    print(text)
    print(svos)
    print(sms)

