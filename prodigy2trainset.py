from collections import defaultdict
import sys
import json
import re
import utils

g_anns = ['yosi', 'shaked', 'dana_a', 'dana_n', 'yuval', 'yakir', 'hagit', 'maytal']


########################################################## process input ########################################################


def sort_rels(rels_by_anno):
    for annotator, rels in rels_by_anno.items():
        for rel in rels:
            rel['spans'].sort()
        rels.sort(key=lambda x: (x['example_hash'], str(x['spans'])))


def process_prodigy_output(src, annotators, include_no_combs):
    real_annos = lambda name: name.split("-")[-1]
    rels_by_anno = defaultdict(list)
    rels_by_nary = defaultdict(list)
    rels_by_relcount = defaultdict(list)
    examples_out = ""
    ignored = set()
    with open(src) as f:
        ls = f.readlines()
    for line in ls:
        annotated = json.loads(line.strip())
        if annotated["answer"] != "accept":
            ignored.add(hash(annotated['text']))
    for line in ls:
        annotated = json.loads(line.strip())
        if hash(annotated["text"]) in ignored or (annotators and not any([real_annos(annotated["_session_id"]) == annotator for annotator in annotators])):
            continue
        para = re.sub("<[huib/].*?>", "", re.sub("</h3>", " ", annotated["paragraph"]))
        para2 = re.sub("h3>", "h4>", annotated["paragraph"])
        text = annotated["text"]
        spans = {str(span): {
                **{'span_id': i, 'text': annotated["text"][span['start']:span['end']]},
                **{k: v for k, v in span.items() if k != 'label'}}
            for i, span in enumerate(annotated['spans'])}
        rels = defaultdict(set)
        used_spans = []
        for rel in annotated["relations"]:
            for span_type in ['head_span', 'child_span']:
                span = spans.get(str(rel[span_type]), None)
                if not span:
                    spans[str(rel[span_type])] = \
                        {** {'span_id': len(spans), 'text': annotated["text"][rel[span_type]['start']:rel[span_type]['end']]},
                         ** {k: v for k, v in rel[span_type].items() if k != 'label'}}
                    span = spans[str(rel[span_type])]
                rels[rel['label']].add(span["span_id"])
                used_spans.append(span["span_id"])
        if include_no_combs:
            for span in spans.values():
                if span["span_id"] not in used_spans:
                    rels["NO_COMB1"].add(span["span_id"])

        final = []
        for k, v in rels.items():
            appendi = {
                'example_hash': hash(annotated['text']),
                'class': k[:-1],
                'class_orig': k,
                'spans': [(span["token_start"], span["token_end"]) for span in spans.values() if span["span_id"] in list(v)],
                'radio': [x for x in annotated['radio'] if "T" not in x],
                'text': annotated['text'],
                "paragraph": para2,
                "annotator": annotated["_session_id"].split("-")[-1]
            }
            rels_by_anno[real_annos(annotated["_session_id"])].append(appendi)
            rels_by_nary[len(v)].append(appendi)
            rels_by_relcount[len(rels)].append(appendi)
            is_context_needed = (len([radio for radio in annotated["radio"] if radio.startswith(k) and "T" not in radio and radio.endswith("1")]) == 1) or \
                                (k.startswith("COMB"))

            final.append({'class': k[:-1], 'spans': list(v), "is_context_needed": is_context_needed})
        spans_fixed = [
            {
                **{k: v for k, v in span.items() if k != 'token_end'},
                **{'token_end': span['token_end'] + 1}}
            for i, span in enumerate(spans.values())
        ]
        examples_out += json.dumps({"sentence": text, "spans": spans_fixed, "rels": final, "paragraph": para, "source": annotated.get("article_link", None)}) + "\n"
    # sort rels_by_anno for alignment:
    sort_rels(rels_by_anno)

    return rels_by_anno, examples_out, rels_by_nary, rels_by_relcount


########################################################## Yosi's HTML ########################################################


def label_text(spans, text, lines_to_add, show_no_comb=False):
    classes = defaultdict(list)
    for ann in spans:
        if ann["class"].startswith("NO_COMB") and not show_no_comb:
            continue
        for span in ann["spans"]:
            for i in range(span[0], span[1] + 1):
                classes[i].append((ann["class_orig"][0] if not ann["class_orig"].startswith("NO_COMB") else "O") + ann["class_orig"][-1])
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


