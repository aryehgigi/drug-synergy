import prodigy
import csv


@prodigy.recipe(
    "drug-drug-recipe",
    dataset=("Dataset to save answers to", "positional", None, str),
)
def drug_drug_recipe(dataset, source):
    opts = [
        {"id": "CONTEXT", "text": "Was the context required?"},
        {"id": "TEMPO", "text": "Did the sentence contain temporal information?"}
    ]
    
    with open("drugs.txt") as f:
        drugs = [l.strip().lower() for l in f.readlines()]
    
    def get_start_offset(e, j):
        return len(" ".join(e['sentence_text'].split()[:j]))
    
    def find_sent_in_para(sent, para):
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
        examples = []
        sents = set()
        with open(s) as f:
            reader = csv.DictReader(f)
            for line in reader:
                if (line['sentence_text'] in sents) or (line['d1'].lower() == line['d2'].lower()):
                    continue
                examples.append({'sentence_text': line['sentence_text'], 'paragraph_text': line['paragraph_text'], 'd1': line['d1'], 'd1_first_index': int(line['d1_first_index']), 'd1_last_index': int(line['d1_last_index']), 'd2': line['d2'], 'd2_first_index': int(line['d2_first_index']), 'd2_last_index': int(line['d2_last_index'])})
                sents.add(line['sentence_text'])
        return [{
                "text": example['sentence_text'],
                "paragraph": example['paragraph_text'][:find_sent_in_para(example['sentence_text'], example['paragraph_text'])[0]] + "<b><i>" + example['sentence_text'] + "</i></b>" + example['paragraph_text'][find_sent_in_para(example['sentence_text'], example['paragraph_text'])[1]:],
                "options": opts,
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
    print(len(stream))
    
    def my_template():
        return '''
            <button type="button" class="collapsible" onclick="dis = document.getElementsByClassName('content')[0]; if (dis.style.display === 'block') {dis.style.display = 'none'} else {dis.style.display = 'block'};">Click to get full context</button>
            <div class="content" style="display: none;text-align:left;">{{{paragraph}}}</div>
        '''
    
    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "blocks",
        "config": {
            "labels": ["SYN1", "SYN2", "SYN3", "SYN4", "SYN5", "NON1", "NON2", "NON3", "NON4", "NON5"],
            "hide_relations_arrow": True,
            "wrap_relations": True,
            "relations_span_labels": ["DRUG"],
            "choice_style": "multiple",
            "blocks": [
                {"view_id": "relations"},
                {"view_id": "html", "html_template": my_template(), },
                {"view_id": "choice", "text": None},
            ]
        }
    }