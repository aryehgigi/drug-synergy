function contextClicked() {
	dis = document.getElementsByClassName('content')[0];
	if (dis.style.display === 'block') {
		dis.style.display = 'none'
	} else {
		dis.style.display = 'block'
	};
}

function proceed() {
    	let opts = []
        let labels = new Set(window.prodigy.content["relations"].map(re => re["label"]));
	labels.forEach((rel) => {opts.push(...[
        	{"id": "CONTEXT" + rel, "text": "Check this if the context was required for relation " + rel + "?"},
        	{"id": "CONTEXTNO" + rel, "text": "Otherwise, Check this if the context wasn't required for relation " + rel},
                {"id": "TEMPO" + rel, "text": "Check this if the sentence contain temporal information relevant for " + rel},
		{"id": "TEMPONO" + rel, "text": "Otherwise, check this if the sentence didn't contain temporal information relevant for " + rel},
	])});
	
	window.prodigy.config["blocks"].push({"view_id": "choice", "text": null, "options": opts})

	window.prodigy.update({
		"config": {"block": window.prodigy.config["blocks"]}
	});
}	
	
document.addEventListener('prodigyanswer', ev => {
	window.prodigy.config["blocks"] = [
                {"view_id": "relations"},
                {"view_id": "html", "html_template": '<button type="button" class="collapsible" onclick="contextClicked()">Click to get full context</button><div class="content" style="display: none;text-align:left;">{{{paragraph}}}</div>', },
                {"view_id": "html", "html_template": '<button type="button" onclick="proceed()">Proceed to choice questions</button>', },
        ]

      	window.prodigy.update({
		"config": {"block": window.prodigy.config["blocks"]}
	});
})

