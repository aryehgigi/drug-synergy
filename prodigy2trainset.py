from collections import defaultdict
import sys
import json
import re
from enum import Enum
import numpy as np
from sklearn.metrics import cohen_kappa_score


class Label(Enum):
    NO_COMB = 0
    COMB_NEG = 1
    COMB = 2
    COMB_POS = 3


labels = {"POS": Label.COMB_POS.value, "NEG": Label.COMB_NEG.value, "COMB": Label.COMB.value}
labels2 = {"POS": Label.COMB_POS.value, "NEG": Label.NO_COMB.value, "COMB": Label.NO_COMB.value}
g_anns = ['drug_drug_pilot_shared-yosi', 'drug_drug_pilot_shared-dana_a', 'drug_drug_pilot_shared-dana_n', 'drug_drug_pilot_shared-yuval', 'drug_drug_pilot_shared-yakir', 'drug_drug_pilot_shared-hagit', 'drug_drug_pilot_shared-maytal']


def sort_rels(rels_by_anno):
    for annotator, rels in rels_by_anno.items():
        for rel in rels:
            rel['spans'].sort()
        rels.sort(key=lambda x: (x['example_hash'], str(x['spans'])))


def get_label(rel, metric):
    return labels[rel['class']] if "ONE_NEG" not in metric else labels2[rel['class']]


def calc_rel_agreement(anno1, anno2, metric):
    i = 0
    j = 0
    vec1 = []
    vec2 = []
    if "RIGOROUS" not in metric:
        bla = set()
        for rel1 in anno1:
            found = False
            for k, rel2 in enumerate(anno2):
                if (rel1['example_hash'] != rel2['example_hash']):
                    continue
                rel2_spans = set(rel2['spans'])
                spans_intersecting = 0
                for span in rel1['spans']:
                    for span2 in rel2_spans:
                        if (span2[0] <= span[0] <= span2[1]) or (span2[0] <= span[1] <= span2[1]):
                            rel2_spans.remove(span2)
                            spans_intersecting += 1
                            break
                if spans_intersecting >= 2:
                    vec1.append(get_label(rel1, metric))
                    vec2.append(get_label(rel2, metric))
                    if get_label(rel1, metric) != get_label(rel2, metric):
                        print(f"same tree, diff label: {rel1} {rel2}")
                    found = True
                    bla.add(k)
            if not found:
                vec1.append(get_label(rel1, metric))
                vec2.append(Label.NO_COMB.value)
                if get_label(rel1, metric) != Label.NO_COMB.value:
                    print(f"leftover rel1: {rel1}")
        for k, rel2 in enumerate(anno2):
            if k not in bla:
                vec1.append(Label.NO_COMB.value)
                vec2.append(get_label(rel2, metric))
                if get_label(rel2, metric) != Label.NO_COMB.value:
                    print(f"leftover rel2: {rel2}")
        return vec1, vec2
    while i < len(anno1) and j < len(anno2):
        if anno1[i]['text'] == anno2[j]['text']:
            bla = anno1[i]['text']
        if (i == len(anno1)) or ((j < len(anno2)) and (anno1[i]['example_hash'] > anno2[j]['example_hash'])):
            vec1.append(Label.NO_COMB.value)
            vec2.append(get_label(anno2[j], metric))
            j += 1
        elif (j == len(anno2)) or ((i < len(anno1)) and (anno1[i]['example_hash'] < anno2[j]['example_hash'])):
            vec1.append(get_label(anno1[i], metric))
            vec2.append(Label.NO_COMB.value)
            i += 1
        elif anno1[i]['spans'] == anno2[j]['spans']:
            vec1.append(get_label(anno1[i], metric))
            vec2.append(get_label(anno2[j], metric))
            i += 1
            j += 1
        # for now we treat only exact match as success,
        #   but next i should think of how to treat the different cases (completely different/subordinate/overlap)
        #   of the non rigorous metrics.
        else:
            which = 0
            for a1, a2 in zip(list(sum(anno1[i]['spans'], ())), list(sum(anno2[j]['spans'], ()))):
                if a1 < a2:
                    which = 1
                    break
                elif a1 > a2:
                    which = 2
                    break
                # here I can check if they equal but this is obviously not enough to detrmine overlap, or to know if future rel
            if which == 0:
                which = 1 if len(anno1[i]['spans']) < len(anno2[j]['spans']) else 2
            if which == 2:
                vec1.append(Label.NO_COMB.value)
                vec2.append(get_label(anno2[j], metric))
                j += 1
            else:
                vec1.append(get_label(anno1[i], metric))
                vec2.append(Label.NO_COMB.value)
                i += 1
    return vec1, vec2


