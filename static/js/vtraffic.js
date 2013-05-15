function lplot (ph, options) {
	
	this.default_options = { 
		xaxis: { mode: "time", timezone: false, alignTicksWithAxis:true },
		yaxis: { mode: 'time', position: 'left', zoomRange: false, panRange: false, },			
		y2axis:{ mode: null},
		series:{ lines: { show: true, fill: true },
				 points: { show: true },
				 bars: {show: false}},
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
		},
		addDynamically: false,
	};

	this.datasets = [];	// All series available
	this.data = [];		// All series shown	
	this.placeholder;
	this.options;
	var addDynamically;

	this.plotAccordingToChoices = function () {
		var tab = thatClass.placeholder.split('_chart')[0];
		$('#loading').hide(); $('body').css("cursor", "auto");		

		if ( jQuery.isEmptyObject(thatClass.data) ) {
			$( tab + ' .label-warning').show();
			$(thatClass.placeholder).parent().hide();
		} else { 
			$( tab + ' .label-warning').hide();
			$(thatClass.placeholder).parent().show();
		}
		//options.crosshair.mode = data.length>1 ? 'x' : null;

		if ( thatClass.data.length == $(thatClass.datasets).length ) {
			$("#all").attr('checked', 'checked');
		} 

		var plot = $.plot(thatClass.placeholder, thatClass.data, thatClass.options);
		if ( jQuery.isEmptyObject(thatClass.datasets) ) { return; }
		var dataPlotted = plot.getData();

		for (var d in dataPlotted) {
			$('#' + dataPlotted[d].id).children('span.legend_box_color').css('background-color', dataPlotted[d].color);
		}
	};

	this.onDataReceived = function (json) {
		var tab = thatClass.placeholder.split('_chart')[0];
		var data_placeholder = $(tab + ' .data_list');
		var series = json['series'];


		if (thatClass.options.addDynamically === false) {
			thatClass.data = [];		// Reset data
			thatClass.datasets = [];	
		}
	
		var n = Object.keys(thatClass.datasets).length;
		for (var k in series) {
			current = series[k];
			if ( typeof current.id === 'undefined' ) {
				current.id = k;
			} 
			current['color'] = n;
			n = n + 1;
			/*json[k]['label'] = $('#'+k).attr('title') ;*/
			thatClass.data.push(current);
		}

		if (thatClass.options.addDynamically === true) {	
			$.merge(thatClass.datasets, series);
		}  else {
			thatClass.datasets = series;
			$(data_placeholder).empty();
			
			for (var i in thatClass.datasets) {
				current = thatClass.datasets[i];
				$(data_placeholder).append( $("<li><a id='idJS' title='labelJS' href='#' class=''><span class='legend_box_color'> </span>labelJS</a></li>".replace(/labelJS/g, current.label ).replace(/idJS/, current.id)) );
			}
		}
		interval = $("li.active a[class='group']").attr('id').split('_')[1];
		thatClass.options.series.bars.barWidth = 60*60*1000*interval;
		thatClass.plotAccordingToChoices();
	};

	this.loadData = function(url) {
		$('#loading').show();
		$('body').css("cursor", "progress");
		$.ajax({
			url: url,
			method: 'GET',
		    dataType: 'json',
		    success: thatClass.onDataReceived
		});
	};

	this.getData = function () {
		return thatClass.data;
	};

	this.getObj = function (key) {
		var current;
		for (k in thatClass.datasets) {
			current = thatClass.datasets[k];
			if (current.id == key) {
				return current;			
			}
		}
		return undefined;
	};
	
	this.options = $.extend(this.default_options, options);
	this.placeholder = ("#" + ph);
	var thatClass = this;
	var tab = this.placeholder.split('_chart')[0];

	$(tab).on('click', '.data_list a', function() {
		var key = $(this).attr("id");	
		$(this).toggleClass('muted');	
		var current = thatClass.getObj(key);
		var index = jQuery.inArray(current, thatClass.data);
		if ( index > -1 ) {	// Current element is shown	
			$('#' + key + ' .legend_box_color').css('background-color', "rgb(204,204,204)");
			thatClass.data.splice(index, 1);
		} else {
			thatClass.data.push(current);
		}
		thatClass.plotAccordingToChoices();	
	});

	$(tab).on('click', '[name="all"]', function() {
		thatClass.data = [];
		for (pos in thatClass.datasets) {
			var current = thatClass.datasets[pos];
			var id = current.id;
			if ( $(this).is (':checked') ) {
				$('#' + id).removeClass('muted');
				thatClass.data.push(current);
			} else {
				$('#' + id).addClass('muted');
				$('#' + id + ' .legend_box_color').css('background-color', "rgb(204,204,204)");			
			}
		}
		thatClass.plotAccordingToChoices();
	});



	/*this.init = function(placeholder) {
    };
	this.init();*/
}
