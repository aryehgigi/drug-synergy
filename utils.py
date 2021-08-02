from enum import Enum
import numpy as np
from collections import defaultdict


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
    g_out = defaultdict(list)
    t_out = defaultdict(list)
    matched = set()
    for rel1 in gold:
        found = False
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
                score = spans_intersecting / len(set(rel1['spans'] + list(rel2_spans)))
                g_out[(rel1["example_hash"], str(rel1["spans"]), get_label(rel1, unify_negs))].append((get_label(rel2, unify_negs), score))
                t_out[(rel2["example_hash"], str(rel2["spans"]), get_label(rel2, unify_negs))].append((get_label(rel1, unify_negs), score))
                found = True
                matched.add(k)
        # if a gold positive not found by test, add a false negative pair
        if not found:
            g_out[(rel1["example_hash"], str(rel1["spans"]), get_label(rel1, unify_negs))].append((Label.NO_COMB.value, 0))
    # no we iterate of the remaining relations in the test, and add the false positives
    for k, rel2 in enumerate(test):
        if k not in matched:
            t_out[(rel2["example_hash"], str(rel2["spans"]), get_label(rel2, unify_negs))].append((Label.NO_COMB.value, 0))
    return g_out, t_out


def get_confusion_matrix(gs, ts):
    m = np.zeros((len(labels), len(labels)))
    sum_m = 0
    for (_, _, label), matched in gs.items():
        scores = [s if (other == label) else 0 for other, s in matched if s == 1 or s == 0]
        if len(scores) > 0:
            o = matched[np.argmax(scores)][0]
        else:
            o = 0
        sum_m += 1
        m[o][label] += 1
        m[label][o] += 1 if label != o else 0
    for (_, _, label), matched in ts.items():
        o = matched[np.argmax([s if (other == label) else 0 for other, s in matched])][0]
        if o == 0:
            sum_m += 1
            m[label][o] += 1
            m[o][label] += 1 if label != o else 0
    return m


def f_from_p_r(gs, ts, labeled=False):
    def get_max_sum_score(v):
        interesting = 0
        score = 0
        for (_, _, label), matched in v.items():
            if label != Label.NO_COMB.value:
                interesting += 1
                score += max([s if ((not labeled) or (other == label)) else 0 for other, s in matched])
        return score / interesting
    p = get_max_sum_score(ts)
    r = get_max_sum_score(gs)
    return (2 * p * r) / (p + r)


# gold can be an annotator as reference or a data that is considered gold labeled.
# test can be an annotator to check or a model
def f_score(test, gold, unify_negs):
    gs, ts = create_vectors(gold, test, unify_negs)
    f = f_from_p_r(gs, ts)
    f_labeled = f_from_p_r(gs, ts, labeled=True)
    m = get_confusion_matrix(gs, ts) if not unify_negs else np.zeros((len(labels), len(labels)))
    return f, f_labeled, m


def relation_agreement(rels_by_anno, anns):
    m = [np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns)))]
    t_c_m = np.zeros((len(labels), len(labels)))
    for m_i, unify_negs in enumerate([False, True]):
        sum_f = 0
        sum_f_labeled = 0
        for i in range(len(anns)):
            for j in range(len(anns)):
                if i == j:
                    continue
                f, f_labeled, c_m = f_score(rels_by_anno[anns[i]], rels_by_anno[anns[j]], unify_negs)
                t_c_m = np.add(t_c_m, c_m if j > i else np.zeros((len(labels), len(labels))))
                sum_f += f
                sum_f_labeled += f_labeled
                m[m_i][i, j] = f
                m[m_i + 2][i, j] = f_labeled
        print(f"averaged unlabeled F1 score {'where POS vs NEG+COMB ' if unify_negs else ''}= {sum_f / (len(anns) * (len(anns) - 1))}")
        print(f"averaged labeled F1 score {'where POS vs NEG+COMB ' if unify_negs else ''}= {sum_f_labeled / (len(anns) * (len(anns) - 1))}")
    for i, m_i in enumerate([m[0], m[2], m[1], m[3]]):
        print(f"This is {'POS vs NEG+COMB ' if i > 1 else ''}{'unlabeled' if i % 2 == 0 else 'labeled'} pairwise F1 score table:")
        print(f'{"":7}', [f'{ann.split("-")[-1]:7}' for ann in anns])
        for i, l in enumerate(m_i):
            print(f'{anns[i].split("-")[-1]:7}', [f"{ll:7.4f}" for ll in l])
        print()
    labels_sorted = [k if k != "NO_COMB" else "N_C" for k, v in sorted(labels.items(), key=lambda x: x[1])]
    # t_c_m = t_c_m / 28
    # s = sum([t_c_m[i][j] for i in range(len(t_c_m)) for j in range(len(t_c_m)) if i >= j])
    print(f'{"":4}', [f'{label:4}' for label in labels_sorted])
    for i, l in enumerate(t_c_m):
        # sl = sum(l)
        print(f'{labels_sorted[i]:4}', [f"{ll:4.2f}" if i != 0 or j != 0 else f"{' -- ':4}" for j, ll in enumerate(l)])
