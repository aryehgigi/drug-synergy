import prodigy
import json
import re


@prodigy.recipe(
    "drug-drug-recipe",
    dataset=("Dataset to save answers to", "positional", None, str),
    annotators=("amount of annotator", "positional", None, int),
    annotator_idx=("index of current annotator for data split", "positional", None, int),
)
def drug_drug_recipe(dataset, annotators, annotator_idx, source):
    with open("drugs.txt") as f:
        drugs = [l.strip().lower() for l in f.readlines()]
        drugs_c = [re.compile(re.escape(drug), re.IGNORECASE) for drug in drugs]

    def highlight_drugs(text):
        out = text
        for drug, drug_c in zip(drugs, drugs_c):
            out = drug_c.sub(f"<b style='color:Tomato;'><i>{drug}</i></b>", out)
        return out

    def get_start_offset(e, j):
        return len(" ".join(e['sentence_text'].split()[:j])) + (0 if j == 0 else 1)
    
    def find_sent_in_para(sent, para):
        para = para.replace("\u2009", " ")
        idx = para.replace(" ", "").find(sent.replace(" ", ""))
        c = 0
        for i in range(idx):
            while para[i + c] == " ":
                c += 1
        c2 = 0
        for i in range(len(sent.replace(" ", ""))):
            while para[i + idx + c + c2] == " ":
                c2 += 1
        return idx + c, idx + c + c2 + len(sent.replace(" ", ""))
    
    def load_my_custom_stream(s):
        with open(s) as f:
            examples = [json.loads(l.strip()) for l in  f.readlines()]
        return [{
                "text": example['sentence_text'],
                "paragraph": "<h3><u>" + example['title'] + "</u></h3>" +
                             highlight_drugs(example['paragraph_text'][:find_sent_in_para(example['sentence_text'], example['paragraph_text'])[0]]) + " " +
                             " ".join([f"<b style='color:{'MediumOrchid' if tok.lower() in drugs else 'DodgerBlue'};'><i>" + tok + "</i></b>" for i, tok in enumerate(example['sentence_text'].split())]) +
                             highlight_drugs(example['paragraph_text'][find_sent_in_para(example['sentence_text'], example['paragraph_text'])[1]:]),
                "tokens": [
                    {"text": tok, "start": get_start_offset(example, i), "end": get_start_offset(example, i) + len(tok), "id": i, "ws": True if i + 1 != len(example['sentence_text'].split()) else False} # "disabled": not (find_sent_words_offsets(example['sentence_text'], example['paragraph_text'])[0] <= i < find_sent_words_offsets(example['sentence_text'], example['paragraph_text'])[1]), 
                    for i, tok in enumerate(example['sentence_text'].split())
                ],
                "spans": [
                    {"start": get_start_offset(example, i), "end": get_start_offset(example, i) + len(tok), "token_start": i, "token_end": i, "label": "DRUG"} for i, tok in enumerate(example['sentence_text'].split()) if tok.lower() in drugs
                ],
        } for example in examples]
    
    # Load your own streams from anywhere you want
    stream = load_my_custom_stream(source)
    stream = stream[annotator_idx * int(len(stream) / annotators): (annotator_idx + 1) * int(len(stream) / annotators)]
    print(len(stream))
    
    def my_template():
        return '''
            <button type="button" class="collapsible" onclick="contextClicked()">Click to get full context</button>
            <div class="content" style="word-spacing:3px;display: none;text-align:left;">{{{paragraph}}}</div>
        '''
        
    def my_template3():
        with open("radio.html") as f:
            html_txt = f.read()
        return html_txt

    def validate_answer(eg):
        selected = eg.get("radio", [])
        for label in set([rel["label"] for rel in eg.get("relations", [])]):
            if not label.startswith("COMB"):
                assert (label + "1" in selected) or (label + "0" in selected), "Before accepting, please answer the questions regarding `context` for the relevant labels."
            assert (label + "T0" in selected) or (label + "T1" in selected), "Before accepting, please answer the questions regarding `temporal information` for the relevant labels."

    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "blocks",
        "validate_answer": validate_answer,
        "config": {
            "labels": ["POS1", "POS2", "POS3", "NEG1", "NEG2", "NEG3", "COMB1", "COMB2", "COMB3"],
            "hide_relations_arrow": True,
            "wrap_relations": True,
            "relations_span_labels": ["DRUG"],
            "choice_style": "multiple",
            "javascript": open("./funcs.js").read(),
            "global_css": open("./pretty.css").read(),
            "blocks": [
                {"view_id": "relations"},
                {"view_id": "html", "html_template": my_template(), },
                {"view_id": "html", "html_template": my_template3(), },
            ]
        }
    }
