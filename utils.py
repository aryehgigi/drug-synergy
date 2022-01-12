from enum import Enum
import numpy as np
from collections import defaultdict
# from nltk import agreement
# from sklearn.metrics import cohen_kappa_score


class Label(Enum):
    NO_COMB = 0
    COMB_NEG = 1
    COMB = 2
    COMB_POS = 3
    UNIFY = 4


labels = {"POS": Label.COMB_POS.value, "NEG": Label.COMB_NEG.value, "COMB": Label.COMB.value, "NO_COMB": Label.NO_COMB.value}
labels1 = {"POS": Label.COMB_POS.value, "NEG": Label.UNIFY.value, "COMB": Label.UNIFY.value, "NO_COMB": Label.NO_COMB.value}
labels2 = {"POS": Label.UNIFY.value, "NEG": Label.UNIFY.value, "COMB": Label.UNIFY.value, "NO_COMB": Label.NO_COMB.value}
labels3 = {"POS": Label.COMB_POS.value, "NEG": Label.NO_COMB.value, "COMB": Label.NO_COMB.value, "NO_COMB": Label.NO_COMB.value}
labels4 = {"POS": Label.COMB_POS.value, "NEG": Label.NO_COMB.value, "COMB": Label.NO_COMB.value, "NO_COMB": Label.NO_COMB.value}

unification_scheme = {0: labels, 1: labels1, 2: labels2, 3: labels3, 4: labels4}


def get_label(rel, unify_negs):
    return unification_scheme[unify_negs][rel['class']]


def create_vectors(gold, test, unify_negs, exact_match):
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
            if ((spans_intersecting >= 2) and (not exact_match)) or ((spans_intersecting / len(set(rel1['spans'] + list(rel2_spans)))) == 1):
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


def kappa_self(a1, a2):
    if len(a1) == 0 or len(a2) == 0:
        return 0
    cur_labels = set(a1 + a2)
    ao = sum(aa1 == aa2 for aa1, aa2 in zip(a1, a2)) / len(a1)
    ae = sum([(sum([aa == label for aa in a1]) / len(a1)) *
              (sum([aa == label for aa in a2]) / len(a2))
              for label in cur_labels])
    k = (ao - ae) / (1 - ae)
    return k


def calculate_cohens_kappa(gold, test, unify_negs):
    gs, ts = create_vectors(gold, test, unify_negs, True)
    a1 = []
    a2 = []
    for (_, _, label), matched in gs.items():
        if matched[0][0] == 0:
            continue
        a1.append(label)
        a2.append(matched[0][0])
    # formatted_codes = [[1, i, a1[i]] for i in range(len(a1))] + [[2, i, a2[i]] for i in range(len(a2))]
    # ratingtask = agreement.AnnotationTask(data=formatted_codes)
    # k = cohen_kappa_score(a1, a2)
    # print(ratingtask.alpha(), ratingtask.kappa(), k)
    k = kappa_self(a1, a2)
    total_structures = len(gs) + len([label for (_, _, label), matched in ts.items() if matched[0][0] == 0])
    return k, len(a1), total_structures


def get_confusion_matrix(gold, test):
    gs, ts = create_vectors(gold, test, False, True)
    m = np.zeros((len(labels), len(labels)))
    for (_, _, label), matched in gs.items():
        other = matched[0][0]
        m[other][label] += 1
        m[label][other] += 1 if label != other else 0
    for (_, _, label), matched in ts.items():
        other = matched[0][0]
        if other == 0:
            m[label][other] += 1
            m[other][label] += 1 if label != other else 0
    return m


def f_from_p_r(gs, ts, labeled=False):
    def get_max_sum_score(v):
        interesting = 0
        score = 0
        for (_, _, label), matched in v.items():
            if label != Label.NO_COMB.value:
                interesting += 1
                score += max([s if ((not labeled) or (other == label)) else 0 for other, s in matched])
        return (score / interesting) if interesting else 0
    p = get_max_sum_score(ts)
    r = get_max_sum_score(gs)
    return ((2 * p * r) / (p + r)) if (p + r > 0) else 0


# gold can be an annotator as reference or a data that is considered gold labeled.
# test can be an annotator to check or a model
def f_score(test, gold, unify_negs, exact_match):
    gs, ts = create_vectors(gold, test, unify_negs, exact_match)
    f = f_from_p_r(gs, ts)
    f_labeled = f_from_p_r(gs, ts, labeled=True)
    return f, f_labeled


