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
	const labels = ["POS1", "POS1T", "POS2", "POS2T", "POS3", "POS3T", "NEG1", "NEG1T", "NEG2", "NEG2T", "NEG3", "NEG3T", "COMB1", "COMB1T", "COMB2", "COMB2T", "COMB3", "COMB3T"];
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
