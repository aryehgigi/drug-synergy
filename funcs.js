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
	console.log(window.prodigy.content);
	window.prodigy.update({ 'options': opts });
}