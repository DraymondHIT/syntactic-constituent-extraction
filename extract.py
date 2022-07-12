# Copyright 2017 Peter de Vocht
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import en_core_web_sm
from collections.abc import Iterable

# use spacy small model
nlp = en_core_web_sm.load()

# dependency markers for subjects
SUBJECTS = {"nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"}
# dependency markers for objects
OBJECTS = {"dobj", "dative", "attr", "oprd", "acomp", "pobj"}
# POS tags that will break adjoining items
BREAKER_POS = {"VERB"}
# words that are negations
NEGATIONS = {"no", "not", "n't", "never", "none"}

# AUX
AUX = {"be", "is", "was", "are", "were"}
# special phrases
SPECIAL_PHRASES = {"regarded as", "viewed as", "known as", "considered as"}


def get_special_phrases(text):
    for sp in SPECIAL_PHRASES:
        if text.find(sp) != -1:
            return sp + ' '
    return ''


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
def _find_subs(tok):
    head = tok.head
    while head.pos_ != "VERB" and head.pos_ != "NOUN" and head.head != head:
        head = head.head
    if head.pos_ == "VERB" or head.pos_ == "AUX":
        subs = [tok for tok in head.lefts if tok.dep_ in SUBJECTS]
        if len(subs) > 0:
            verb_negated = _is_negated(head) or _is_negated(tok)
            subs.extend(_get_subs_from_conjunctions(subs))
            return subs, verb_negated
        elif head.head != head:
            return _find_subs(head)
    elif head.pos_ == "NOUN":
        return [head], _is_negated(tok)
    return [], False


# is the tok set's left or right negated?
def _is_negated(tok):
    parts = list(tok.lefts) + list(tok.rights)
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


# get grammatical objects for a given set of dependencies (including passive sentences)
def _get_objs_from_prepositions(deps, is_pas):
    objs = []
    for dep in deps:
        if dep.pos_ == "ADP" and is_pas and dep.dep_ == "agent":
            objs.extend([tok for tok in dep.rights if tok.dep_ in OBJECTS or
                         (tok.pos_ == "PRON" and tok.lower_ == "me") or
                         (is_pas and tok.dep_ == 'pobj')])
    return objs


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
def _get_all_subs(v):
    verb_negated = _is_negated(v)
    subs = [tok for tok in v.lefts if tok.dep_ in SUBJECTS and tok.pos_ != "DET"]
    if len(subs) > 0:
        subs.extend(_get_subs_from_conjunctions(subs))
    else:
        foundSubs, verb_negated = _find_subs(v)
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
    return (tok.pos_ == "VERB" or tok.pos_ == "AUX") and (tok.dep_ != "aux" and tok.dep_ != "auxpass" and tok.dep_ != "acl" and tok.dep_ != "advcl")


# is the token a verb?  (excluding auxiliary verbs)
def _is_verb(tok):
    return tok.pos_ == "VERB" or tok.pos_ == "AUX"


# return the verb to the right of this verb in a CCONJ relationship if applicable
# returns a tuple, first part True|False and second part the modified verb if True
def _right_of_verb_is_conj_verb(v):
    # rights is a generator
    rights = list(v.rights)

    # VERB CCONJ VERB (e.g. he beat and hurt me)
    if len(rights) > 1 and rights[0].pos_ == 'CCONJ':
        for tok in rights[1:]:
            if _is_non_aux_verb(tok):
                return True, tok

    return False, v


# get all objects for an active/passive sentence
def _get_all_objs(v, is_pas):
    # rights is a generator
    rights = list(v.rights)

    objs = [tok for tok in rights if tok.dep_ in OBJECTS or (is_pas and tok.dep_ == 'pobj')]
    objs.extend(_get_objs_from_prepositions(rights, is_pas))

    #potentialNewVerb, potentialNewObjs = _get_objs_from_attrs(rights)
    #if potentialNewVerb is not None and potentialNewObjs is not None and len(potentialNewObjs) > 0:
    #    objs.extend(potentialNewObjs)
    #    v = potentialNewVerb

    potential_new_verb, potential_new_objs = _get_obj_from_xcomp(rights, is_pas)
    if potential_new_verb is not None and potential_new_objs is not None and len(potential_new_objs) > 0:
        objs.extend(potential_new_objs)
        v = potential_new_verb
    if len(objs) > 0:
        objs.extend(_get_objs_from_conjunctions(objs))
    return v, objs


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
        print(tok.orth_, tok.dep_, tok.pos_, tok.head.orth_, [t.orth_ for t in tok.lefts], [t.orth_ for t in tok.rights])


