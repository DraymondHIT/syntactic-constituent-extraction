import en_core_web_sm
from collections.abc import Iterable

# use spacy small model
nlp = en_core_web_sm.load()

with open("pmi-masking/pmi-wiki-bc.txt", "r", encoding='utf-8') as f:
    collocation = f.read().splitlines()

# dependency markers for subjects
SUBJECTS = {"nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"}
# dependency markers for objects
OBJECTS = {"dobj", "dative", "attr", "oprd", "acomp", "pcomp", "pobj"}
# POS tags that will break adjoining items
BREAKER_POS = {"VERB"}
# words that are negations
NEGATIONS = {"no", "not", "n't", "never", "none"}

# AUX
AUX = {"be", "is", "was", "are", "were"}
# relative word
RELATIVE_WORDS = {"which", "that"}
# conjunction
CONJUNCTIONS = {"that", "if", "while"}
# location preposition word
LOCATION_PREPOSITIONS = {"in", "on", "at", "above", "below"}
# special verb dependencies
SPECIAL_VERB_DEPS = {"amod", "acl", "pcomp", "ccomp"}


# does dependency set contain any coordinating conjunctions?
def contains_conj(depSet):
    return "and" in depSet or "or" in depSet or "nor" in depSet or \
           "but" in depSet or "yet" in depSet or "so" in depSet or "for" in depSet


