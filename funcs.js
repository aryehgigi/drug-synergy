function contextClicked() {
	dis = document.getElementsByClassName('content')[0];
	if (dis.style.display === 'block') {
		dis.style.display = 'none'
	} else {
		dis.style.display = 'block'
	};
}

var button = document.getElementsByClassName("prodigy-button-accept")[0];
button.addEventListener('click', function() {
	window.prodigy.content["radio"] = [];
	const labels = ["POS1", "POS2", "POS3", "NEG1", "NEG2", "NEG3"];
	labels.forEach(label => {
		rbs = document.querySelectorAll('input[name="' + label + '"]');
		for (const rb of rbs) {
			if (rb.checked) {
				window.prodigy.content["radio"].push(label + rb.value);
			}
		}
	})
})

document.addEventListener('prodigyanswer', ev => {
	delete window.prodigy.content["radio"]
	let btns = document.getElementsByClassName('btn_aryeh')
	
	for (const btn of btns) {
		btn.checked = false;
	}
})

// var btns = document.getElementsByClassName('btn_aryeh')[0];
// btns.addEventListener('click', function() {
//	 console.log(this, btn)
//	 if (this.checked === true) {
//		 this.checked = false;
//	 } else {
//		 this.checked = true;
//	 }
// })