def label_container(spans1, spans2, text, para, lines_to_add, annotator1, annotator2):
    if len([span for span in spans1 + spans2 if not span["class"].startswith("NO_COMB")]) == 0:
        return
    s = max(len(annotator2), len(annotator1))
    lines_to_add.append('''<div class="supercontainer"><div class="midcontainer">''')
    lines_to_add.append(f'''<div class="container"><div class="annotation-head"></div><div class="annotation-segment">''')
    lines_to_add.append("<b>" + f'{annotator1.capitalize():{s}}'.replace(" ", "_") + ":</b> ")
    label_text(spans1, text, lines_to_add)
    lines_to_add.append(
        '''</div></div><div class="container"><div class="annotation-head"></div><div class="annotation-segment">''')
    lines_to_add.append("<b>" + f'{annotator2.capitalize():{s}}'.replace(" ", "_") + ":</b> ")
    label_text(spans2, text, lines_to_add)
    lines_to_add.append('''</div></div></div><div class="abstractcontainer">''')
    lines_to_add.append(
        f'''<button type="button" class="collapsible" style="background-color:#eee">Click to see abstract</button><div style="display:none">{para}</div>''')
    lines_to_add.append('''</div></div>''')


def make_html(rels_by_anno):
    ls2 = []
    annotator1 = "yosi"
    annotations1 = rels_by_anno[annotator1]
    visited = set()
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
                visited.add(annotation1["example_hash"])
                for annotation2 in annotations2:
                    if annotation2["example_hash"] == annotation1["example_hash"]:
                        spans2.append(annotation2)
                if str([(span["spans"], span["class"]) for span in spans1]) == str([(span["spans"], span["class"]) for span in spans2]):
                    spans1 = []
                    continue
                label_container(spans1, spans2, annotation1["text"], annotation1["paragraph"], ls2, annotator1, annotator2)
                spans1 = []
        spans2 = []
        for i, annotation2 in enumerate(annotations2):
            if annotation2["example_hash"] in visited:
                continue
            spans2.append(annotation2)
            if (i + 1 == len(annotations2)) or (annotation2["example_hash"] != annotations2[i + 1]["example_hash"]):
                label_container([], spans2, annotation2["text"], annotation2["paragraph"], ls2, annotator1, annotator2)
                spans2 = []
        ls2.append('''</div>''')
    ls_pre = []
    ls_post = []
    move_to_post = False
    with open("explains/explain.html") as f:
        for l in f.readlines():
            if l.startswith("#replace_here"):
                move_to_post = True
                continue
            if move_to_post:
                ls_post.append(l)
            else:
                ls_pre.append(l)
    with open("explains/explain_edited.html", "w") as f:
        f.writelines(ls_pre)
        f.writelines(ls2)
        f.writelines(ls_post)


########################################################## Hillel's HTML ########################################################


def hillel_label_container(spans1, text, para, lines_to_add, annotator):
    lines_to_add.append('''<div class="supercontainer"><div class="midcontainer">''')
    lines_to_add.append(f'''<div class="container"><div class="annotation-head"></div><div class="annotation-segment">''')
    lines_to_add.append(f"<b>{annotator.capitalize()}:</b> ")
    label_text(spans1, text, lines_to_add)
    lines_to_add.append('''</div></div></div><div class="abstractcontainer">''')
    lines_to_add.append(
        f'''<button type="button" class="collapsible" style="background-color:#eee">Click to see abstract</button><div style="display:none">{para}</div>''')
    lines_to_add.append('''</div></div>''')


def no_comb_error_analysis_label_container(spans1, text, para, lines_to_add, annotator):
    found_no_comb = False
    found_other = False
    for ann in spans1:
        if ann["class"].startswith("NO_COMB"):
            found_no_comb = True
        if not ann["class"].startswith("NO_COMB"):
            found_other = True
    if not (found_no_comb and found_other):
        return
    lines_to_add.append('''<div class="supercontainer"><div class="midcontainer">''')
    lines_to_add.append(f'''<div class="container"><div class="annotation-head"></div><div class="annotation-segment">''')
    lines_to_add.append(f"<b>{annotator.capitalize()}:</b> ")
    label_text(spans1, text, lines_to_add, show_no_comb=True)
    lines_to_add.append('''</div></div></div><div class="abstractcontainer">''')
    lines_to_add.append(
        f'''<button type="button" class="collapsible" style="background-color:#eee">Click to see abstract</button><div style="display:none">{para}</div>''')
    lines_to_add.append('''</div></div>''')


