from collections import defaultdict
import sys
import json
import re


def main(src, annotator=None):
    with open(src) as f:
        ls = f.readlines()
    for line in ls:
        annotated = json.loads(line.strip())
        if (annotated["answer"] != "accept") or (annotator and not annotated["_session_id"].endswith(annotator)):
            continue
        para = re.sub("<.+?>", "", re.sub("</h3>", " ", annotated["paragraph"]))
        text = re.sub("<.+?>", "", re.sub("</h3>", " ", annotated["text"]))
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
            final.append({'class': k[:-1], 'spans': list(v)})
        with open("examples.jsonl", "a") as f:
            json.dump({"sentence": text, "spans": list(spans.values()), "rels": final, "paragraph": para}, f)
            f.write("\n")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])

