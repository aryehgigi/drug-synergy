import prodigy
import csv
# import spacy
# from prodigy.components.preprocess import add_tokens


highlight_js = '''let text_selection = document.getElementById("text");
text_selection.addEventListener("select", highlightText);

function highlightText() {
  let textarea = event.target;
  let selection = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
  console.log(selection)
}'''

highlight_js = '''let text_selection = document.getElementById("text");text_selection.addEventListener("select", highlightText);function highlightText() {let textarea = event.target;let selection = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);console.log(selection)}'''


@prodigy.recipe(
    "drug-drug-recipe",
    dataset=("Dataset to save answers to", "positional", None, str),
)
def drug_drug_recipe(dataset, source):
    opts = [
        {"id": "CONTEXT", "text": "Was the context required?"},
        {"id": "TEMPO", "text": "Did the sentence contain temporal information?"}
    ]
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
    
    # def find_sent_words_offsets(sent, para):
    # idx = para.replace(" ", "").find(sent.replace(" ", ""))
    # c = 0
    # for i in range(idx):
        # while para[i + c] == " ":
            # c += 1
    # c2 = 0
    # for i in range(len(sent.replace(" ", ""))):
        # while para[i + idx + c + c2] == " ":
            # c2 += 1
    # return len(para[:idx + c].split()), len(para[idx + c: idx + c + c2 + len(sent.replace(" ", ""))].split())
    
    def load_my_custom_stream(s):
        examples = []
        with open(s) as f:
            reader = csv.DictReader(f)
            for line in reader:
                examples.append({'sentence_text': line['sentence_text'], 'paragraph_text': line['paragraph_text'], 'd1': line['d1'], 'd1_first_index': int(line['d1_first_index']), 'd1_last_index': int(line['d1_last_index'])})
        return [{
                "text": example['sentence_text'],
                "paragraph": example['paragraph_text'][:find_sent_in_para(example['sentence_text'], example['paragraph_text'])[0]] + "<b><i>" + example['sentence_text'] + "</i></b>" + example['paragraph_text'][find_sent_in_para(example['sentence_text'], example['paragraph_text'])[1]:],
                "options": opts,
                "tokens": [
                    {"text": tok, "start": get_start_offset(example, i), "end": get_start_offset(example, i) + len(tok), "id": i, "ws": True if i + 1 != len(example['sentence_text'].split()) else False} # "disabled": not (find_sent_words_offsets(example['sentence_text'], example['paragraph_text'])[0] <= i < find_sent_words_offsets(example['sentence_text'], example['paragraph_text'])[1]), 
                    for i, tok in enumerate(example['sentence_text'].split())
                ],
                "spans": [
                    {"start": get_start_offset(example, example['d1_first_index']), "end": get_start_offset(example, example['d1_first_index']) + len(example['d1']), "token_start": example['d1_first_index'], "token_end": example['d1_last_index'], "label": "DRUG"}
                ],
        } for example in examples]
    
    # Load your own streams from anywhere you want
    stream = load_my_custom_stream(source)
    #stream = list(add_tokens(spacy.blank("en"), stream))
    print(len(stream))
    
    def my_template():
        return '''
            <button type="button" class="collapsible" onclick="dis = document.getElementsByClassName('content')[0]; if (dis.style.display === 'block') {dis.style.display = 'none'} else {dis.style.display = 'block'};">Click to get full context</button>
            <div class="content" style="display: none;text-align:left;">{{{paragraph}}}</div>
        '''
    
    def highlight_para():
        return '''
            <button type="button" class="collapsible" onclick="dis = document.getElementsByClassName('content')[0]; if (dis.style.display === 'block') {dis.style.display = 'none'} else {dis.style.display = 'block'};">Click to get full context</button>
            <textarea rows=15 cols=80 readonly class="content" style="display: none;text-align:left;font-size: large;" onselect="console.log(this);selection = this.value.substring(this.selectionStart, this.selectionEnd);let us = document.getElementById('user_input');us.value = selection;console.log(selection)">{{{paragraph}}}</textarea>
        '''
    
    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "blocks",
        "config": {
            "labels": ["INTERACTION1", "INTERACTION2", "INTERACTION3", "INTERACTION4"],
            "hide_relations_arrow": True,
            "wrap_relations": True,
            "relations_span_labels": ["DRUG", "TRIGGER"],
            "choice_style": "multiple",
            "blocks": [
                {"view_id": "relations"},
                #{"view_id": "html", "html_template": my_template(), },
                {"view_id": "html", "html_template": highlight_para()},
                {"view_id": "text_input", "field_rows": 3, "field_label": "Triggers"},
                {"view_id": "choice", "text": None},
            ]
        }
    }