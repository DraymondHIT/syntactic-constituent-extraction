import en_core_web_sm

nlp = en_core_web_sm.load()


def clean(tuples):
    cleaned_tuples = []
    for i in range(len(tuples)):
        if len(tuples[i]) == 2:
            cleaned_tuples.append(tuples[i])
            continue
        is_delete = False
        for j in range(len(tuples)):
            if i == j:
                continue
            if tuples[i][0] == tuples[j][0] and tuples[i][1] == tuples[j][1] and tuples[j][2].find(tuples[i][2]) != -1:
                is_delete = True
                break
        if not is_delete:
            cleaned_tuples.append(tuples[i])
    return cleaned_tuples


def generate(text, svos, sms, vms, ce):
    svos = clean(svos)

    # tokens = nlp(text)
    # for token in tokens.ents:
    #     print(token.text, token.label_)

