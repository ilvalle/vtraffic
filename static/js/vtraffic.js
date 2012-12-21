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

/*function showTooltip(x, y, contents) {
	$('<div id="tooltip">' + contents + '</div>').css( {
	    position: 'absolute',
	    display: 'none',
	    top: y + 5,
	    left: x + 5,
	    border: '1px solid #fdd',
	    padding: '2px',
	    'background-color': '#fee',
	    opacity: 0.80
	}).appendTo("body").fadeIn(200);
}*/