# expand an obj / subj np using its chunk
def expand(item, tokens, visited):
    # if item.lower_ == 'that':
    #     temp_item = _get_that_resolution(tokens)
    #     if temp_item is not None:
    #         item = temp_item

    parts = []

    if hasattr(item, 'lefts'):
        for part in item.lefts:
            if part.pos_ in BREAKER_POS:
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
            if part.pos_ in BREAKER_POS:
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


# expand an obj / subj np using its chunk
def passive_expand(item, tokens, visited):
    if item.lower_ == 'that':
        temp_item = _get_that_resolution(tokens)
        if temp_item is not None:
            item = temp_item

    parts = []

    if hasattr(item, 'lefts'):
        for part in item.lefts:
            if part.pos_ in BREAKER_POS:
                break
            if not part.lower_ in NEGATIONS:
                parts.append(part)

    parts.append(item)

    if hasattr(item, 'rights'):
        for part in item.rights:
            if part.pos_ in BREAKER_POS:
                break
            if not part.lower_ in NEGATIONS:
                parts.append(part)

    if hasattr(parts[-1], 'rights'):
        for item2 in parts[-1].rights:
            if item2.pos_ == "DET" or item2.pos_ == "NOUN" or item2.pos_ == "PROPN":
                if item2.i not in visited:
                    visited.add(item2.i)
                    parts.extend(expand(item2, tokens, visited))
                break

    return parts


# convert a list of tokens to a string
def to_str(tokens):
    if isinstance(tokens, Iterable):
        return ' '.join([item.text for item in tokens])
    else:
        return ''


# find verbs and their subjects / objects to create SVOs, detect passive/active sentences
def findSVOs(tokens):
    svos = []
    passive_verbs = _get_passive_verbs(tokens)
    verbs = _find_verbs(tokens)
    for v in verbs:
        visited = set()  # recursion detection
        advmod = '' if len(list(v.rights)) == 0 or list(v.rights)[0].dep_ != "advmod" else ' ' + list(v.rights)[0].lemma_
        subs, verbNegated = _get_all_subs(v)
        # hopefully there are subs, if not, don't examine this verb any longer
        if len(subs) > 0:
            isConjVerb, conjV = _right_of_verb_is_conj_verb(v)
            if isConjVerb:
                is_pas = conjV in passive_verbs
                v2, objs = _get_all_objs(conjV, is_pas)
                advmod2 = '' if len(list(v.rights)) == 0 or list(v.rights)[0].dep_ != "advmod" else ' ' + list(v.rights)[0].lemma_
                for sub in subs:
                    if len(objs) > 0:
                        for obj in objs:
                            objNegated = _is_negated(obj)
                            if is_pas:  # reverse object / subject for passive
                                svos.append((to_str(passive_expand(obj, tokens, visited)),
                                             "!" + v.lemma_ + advmod if verbNegated or objNegated else v.lemma_ + advmod, to_str(passive_expand(sub, tokens, visited))))
                                svos.append((to_str(passive_expand(obj, tokens, visited)),
                                             "!" + v2.lemma_ + advmod2 if verbNegated or objNegated else v2.lemma_ + advmod2, to_str(passive_expand(sub, tokens, visited))))
                            else:
                                svos.append((to_str(expand(sub, tokens, visited)),
                                             "!" + v.lower_ + advmod if verbNegated or objNegated else v.lower_ + advmod, to_str(expand(obj, tokens, visited))))
                                svos.append((to_str(expand(sub, tokens, visited)),
                                             "!" + v2.lower_ + advmod2 if verbNegated or objNegated else v2.lower_ + advmod2, to_str(expand(obj, tokens, visited))))
                    else:
                        svos.append((to_str(expand(sub, tokens, visited)),
                                     "!" + v.lower_ + advmod if verbNegated else v.lower_ + advmod,))
            else:
                is_pas = v in passive_verbs
                v, objs = _get_all_objs(v, is_pas)
                advmod = '' if len(list(v.rights)) == 0 or list(v.rights)[0].dep_ != "advmod" else ' ' + list(v.rights)[0].lemma_
                for sub in subs:
                    if len(objs) > 0:
                        for obj in objs:
                            objNegated = _is_negated(obj)
                            if is_pas:  # reverse object / subject for passive
                                svos.append((to_str(passive_expand(obj, tokens, visited)),
                                             "!" + v.lemma_ + advmod if verbNegated or objNegated else v.lemma_ + advmod, to_str(passive_expand(sub, tokens, visited))))
                            else:
                                svos.append((to_str(expand(sub, tokens, visited)),
                                             "!" + v.lower_ + advmod if verbNegated or objNegated else v.lower_ + advmod, to_str(expand(obj, tokens, visited))))
                    else:
                        # no obj - just return the SV parts
                        svos.append((to_str(expand(sub, tokens, visited)),
                                     "!" + v.lower_ + advmod if verbNegated else v.lower_ + advmod,))

    return svos


