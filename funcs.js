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
	console.log("here1", window.prodigy.content)
	window.prodigy.content["radio"] = [];
	const labels = ["SYN1", "SYN1T", "SYN2", "SYN2T", "SYN3", "SYN3T", "ANT1", "ANT1T", "ANT2", "ANT2T", "ANT3", "ANT3T", "UNK1", "UNK1T", "UNK2", "UNK2T", "UNK3", "UNK3T"];
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
	console.log("here2", window.prodigy.content)
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