def print_kappas(kappas, anns, unify_negs, structure_agreement):
    c = 0
    k_avg = [0] * len(anns)
    print()
    print(f'kappa calculation (unify negs = {unify_negs}):')
    print(' '.join([f'{ii:4}' for ii in range(len(anns))]))
    for i in range(len(anns)):
        s = f'{i}: '
        for j in range(len(anns)):
            if j > i:
                s += f'{kappas[c]:4.2f} '
                k_avg[i] += kappas[c]
                k_avg[j] += kappas[c]
                c += 1
            elif i == j:
                s += '---- '
            else:
                s += '0.00 '
        print(s)
    print(f'avg kappa global {sum(kappas) / len(kappas):.2f}')
    print(f'avg kappa per annotator: ' + ', '.join([f'{i}: {k / (len(anns) - 1):.2f}' for i, k in enumerate(k_avg)]))
    sa_final = [f'{i}: {sa[0]:.2f} ({sa[1]:.2f})' for i, sa in enumerate(structure_agreement)]
    print(f"averaged agreed structures (out of averaged total structure count): " + ', '.join(sa_final))
    print(f"{' ':3}{'k':4} {'sa':5} {'st':5}")
    for i, (k, sa) in enumerate(zip(k_avg, structure_agreement)):
        print(f'{str(i) + ":":3}{k / (len(anns) - 1):4.2f} {sa[0]:5.2f} {sa[1]:5.2f}')
    print()


def relation_agreement(rels_by_anno, anns, exact_match=False):
    m = [np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns)))]
    t_c_m = np.zeros((len(labels), len(labels)))
    for m_i, unify_negs in enumerate([0, 1, 2, 3]):
        kappas = []
        sum_f = 0
        sum_f_labeled = 0
        structure_agreement = []
        for i in range(len(anns)):
            total_agreed = []
            total_total = []
            for j in range(len(anns)):
                if i == j:
                    continue
                f, f_labeled = f_score(rels_by_anno[anns[i]], rels_by_anno[anns[j]], unify_negs, exact_match)
                sum_f += f
                sum_f_labeled += f_labeled
                # m[m_i][i, j] = f
                # m[m_i + 2][i, j] = f_labeled
                if (0 == unify_negs) and (j > i):
                    c_m = get_confusion_matrix(rels_by_anno[anns[i]], rels_by_anno[anns[j]])
                    t_c_m = np.add(t_c_m, c_m)
                # k, agreed, total = calculate_cohens_kappa(rels_by_anno[anns[i]], rels_by_anno[anns[j]], unify_negs)
                # total_agreed.append(agreed)
                # total_total.append(total)
                # if j > i:
                #     kappas.append(k)
            #structure_agreement.append((sum(total_agreed) / len(total_agreed), sum(total_total) / len(total_total)))
        print(f"averaged unlabeled F1 score where the unification scheme is {unify_negs}= {sum_f / (len(anns) * (len(anns) - 1))}")
        print(f"averaged labeled F1 score where the unification scheme is {unify_negs}= {sum_f_labeled / (len(anns) * (len(anns) - 1))}")
        #print_kappas(kappas, anns, unify_negs, structure_agreement)
    # for i, m_i in enumerate([m[0], m[2], m[1], m[3]]):
    #     if i == 2:
    #         continue
    #     print(f"This is {'POS vs NEG+COMB ' if i > 1 else ''}{'unlabeled' if i % 2 == 0 else 'labeled'} pairwise F1 score table:")
    #     print(f'{"":7}', [f'{ann.split("-")[-1]:7}' for ann in anns])
    #     for i, l in enumerate(m_i):
    #         print(f'{anns[i].split("-")[-1]:7}', [f"{ll:7.4f}" for ll in l])
    #     print()
    labels_sorted = [k if k != "NO_COMB" else "N_C" for k, v in sorted(labels.items(), key=lambda x: x[1])]
    print(f'{"":4}', [f'{label:4}' for label in labels_sorted])
    for i, l in enumerate(t_c_m):
        print(f'{labels_sorted[i]:4}', [f"{int(ll):4}" if i != 0 or j != 0 else f"{' -- ':4}" for j, ll in enumerate(l)])
    print()

    # s = sum([t_c_m[i][j] for i in range(len(t_c_m)) for j in range(len(t_c_m)) if i >= j])
    print(f'{"":4}', [f'{label:4}' for label in labels_sorted])
    for i, l in enumerate(t_c_m):
        if i == 0:
            continue
        sl = sum(l)
        print(f'{labels_sorted[i]:4}', [f"{ll/sl:4.2f}" if i != 0 or j != 0 else f"{' -- ':4}" for j, ll in enumerate(l)])
    print()