def get_subject(item, tokens, visited):
    parts = []

    if hasattr(item, 'lefts'):
        for part in item.lefts:
            if part.pos_ in BREAKER_POS:
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

    return parts


def get_modifier(item, tokens, visited):
    if item.lower_ == 'that':
        temp_item = _get_that_resolution(tokens)
        if temp_item is not None:
            item = temp_item

    parts = []

    if hasattr(item, 'rights'):
        for part in item.rights:
            if part.pos_ in BREAKER_POS:
                break
            if not part.lower_ in NEGATIONS:
                parts.append(part)
                if hasattr(part, 'rights'):
                    for item2 in part.rights:
                        if item2.i not in visited:
                            visited.add(item2.i)
                            parts.extend(expand(item2, tokens, visited))

    return parts


# find subjects and their modifiers to create SMs
def findSMs(tokens):
    sms = set()
    passive_verbs = _get_passive_verbs(tokens)
    verbs = _find_verbs(tokens)
    for v in verbs:
        visited = set()  # recursion detection
        subs, verbNegated = _get_all_subs(v)
        # hopefully there are subs, if not, don't examine this verb any longer
        if len(subs) > 0:
            isConjVerb, conjV = _right_of_verb_is_conj_verb(v)
            if isConjVerb:
                is_pas = conjV in passive_verbs
                v2, objs = _get_all_objs(conjV, is_pas)
                if is_pas:
                    for obj in objs:
                        sms.add((to_str(get_subject(obj, tokens, visited)), to_str(get_modifier(obj, tokens, visited))))
                else:
                    for sub in subs:
                        sms.add((to_str(get_subject(sub, tokens, visited)), to_str(get_modifier(sub, tokens, visited))))

            else:
                is_pas = v in passive_verbs
                v, objs = _get_all_objs(v, is_pas)
                if is_pas:
                    if len(objs) > 0:
                        for obj in objs:
                            sms.add((to_str(get_subject(obj, tokens, visited)), to_str(get_modifier(obj, tokens, visited))))
                else:
                    for sub in subs:
                        sms.add((to_str(get_subject(sub, tokens, visited)), to_str(get_modifier(sub, tokens, visited))))

    return list(sms)


def _get_mods_from_prepositions(deps, tokens, visited):
    mods = []
    for dep in deps:
        if dep.pos_ == "ADP" and dep.dep_ == "prep":
            mods.extend(expand(dep, tokens, visited))
    return mods


def _get_mods_from_clauses(deps, tokens, visited):
    mods = []
    for dep in deps:
        for item in dep.lefts:
            if item.pos_ == "SCONJ" and (item.lower_ == 'that' or item.lower_ == 'if'):
                mods.extend(expand(dep, tokens, visited))
    return mods


# find subjects and their modifiers to create SMs
def findVMs(tokens):
    vms = []
    verbs = _find_verbs(tokens)
    for v in verbs:
        visited = set()
        advmod = '' if len(list(v.rights)) == 0 or list(v.rights)[0].dep_ != "advmod" else ' ' + list(v.rights)[0].lemma_
        mods = _get_mods_from_prepositions(v.rights, tokens, visited)
        _mods = _get_mods_from_clauses(v.rights, tokens, visited)
        if len(mods) > 0:
            vms.append((v.lower_ + advmod, to_str(mods)))
        elif len(_mods) > 0:
            vms.append((v.lower_ + advmod, to_str(_mods)))
        else:
            vms.append((v.lower_ + advmod, ''))

    return vms