def relation_agreement(rels_by_anno, anns):
    m = [np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns))), np.ones((len(anns), len(anns)))]
    for m_i, metric in enumerate([""]): #["", "ONE_NEG", "RIGOROUS", "RIGOROUS_ONE_NEG"]):
        for i in range(len(anns)):
            for j in range(len(anns)):
                if i == j:
                    continue
                print([{'example_hash': e['example_hash'], 'class': e['class'], 'spans': e['spans']} for e in rels_by_anno[anns[i]]])
                print([{'example_hash': e['example_hash'], 'class': e['class'], 'spans': e['spans']} for e in rels_by_anno[anns[j]]])
                vec1, vec2 = calc_rel_agreement(rels_by_anno[anns[i]], rels_by_anno[anns[j]], metric)
                print(anns[i], vec1)
                print(anns[j], vec2)
                score = cohen_kappa_score(vec1, vec2)
                print(f"score: {score}")
                m[m_i][i, j] = score
    for m_i in m:
        for l in m_i:
            print([f"{ll:.4f}" for ll in l])
        print()


def main(src, annotators=None):
    rels_by_anno = defaultdict(list)
    extra_spans = dict()
    skipped = dict()
    with open(src) as f:
        ls = f.readlines()
    for line in ls:
        annotated = json.loads(line.strip())
        if (annotated["answer"] != "accept") or (annotators and not any([annotated["_session_id"].endswith(annotator) for annotator in annotators])):
            # # for entity agreement
            # k = str(hash(annotated["text"]))
            # if k in skipped:
            #     skipped[k].append(annotated["_session_id"])
            # else:
            #     skipped[k] = [annotated["_session_id"]]
            continue
        para = re.sub("<[huib/].*?>", "", re.sub("</h3>", " ", annotated["paragraph"]))
        text = annotated["text"]
        spans = {str(span): {
                **{'span_id': i, 'text': annotated["text"][span['start']:span['end']]},
                **{k: v for k, v in span.items() if k != 'label'}}
            for i, span in enumerate(annotated['spans'])}
        rels = defaultdict(set)
        for rel in annotated["relations"]:
            for span_type in ['head_span', 'child_span']:
                span = spans.get(str(rel[span_type]), None)
                if not span:
                    spans[str(rel[span_type])] = \
                        {** {'span_id': len(spans), 'text': annotated["text"][rel[span_type]['start']:rel[span_type]['end']]},
                         ** {k: v for k, v in rel[span_type].items() if k != 'label'}}
                    span = spans[str(rel[span_type])]
                    # for entity agreement
                    k = str((hash(annotated["text"]), span["token_start"], span["token_end"]))
                    if k in extra_spans:
                        extra_spans[k].append(annotated["_session_id"])
                    else:
                        extra_spans[k] = [annotated["_session_id"]]
                rels[rel['label']].add(span["span_id"])

        final = []
        for k, v in rels.items():
            rels_by_anno[annotated["_session_id"]].append({'example_hash': hash(annotated['text']), 'text': annotated['text'], 'class': k[:-1], 'spans':
                [(span["token_start"], span["token_end"]) for span in spans.values() if span["span_id"] in list(v)]
            })
            final.append({'class': k[:-1], 'spans': list(v)})
        with open("examples2.jsonl", "a") as f:
            json.dump({"sentence": text, "spans": list(spans.values()), "rels": final, "paragraph": para, "source": annotated["article_link"]}, f)
            f.write("\n")
    # sort rels_by_anno for alignment:
    sort_rels(rels_by_anno)

    return rels_by_anno

    # entity agreement
    # if False:
    #     krip = []
    #     for i in extra_spans:
    #         krip.append([])
    #     for i, (k, v) in enumerate(extra_spans.items()):
    #         for ann in anns:
    #             if ann in v:
    #                 krip[i].append(1)
    #             elif k.split(",")[0][1:] in skipped and ann in skipped[k.split(",")[0][1:]]:
    #                 krip[i].append(0)
    #             else:
    #                 krip[i].append(2)
    #     print(krip)


def make_html(rels_by_anno):
    ls2 = []
    for i, (annotator1, annotation1) in enumerate(list(rels_by_anno.items())[:-1]):
        for annotator2, annotation2 in list(rels_by_anno.items())[i + 1:]:
            ls2.append(f'''
                <button type="button" class="collapsible">{annotator1}-{annotator2}</button>
                <div class="content">
                    <p>{annotation1}</p>
                    <p>{annotation2}</p>
                </div>''')
    with open("explain.html") as f:
        ls = f.readlines()
    with open("explain_edited.html", "w") as f:
        f.writelines(ls)
        f.writelines(ls2)



if __name__ == "__main__":
    rels_by_anno = []
    if len(sys.argv) == 2:
        rels_by_anno = main(sys.argv[1])
    elif len(sys.argv) == 3:
        rels_by_anno = main(sys.argv[1], sys.argv[2].split())

    # compute agreement
    #relation_agreement(rels_by_anno, [g_anns[0], g_anns[5]])

    make_html(rels_by_anno)