# get subs joined by conjunctions
def _get_subs_from_conjunctions(subs):
    more_subs = []
    for sub in subs:
        # rights is a generator
        rights = list(sub.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if contains_conj(rightDeps):
            more_subs.extend([tok for tok in rights if tok.dep_ in SUBJECTS or tok.pos_ == "NOUN"])
            if len(more_subs) > 0:
                more_subs.extend(_get_subs_from_conjunctions(more_subs))
    return more_subs


# get objects joined by conjunctions
def _get_objs_from_conjunctions(objs):
    more_objs = []
    for obj in objs:
        # rights is a generator
        rights = list(obj.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if contains_conj(rightDeps):
            more_objs.extend([tok for tok in rights if tok.dep_ in OBJECTS or tok.pos_ == "NOUN"])
            if len(more_objs) > 0:
                more_objs.extend(_get_objs_from_conjunctions(more_objs))
    return more_objs


# find sub dependencies
def _find_subs(toks):
    if type(toks).__name__ == "list":
        tok = get_center_verb(toks)
        head = tok.head
    else:
        head = toks.head
    while head.pos_ != "VERB" and head.pos_ != "NOUN" and head.head != head:
        head = head.head
    if head.pos_ == "VERB" or head.pos_ == "AUX":
        subs = [tok for tok in head.lefts if tok.dep_ in SUBJECTS]
        if len(subs) > 0:
            # verb_negated = _is_negated(head) or _is_negated(tok)
            verb_negated = False
            subs.extend(_get_subs_from_conjunctions(subs))
            return subs, verb_negated
        elif head.head != head:
            return _find_subs(head)
    elif head.pos_ == "NOUN":
        # return [head], _is_negated(tok)
        return [head], False
    return [], False


# is the tok set's left or right negated?
def _is_negated(toks):
    parts = []
    for tok in toks:
        parts.extend(list(tok.lefts) + list(tok.rights))
    for dep in parts:
        if dep.lower_ in NEGATIONS:
            return True
    return False


# get all the verbs on tokens with negation marker
def _find_svs(tokens):
    svs = []
    verbs = [tok for tok in tokens if tok.pos_ == "VERB"]
    for v in verbs:
        subs, verbNegated = _get_all_subs(v)
        if len(subs) > 0:
            for sub in subs:
                svs.append((sub.orth_, "!" + v.orth_ if verbNegated else v.orth_))
    return svs


# get objects from the dependencies using the attribute dependency
def _get_objs_from_attrs(deps, is_pas):
    for dep in deps:
        if dep.pos_ == "NOUN" and dep.dep_ == "attr":
            verbs = [tok for tok in dep.rights if tok.pos_ == "VERB"]
            if len(verbs) > 0:
                for v in verbs:
                    rights = list(v.rights)
                    objs = [tok for tok in rights if tok.dep_ in OBJECTS]
                    objs.extend(_get_objs_from_prepositions(rights, is_pas))
                    if len(objs) > 0:
                        return v, objs
    return None, None


# xcomp; open complement - verb has no suject
def _get_obj_from_xcomp(deps, is_pas):
    # for dep in deps:
    #     if dep.pos_ == "VERB" and dep.dep_ == "xcomp":
    #         v = dep
    #         rights = list(v.rights)
    #         objs = [tok for tok in rights if tok.dep_ in OBJECTS]
    #         objs.extend(_get_objs_from_prepositions(rights, is_pas))
    #         if len(objs) > 0:
    #             return v, objs
    return None, None


# get all functional subjects adjacent to the verb passed in
def _get_all_subs(v_list):
    # verb_negated = _is_negated(v_list)
    verb_negated = False
    subs = [tok for v in v_list for tok in v.lefts if tok.dep_ in SUBJECTS and tok.pos_ != "DET"]
    if len(subs) > 0:
        subs.extend(_get_subs_from_conjunctions(subs))
    else:
        foundSubs, verb_negated = _find_subs(v_list)
        subs.extend(foundSubs)
    return subs, verb_negated


# find the main verb - or any aux verb if we can't find it
def _find_verbs(tokens):
    verbs = [tok for tok in tokens if _is_non_aux_verb(tok)]
    if len(verbs) == 0:
        verbs = [tok for tok in tokens if _is_verb(tok)]
    return verbs


# is the token a verb?  (excluding auxiliary verbs)
def _is_non_aux_verb(tok):
    return tok.pos_ == "VERB" and (tok.dep_ not in SPECIAL_VERB_DEPS and tok.dep_ != "advcl") or \
           tok.pos_ == "AUX" and (tok.dep_ != "aux" and tok.dep_ != "auxpass")


# is the token a verb?  (excluding auxiliary verbs)
def _is_verb(tok):
    return tok.pos_ == "VERB" or tok.pos_ == "AUX"


# return the verb to the right of this verb in a CCONJ relationship if applicable
# returns a tuple, first part True|False and second part the modified verb if True
def _right_of_verb_is_conj_verb(v_list):
    # rights is a generator
    rights = []
    for v in v_list:
        rights.extend(list(v.rights))

    # VERB CCONJ VERB (e.g. he beat and hurt me)
    if len(rights) > 1 and rights[0].pos_ == 'CCONJ':
        for tok in rights[1:]:
            if _is_non_aux_verb(tok):
                return True, expand_verb(tok)

    return False, v_list


# get all objects for an active/passive sentence
def _get_all_objs(v_list, visited, is_pas):
    # rights is a generator
    rights = []
    for v in v_list:
        rights.extend(list(v.rights))

    objs = [tok for tok in rights if tok.i not in visited and (tok.dep_ in OBJECTS)]

    # potentialNewVerb, potentialNewObjs = _get_objs_from_attrs(rights)
    # if potentialNewVerb is not None and potentialNewObjs is not None and len(potentialNewObjs) > 0:
    #    objs.extend(potentialNewObjs)
    #    v = potentialNewVerb

    # potential_new_verb, potential_new_objs = _get_obj_from_xcomp(rights, is_pas)
    # if potential_new_verb is not None and potential_new_objs is not None and len(potential_new_objs) > 0:
    #     objs.extend(potential_new_objs)
    #     v = potential_new_verb
    if len(objs) > 0:
        objs.extend(_get_objs_from_conjunctions(objs))
    return v_list, objs


# return all passive verbs
def _get_passive_verbs(tokens):
    passive_verbs = []
    for tok in tokens:
        # if tok.dep_ == "acl" or tok.dep_ == "advcl":
        #     passive_verbs.append(tok)
        if tok.dep_ == "auxpass":
            passive_verbs.append(tok.head)
        for item in tok.rights:
            if item.dep_ == "agent":
                passive_verbs.append(tok)
                break

    return passive_verbs


# resolve a 'that' where/if appropriate
def _get_that_resolution(toks):
    for tok in toks:
        if 'that' in [t.orth_ for t in tok.lefts]:
            return tok.head
    return None


# simple stemmer using lemmas
def _get_lemma(word: str):
    tokens = nlp(word)
    if len(tokens) == 1:
        return tokens[0].lemma_
    return word


# print information for displaying all kinds of things of the parse tree
def printDeps(toks):
    for tok in toks:
        print(tok.orth_, tok.dep_, tok.pos_, tok.head.orth_, [t.orth_ for t in tok.lefts],
              [t.orth_ for t in tok.rights])


# expand an obj / subj np using its chunk
def expand(item, tokens, visited, isfirst=False):
    # if item.lower_ == 'that':
    #     temp_item = _get_that_resolution(tokens)
    #     if temp_item is not None:
    #         item = temp_item
    if isfirst and item.i in visited:
        return []

    parts = []

    if hasattr(item, 'lefts'):
        for part in item.lefts:
            if part.pos_ in BREAKER_POS and part.dep_ not in SPECIAL_VERB_DEPS or part.i in visited:
                break
            if not part.lower_ in NEGATIONS:
                if hasattr(part, 'lefts'):
                    for item2 in part.lefts:
                        if item2.i not in visited:
                            visited.add(item2.i)
                            parts.extend(expand(item2, tokens, visited))
                parts.append(part)
                if hasattr(part, 'rights'):
                    for item2 in part.rights:
                        if item2.i not in visited:
                            visited.add(item2.i)
                            parts.extend(expand(item2, tokens, visited))

    parts.append(item)

    if hasattr(item, 'rights'):
        for part in item.rights:
            if part.pos_ in BREAKER_POS and part.dep_ not in SPECIAL_VERB_DEPS or part.i in visited:
                break
            if not part.lower_ in NEGATIONS:
                if hasattr(part, 'lefts'):
                    for item2 in part.lefts:
                        if item2.i not in visited:
                            visited.add(item2.i)
                            parts.extend(expand(item2, tokens, visited))
                parts.append(part)
                if hasattr(part, 'rights'):
                    for item2 in part.rights:
                        if item2.i not in visited:
                            visited.add(item2.i)
                            parts.extend(expand(item2, tokens, visited))

    return parts


def multi_expand(items, tokens, visited, isfirst=False):
    parts = []
    for item in list(items):
        parts.extend(expand(item, tokens, visited, isfirst))

    return parts


# convert a list of tokens to a string
def to_str(tokens):
    if isinstance(tokens, Iterable):
        return ' '.join([item.text for item in tokens])
    else:
        return ''


def _get_verb_advmod(item):
    if len(list(item.rights)) == 0 or (list(item.rights)[0].dep_ != "advmod" and list(item.rights)[0].dep_ != "prt"):
        return ''
    else:
        return ' ' + list(item.rights)[0].lemma_


def _process_relative_word_and_pron(items, tokens, visited, coref=None):
    objs = []
    for item in items:
        if item.lemma_ in RELATIVE_WORDS and (
                item.dep_ == "nsubjpass" or item.dep_ == "nsubj") and item.head.dep_ == "relcl":
            visited.add(item.i)
            visited.add(item.head.i)
            objs.append(item.head.head)
        elif coref is not None and item.pos_ == "PRON":
            result = coref.resolve(item)
            if result is not None:
                objs.append(list(tokens)[result])
            else:
                objs.append(item)
        else:
            objs.append(item)
    return objs, visited


def get_center_verb(v_list):
    i_list = [v.i for v in v_list]
    for v in v_list:
        if v.head.i not in i_list:
            return v


def expand_verb(verb):

    if len(list(verb.lefts)) == 0:
        lefts = ['']
    elif list(verb.lefts)[-1].pos_ not in {"NOUN", "PROPN", "PRON", "DET"}:
        lefts = ['', list(verb.lefts)[-1].text.lower()]
    else:
        lefts = ['']

    if len(list(verb.rights)) == 0 or verb.pos_ == "AUX":
        rights = ['']
    elif len(list(verb.rights)) == 1:
        rights = ['', list(verb.rights)[0].text.lower()]
    else:
        rights = ['', list(verb.rights)[0].text.lower(),
                  list(verb.rights)[0].text.lower() + ' ' + list(verb.rights)[1].text.lower()]

    for left in lefts[::-1]:
        for right in rights[::-1]:
            if (left + ' ' + verb.text.lower() + ' ' + right).strip() in collocation:
                expanded = []
                if left != '':
                    expanded.append(list(verb.lefts)[-1])
                expanded.append(verb)
                if right != '':
                    if ' ' in right:
                        expanded.append(list(verb.rights)[0])
                        expanded.append(list(verb.rights)[1])
                    else:
                        expanded.append(list(verb.rights)[0])
                return expanded

    if len(list(verb.lefts)) > 1 and list(verb.lefts)[-1].dep_ == "neg":
        return [list(verb.lefts)[-1], verb]

    return [verb]


# find verbs and their subjects / objects to create SVOs, detect passive/active sentences
def findSVOs(tokens, coref=None):
    svos = []
    # passive_verbs = _get_passive_verbs(tokens)
    verbs = _find_verbs(tokens)
    for v in verbs:
        expanded_verb = expand_verb(v)
        visited = set()
        for verb in expanded_verb:
            visited.add(verb.i)
        subs, verbNegated = _get_all_subs(expanded_verb)
        # hopefully there are subs, if not, don't examine this verb any longer
        if len(subs) > 0:
            isConjVerb, conjV = _right_of_verb_is_conj_verb(expanded_verb)
            if isConjVerb:
                # is_pas = conjV in passive_verbs
                v2, objs = _get_all_objs(conjV, visited, False)
                for sub in subs:
                    sub, visited = _process_relative_word_and_pron([sub], list(tokens), visited, coref)
                    sub = sub[0]
                    if len(objs) > 0:
                        # objNegated = _is_negated(obj)
                        objs, visited = _process_relative_word_and_pron(objs, list(tokens), visited, coref)

                        svos.append((to_str(get_subject(sub, tokens, visited)),
                                     "!" + to_str(expanded_verb) if verbNegated else to_str(
                                         expanded_verb),
                                     to_str(multi_expand(objs, tokens, visited, True))))
                        svos.append((to_str(get_subject(sub, tokens, visited)),
                                     "!" + to_str(v2) if verbNegated else to_str(v2),
                                     to_str(multi_expand(objs, tokens, visited, True))))
                    else:
                        svos.append((to_str(get_subject(sub, tokens, visited)),
                                     "!" + to_str(expanded_verb) if verbNegated else to_str(expanded_verb),))
            else:
                # is_pas = v in passive_verbs
                v, objs = _get_all_objs(expanded_verb, visited, False)
                for sub in subs:
                    sub, visited = _process_relative_word_and_pron([sub], list(tokens), visited, coref)
                    sub = sub[0]
                    if len(objs) > 0:
                        # objNegated = _is_negated(obj)
                        objs, visited = _process_relative_word_and_pron(objs, list(tokens), visited, coref)

                        svos.append((to_str(get_subject(sub, tokens, visited)),
                                     "!" + to_str(v) if verbNegated else to_str(v),
                                     to_str(multi_expand(objs, tokens, visited, True))))
                    else:
                        # no obj - just return the SV parts
                        svos.append((to_str(get_subject(sub, tokens, visited)),
                                     "!" + to_str(v) if verbNegated else to_str(v),))

    return svos


def get_subject(item, tokens, visited):
    parts = []

    if hasattr(item, 'lefts'):
        for part in item.lefts:
            if part.pos_ in BREAKER_POS and part.dep_ not in SPECIAL_VERB_DEPS:
                break
            if not part.lower_ in NEGATIONS:
                if hasattr(part, 'lefts'):
                    for item2 in part.lefts:
                        if item2.i not in visited:
                            visited.add(item2.i)
                            parts.extend(expand(item2, tokens, visited, True))
                parts.append(part)
                if hasattr(part, 'rights'):
                    for item2 in part.rights:
                        if item2.i not in visited:
                            visited.add(item2.i)
                            parts.extend(expand(item2, tokens, visited, True))

    parts.append(item)

    return parts


def get_modifier(item, tokens, visited):
    if item.lower_ == 'that':
        temp_item = _get_that_resolution(tokens)
        if temp_item is not None:
            item = temp_item

    parts = []

    if hasattr(item, 'rights'):
        for part in item.rights:
            if part.pos_ in BREAKER_POS and part.dep_ not in SPECIAL_VERB_DEPS:
                break
            if not part.lower_ in NEGATIONS:
                if hasattr(part, 'lefts'):
                    for item2 in part.lefts:
                        if item2.i not in visited:
                            visited.add(item2.i)
                            parts.extend(expand(item2, tokens, visited))
                parts.append(part)
                if hasattr(part, 'rights'):
                    for item2 in part.rights:
                        if item2.i not in visited:
                            visited.add(item2.i)
                            parts.extend(expand(item2, tokens, visited))

    return parts


# find subjects and their modifiers to create SMs
def findSMs(tokens, coref=None):
    sms = set()
    verbs = _find_verbs(tokens)
    for v in verbs:
        expanded_verb = expand_verb(v)
        visited = set()
        for verb in expanded_verb:
            visited.add(verb.i)
        subs, verbNegated = _get_all_subs(expanded_verb)
        # hopefully there are subs, if not, don't examine this verb any longer
        if len(subs) > 0:
            for sub in subs:
                sub, visited = _process_relative_word_and_pron([sub], list(tokens), visited, coref)
                sub = sub[0]
                sms.add((to_str(get_subject(sub, tokens, visited)), to_str(get_modifier(sub, tokens, visited))))

    return list(sms)


def _split_mods(tokens):
    split_mods = []
    split_mod = []
    for token in tokens:
        if (token.pos_ == "ADP" and token.dep_ == "prep" and token.lower_ in LOCATION_PREPOSITIONS) or \
                (token.pos_ == "SCONJ" and token.lower_ in CONJUNCTIONS) or \
                (token.head.pos_ == "VERB" and token.head.dep_ == "advcl" and token.lower_ == 'to'):
            if len(split_mod) > 0:
                split_mods.append(split_mod)
            split_mod = [token]
        else:
            split_mod.append(token)
    if len(split_mod) > 0:
        split_mods.append(split_mod)
    return split_mods


def _get_mods_from_prepositions(deps, tokens, visited):
    mods = []
    for dep in deps:
        if dep.pos_ == "ADP" and dep.dep_ == "prep":
            mods.extend(expand(dep, tokens, visited, True))
    return _split_mods(mods)


def _get_mods_from_clauses(deps, tokens, visited):
    mods = []
    for dep in deps:
        for item in dep.lefts:
            if item.pos_ == "SCONJ" and (item.lower_ == 'that' or item.lower_ == 'if'):
                mods.extend(expand(dep, tokens, visited, True))
    return _split_mods(mods)


def _get_mods_from_inf(deps, tokens, visited):
    mods = []
    for dep in deps:
        if dep.pos_ == "VERB" and dep.dep_ == "advcl":
            mods.extend(expand(dep, tokens, visited, True))
    return _split_mods(mods)


def get_children_of_verb(v_list):
    children = []
    for v in v_list:
        children.extend(list(v.lefts) + list(v.rights))
    return children


# find subjects and their modifiers to create SMs
def findVMs(tokens):
    vms = []
    verbs = _find_verbs(tokens)
    for v in verbs:
        expanded_verb = expand_verb(v)
        visited = set()
        for verb in expanded_verb:
            visited.add(verb.i)
        children = get_children_of_verb(expanded_verb)
        p_mods = _get_mods_from_prepositions(children, tokens, visited)
        c_mods = _get_mods_from_clauses(children, tokens, visited)
        i_mods = _get_mods_from_inf(children, tokens, visited)
        if len(p_mods) > 0:
            vms.append((to_str(expanded_verb), [to_str(p_mod) for p_mod in p_mods]))
        elif len(c_mods) > 0:
            vms.append((to_str(expanded_verb), [to_str(c_mod) for c_mod in c_mods]))
        elif len(i_mods) > 0:
            vms.append((to_str(expanded_verb), [to_str(i_mod) for i_mod in i_mods]))
        else:
            vms.append((to_str(expanded_verb), ''))

    return vms