def make_hillels_html(rels_by_nary, rels_by_relcount, func):
    ls2 = []
    lll = []
    for ii, (nary, annotations) in enumerate(sorted(rels_by_nary.items(), reverse=True)):
        spans1 = []
        iii = 0
        ls3 = []
        for i, annotation1 in enumerate(annotations):
            spans1.append(annotation1)
            if (i + 1 == len(annotations)) or (annotation1["example_hash"] != annotations[i + 1]["example_hash"]):
                func(spans1, annotation1["text"], annotation1["paragraph"], ls3, annotation1["annotator"])
                spans1 = []
                iii += 1
        lll.append(f'<a href="#coll{ii}">{nary}-ary drug combinations: found {iii}</a><br/>')
        ls2.append(
            f'''<button type="button" class="collapsible" id="coll{ii}">{nary}-ary drug combinations: found {iii}</button><div>''')
        ls2.extend(ls3)
        ls2.append('''</div>''')
    ls_pre = []
    ls_post = []
    move_to_post = False
    with open("explains/explain.html") as f:
        for l in f.readlines():
            if l.startswith("#replace_here"):
                move_to_post = True
                continue
            if move_to_post:
                ls_post.append(l)
            else:
                ls_pre.append(l)
    with open("explains/explain_by_nary.html", "w") as f:
        f.writelines(ls_pre)
        f.writelines(lll)
        f.writelines(ls2)
        f.writelines(ls_post)

    ls2 = []
    lll = []
    for ii, (relcount, annotations) in enumerate(sorted(rels_by_relcount.items(), reverse=True)):
        spans1 = []
        ls3 = []
        iii = 0
        for i, annotation1 in enumerate(annotations):
            spans1.append(annotation1)
            if (i + 1 == len(annotations)) or (annotation1["example_hash"] != annotations[i + 1]["example_hash"]):
                func(spans1, annotation1["text"], annotation1["paragraph"], ls3, annotation1["annotator"])
                spans1 = []
                iii += 1
        lll.append(f'<a href="#coll{ii}">sentences with {relcount} relations: found {iii}</a><br/>')
        ls2.append(
            f'''<button type="button" class="collapsible" id="coll{ii}">sentences with {relcount} relations: found {iii}</button><div>''')
        ls2.extend(ls3)
        ls2.append('''</div>''')
    ls_pre = []
    ls_post = []
    move_to_post = False
    with open("explains/explain.html") as f:
        for l in f.readlines():
            if l.startswith("#replace_here"):
                move_to_post = True
                continue
            if move_to_post:
                ls_post.append(l)
            else:
                ls_pre.append(l)
    with open("explains/explain_by_rel_count.html", "w") as f:
        f.writelines(ls_pre)
        f.writelines(lll)
        f.writelines(ls2)
        f.writelines(ls_post)


########################################################## export dataset ########################################################


def export_dataset(examples, i):
    with open(f"converted2model/examples{i}.jsonl", "a") as f:
        f.write(examples)


########################################################## Main ########################################################


if __name__ == "__main__":
    rels_by_anno = []
    examples_out = ""
    annotators = sys.argv[2].split()
    if len(annotators) == 0:
        annotators = g_anns
    do_agreement = bool(int(sys.argv[3]))
    do_agreement_html = bool(int(sys.argv[4]))
    do_explain = bool(int(sys.argv[5]))
    do_err_analysis_no_comb = bool(int(sys.argv[6]))
    export_idx = int(sys.argv[7])

    if do_agreement_html or do_err_analysis_no_comb:
        include_no_combs = True
    else:
        include_no_combs = False

    # process annotations
    rels_by_anno, examples_out, rels_by_nary, rels_by_relcount = process_prodigy_output(sys.argv[1], annotators, include_no_combs)

    # compute agreement
    if do_agreement:
        utils.relation_agreement(rels_by_anno, annotators)

    # prepare disagreement html
    if do_agreement_html:
        make_html(rels_by_anno)
    if do_explain:
        make_hillels_html(rels_by_nary, rels_by_relcount, hillel_label_container)
    # here i check sentences that have both no comb and some other combination
    #   specifically interested with many rels in same sent (due to the max 3 limit)
    if do_err_analysis_no_comb:
        make_hillels_html(rels_by_nary, rels_by_relcount, no_comb_error_analysis_label_container)

    # export dataset for model
    if export_idx:
        export_dataset(examples_out, export_idx)



