function onDataReceived (json) {
	$('#loading').hide();
	datasets = json
	data = []
	for (var i in datasets) {
		splits = datasets[i].id.split('_')
		$('#'+splits[0]).append("<li><label class='checkbox'><input id='idJS' type='checkbox'>labelJS</label></li>".replace(/labelJS/, datasets[i].label ).replace(/idJS/, datasets[i].id ));
	}
	plotAccordingToChoices();
}

