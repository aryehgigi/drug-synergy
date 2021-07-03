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
g_anns = ['yosi', 'shaked', 'dana_a', 'dana_n', 'yuval', 'yakir', 'hagit', 'maytal']


########################################################## Agreement ########################################################


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
    for m_i, metric in enumerate([""]): #, "ONE_NEG", "RIGOROUS", "RIGOROUS_ONE_NEG"]):
        for i in range(len(anns)):
            for j in range(len(anns)):
                if i == j:
                    continue
                print([{'radio': e['radio'], 'example_hash': e['example_hash'], 'class': e['class'], 'spans': e['spans']} for e in rels_by_anno[anns[i]]])
                print([{'example_hash': e['example_hash'], 'class': e['class'], 'spans': e['spans']} for e in rels_by_anno[anns[j]]])
                vec1, vec2 = calc_rel_agreement(rels_by_anno[anns[i]], rels_by_anno[anns[j]], metric)
                print(anns[i], vec1)
                print(anns[j], vec2)
                score = cohen_kappa_score(vec1, vec2)
                print(f"score: {score}")
                m[m_i][i, j] = score
    for m_i in m:
        print(f'{"":7}', [f'{ann.split("-")[-1]:7}' for ann in anns])
        for i, l in enumerate(m_i):
            print(f'{anns[i].split("-")[-1]:7}', [f"{ll:7.4f}" for ll in l])
        print()


########################################################## process input ########################################################


def sort_rels(rels_by_anno):
    for annotator, rels in rels_by_anno.items():
        for rel in rels:
            rel['spans'].sort()
        rels.sort(key=lambda x: (x['example_hash'], str(x['spans'])))


def process_prodigy_output(src, annotators):
    real_annos = lambda name: name.split("-")[-1]
    rels_by_anno = defaultdict(list)
    examples_out = ""
    with open(src) as f:
        ls = f.readlines()
    for line in ls:
        annotated = json.loads(line.strip())
        if (annotated["answer"] != "accept") or (annotators and not any([real_annos(annotated["_session_id"]) == annotator for annotator in annotators])):
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
                rels[rel['label']].add(span["span_id"])

        final = []
        for k, v in rels.items():
            rels_by_anno[real_annos(annotated["_session_id"])].append({
                'example_hash': hash(annotated['text']),
                'class': k[:-1],
                'class_orig': k,
                'spans': [(span["token_start"], span["token_end"]) for span in spans.values() if span["span_id"] in list(v)],
                'radio': [x for x in annotated['radio'] if "T" not in x],
                'text': annotated['text'],
                "paragraph": para
            })
            final.append({'class': k[:-1], 'spans': list(v)})

        examples_out += json.dumps({"sentence": text, "spans": list(spans.values()), "rels": final, "paragraph": para, "source": annotated["article_link"]}) + "\n"
    # sort rels_by_anno for alignment:
    sort_rels(rels_by_anno)

    return rels_by_anno, examples_out


########################################################## HTML ########################################################


def label_text(spans, text, lines_to_add):
    classes = defaultdict(list)
    for ann in spans:
        for span in ann["spans"]:
            for i in range(span[0], span[1] + 1):
                classes[i].append(ann["class_orig"][0] + ann["class_orig"][-1])
    data_anno_id = 0
    bunch_of_words = []
    for i, word in enumerate(text.split()):
        bunch_of_words.append(word)
        if (classes.get(i, None) != classes.get(i + 1, None)) or ((i + 1) == len(text.split())):
            if classes.get(i, None):
                lines_to_add.append(f' <span class="marker" data-anno-id="{data_anno_id}" data-anno-label="{"/".join(classes[i])}">{" ".join(bunch_of_words)}</span> ')
                data_anno_id += 1
            else:
                lines_to_add.append(" " + " ".join(bunch_of_words) + " ")
            bunch_of_words = []


def make_html(rels_by_anno):
    ls2 = []
    # for i, (annotator1, annotations1) in enumerate(list(rels_by_anno.items())[:-1]):
    #     for annotator2, annotations2 in list(rels_by_anno.items())[i + 1:]:
    annotator1 = "yosi"
    annotations1 = rels_by_anno[annotator1]
    for annotator2, annotations2 in rels_by_anno.items():
        if annotator2 == annotator1:
            continue
        ls2.append(f'''<button type="button" class="collapsible">{annotator1} - {annotator2}</button>
        <div>''')
        spans1 = []
        for i, annotation1 in enumerate(annotations1):
            spans1.append(annotation1)
            if (i + 1 == len(annotations1)) or (annotation1["example_hash"] != annotations1[i + 1]["example_hash"]):
                spans2 = []
                for annotation2 in annotations2:
                    if annotation2["example_hash"] == annotation1["example_hash"]:
                        spans2.append(annotation2)
                if str([(span["spans"], span["class_orig"]) for span in spans1]) == str([(span["spans"], span["class_orig"]) for span in spans2]):
                    spans1 = []
                    continue
                ls2.append('''<div class="supercontainer">''')
                ls2.append(f'''<div class="container"><div class="annotation-head"></div><div class="annotation-segment">''')
                label_text(spans1, annotation1["text"], ls2)
                ls2.append('''</div></div><div class="container"><div class="annotation-head"></div><div class="annotation-segment">''')
                label_text(spans2, annotation1["text"], ls2)
                ls2.append('''</div></div>''')
                ls2.append(
                    f'''<button type="button" class="collapsible">Click to see abstract</button><div style="display:none">{annotation1["paragraph"]}</div>''')
                ls2.append('''</div>''')
                spans1 = []
        ls2.append('''</div>''')
    ls_pre = []
    ls_post = []
    move_to_post = False
    with open("explain.html") as f:
        for l in  f.readlines():
            if l.startswith("#replace_here"):
                move_to_post = True
                continue
            if move_to_post:
                ls_post.append(l)
            else:
                ls_pre.append(l)
    with open("explain_edited.html", "w") as f:
        f.writelines(ls_pre)
        f.writelines(ls2)
        f.writelines(ls_post)


########################################################## export dataset ########################################################


def export_dataset(examples):
    with open("examples3.jsonl", "a") as f:
        f.write(examples)


########################################################## Main ########################################################


if __name__ == "__main__":
    rels_by_anno = []
    examples_out = ""
    annotators = sys.argv[2].split() if len(sys.argv) == 3 else g_anns

    # process annotations
    rels_by_anno, examples_out = process_prodigy_output(sys.argv[1], annotators)

    # compute agreement
    relation_agreement(rels_by_anno, annotators)

    # prepare disagreement html
    make_html(rels_by_anno)

    # export dataset for model
    export_dataset(examples_out)



