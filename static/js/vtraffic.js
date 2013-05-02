var flot_global_option = { 
		xaxis: { mode: "time", timezone: false, alignTicksWithAxis:true },
		yaxis: { mode: 'time', position: 'left', axisLabel: "{{=T('Travel time')}}", zoomRange: false, panRange: false, },			
		y2axis:{ mode: null},
		series:{ lines: { show: true, fill: true },
				points: { show: true }},
		legend: {show: false},
		pan: { interactive: true },
		zoom: { interactive: true},
		tooltip: true,       //false
		tooltipOpts: {
			content:      "%s |  %x |  %y",
			yDateFormat: "%H:%M:%S",
			defaultTheme:  true     //true
		},
		grid: {
			color: "#444444",
			/*	backgroundColor: "#DDDDDD",*/
			backgroundColor: {
				colors: ["#fff", "#e4f4f4"]
			},
			borderColor: "#FFFFFF",
			tickColor: "#CCCCCC",
			//aboveData: false,
			borderWidth: 1,
			clickable: true,
			hoverable: true,
			autoHighlight: true,
			markings: function(axes) {
				var markings = [];
				var xaxis = axes.xaxis;
				for (var x = Math.floor(xaxis.min); x < xaxis.max; x += xaxis.tickSize * 2) {
					markings.push({ xaxis: { from: x, to: x + xaxis.tickSize }, color: "rgba(232, 232, 255, 0.2)" });
				}
				return markings;
			}
		}
	}


function onDataReceived (json) {
	$('#loading').hide();	
	if ( jQuery.isEmptyObject(json) ) {
		$('#warning').show();
	}
	data = []
	for (var k in json) {
			/*json[k]['label'] = $('#'+k).attr('title') ;*/
			data.push(json[k]);
	}
	datasets = json;

	for (var i in datasets) {
		splits = datasets[i].id.split('_')
		$('#'+splits[0]).append("<li><a id='idJS' title='labelJS' href='#' class=''><span class='legend_box_color'> </span>labelJS</a></li>".replace(/labelJS/g, datasets[i].label ).replace(/idJS/, datasets[i].id ));
	}
	plotAccordingToChoices();
}

function plotAccordingToChoices() {
	if ( jQuery.isEmptyObject(datasets) ) { return; }

	if ( data.length == $(datasets).length ) {
		$("#all").attr('checked', 'checked');
	} 
	var plot = $.plot($(placeholder_h), data, options);
	var dataPlotted = plot.getData();
	for (var d in dataPlotted) {
		$('#' + dataPlotted[d].id).children('span.legend_box_color').css('background-color', dataPlotted[d].color);
	}
}

$(document).on('click', '#all', function() {
	data = [];
	if ( $(this).is (':checked') ) {
		for (key in datasets) {
			$('#' + key).removeClass('muted');
			data.push(datasets[key]);
		}
	} else {
		for (key in datasets) {
			$('#' + key).addClass('muted');
			$('#' + key + ' .legend_box_color').css('background-color', "rgb(204,204,204)");			
		}
	} 
	plotAccordingToChoices();
});


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
