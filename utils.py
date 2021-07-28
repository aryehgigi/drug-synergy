from enum import Enum
import numpy as np


class Label(Enum):
    NO_COMB = 0
    COMB_NEG = 1
    COMB = 2
    COMB_POS = 3
    NEG_AND_COMB = 4


labels = {"POS": Label.COMB_POS.value, "NEG": Label.COMB_NEG.value, "COMB": Label.COMB.value, "NO_COMB": Label.NO_COMB.value}
labels2 = {"POS": Label.COMB_POS.value, "NEG": Label.NEG_AND_COMB.value, "COMB": Label.NEG_AND_COMB.value, "NO_COMB": Label.NO_COMB.value}


def get_label(rel, unify_negs):
    return labels[rel['class']] if not unify_negs else labels2[rel['class']]


def create_vectors(gold, test, unify_negs):
    v_out = []
    matched = set()
    for rel1 in gold:
        found = False
        max_intersecting = 0
        for k, rel2 in enumerate(test):
            if rel1['example_hash'] != rel2['example_hash']:
                continue
            rel2_spans = set(rel2['spans'])
            spans_intersecting = 0
            # count matching entity-spans
            for span in rel1['spans']:
                for span2 in rel2_spans:
                    # NOTE: currently we ease the case of overlapping drug names
                    if (span2[0] <= span[0] <= span2[1]) or (span2[0] <= span[1] <= span2[1]):
                        rel2_spans.remove(span2)
                        spans_intersecting += 1
                        break
            # we have at least partial matching
            if spans_intersecting >= 2:
                # in case we have several partials matching the same cluster - we want to keep the maximum one
                if spans_intersecting > max_intersecting:
                    if max_intersecting > 0:
                        _ = v_out.pop(-1)
                    max_intersecting = spans_intersecting
                v_out.append((get_label(rel1, unify_negs), get_label(rel2, unify_negs),
                              min(spans_intersecting / len(rel1['spans']), spans_intersecting / len(rel2['spans']))))
                found = True
                matched.add(k)
        # if a gold positive not found by test, add a false negative pair
        if not found:
            v_out.append((get_label(rel1, unify_negs), Label.NO_COMB.value, 0))
    # no we iterate of the remaining relations in the test, and add the false positives
    for k, rel2 in enumerate(test):
        if k not in matched:
            v_out.append((Label.NO_COMB.value, get_label(rel2, unify_negs), 1))
    return v_out


def f_from_p_r(v, labeled=False):
    positives = len([g for (g, _, _) in v if g != Label.NO_COMB.value])
    tp = 0
    predicted = 0
    for g, t, s in v:
        if ((g != 0) and (t != 0)) and ((not labeled) or (g == t)):
            tp += s
            predicted += 1
        elif g == 0 and t != 0:
            predicted += 1
    p = tp / predicted
    r = tp / positives
    return (2 * p * r) / (p + r)


# gold can be an annotator as reference or a data that is considered gold labeled.
# test can be an annotator to check or a model
def f_score(test, gold, unify_negs):
    v = create_vectors(gold, test, unify_negs)
    f = f_from_p_r(v)
    f_labeled = f_from_p_r(v, labeled=True)
    return f, f_labeled


def relation_agreement(rels_by_anno, anns):
    m = [np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns)))]
    for m_i, unify_negs in enumerate([False, True]):
        sum_f = 0
        sum_f_labeled = 0
        for i in range(len(anns)):
            for j in range(len(anns)):
                if i == j:
                    continue
                f, f_labeled = f_score(rels_by_anno[anns[i]], rels_by_anno[anns[j]], unify_negs)
                sum_f += f
                sum_f_labeled += f_labeled
                m[m_i][i, j] = f
                m[m_i + 2][i, j] = f_labeled
        print(f"averaged unlabeled F1 score {'where POS vs NEG+COMB ' if unify_negs else ''}= {sum_f / (len(anns) * (len(anns) - 1))}")
        print(f"averaged labeled F1 score {'where POS vs NEG+COMB ' if unify_negs else ''}= {sum_f_labeled / (len(anns) * (len(anns) - 1))}")
    for i, m_i in enumerate([m[0], m[2], m[1], m[3]]):
        print(f"This is {'POS vs NEG+COMB ' if i > 1 else ''}{'unlabeled' if i % 2 != 0 else 'labeled'} pairwise F1 score table:")
        print(f'{"":7}', [f'{ann.split("-")[-1]:7}' for ann in anns])
        for i, l in enumerate(m_i):
            print(f'{anns[i].split("-")[-1]:7}', [f"{ll:7.4f}" for ll in l])
        print()