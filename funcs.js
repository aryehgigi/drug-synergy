function contextClicked() {
	dis = document.getElementsByClassName('content')[0];
	if (dis.style.display === 'block') {
		dis.style.display = 'none'
	} else {
		dis.style.display = 'block'
	};
}

function proceed() {
	let opts = [
        {"id": "CONTEXT", "text": "Was the context required?"},
        {"id": "TEMPO", "text": "Did the sentence contain temporal information?"}
    ];
	if ("relations" in window.prodigy.content) {
		console.log(window.prodigy.content["relations"]);
	}
	window.prodigy.update({
		"blocks": [
			{"view_id": "relations"},
			{"view_id": "html", "html_template": my_template(), },
			{"view_id": "html", "html_template": my_template2(), },
			{"view_id": "choice", "text": None, "options": opts},
		]
	});
}