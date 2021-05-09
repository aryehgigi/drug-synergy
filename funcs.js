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
	window.prodigy.content["relations"].forEach((re) => {let rel = re['label']; opts.push(...[
        	{"id": "CONTEXT" + rel, "text": "Check this if the context was required for relation " + rel + "?"},
        	{"id": "CONTEXTNO" + rel, "text": "Otherwise, Check this if the context wasn't required for relation " + rel},
                {"id": "TEMPO" + rel, "text": "Check this if the sentence contain temporal information relevant for " + rel},
		{"id": "TEMPONO" + rel, "text": "Otherwise, check this if the sentence didn't contain temporal information relevant for " + rel},
	])});
	if ("relations" in window.prodigy.content) {
		console.log(window.prodigy.content["relations"][0]["label"]);
	}
	window.prodigy.config["blocks"].push({"view_id": "choice", "text": null, "options": opts})

	window.prodigy.update({
		"config": {"block": window.prodigy.config["blocks"]}
	});
}
