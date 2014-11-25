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
	this.data = [];	    // All series shown	
	this.colors = [];		// All colors
	this.placeholder;
	this.options;
	this.plot;
    this.n_active_operations = 0;    // Number of ongoing requests

	this.plotAccordingToChoices = function () {
		var tab = this.placeholder.split('_chart')[0];

		if ( jQuery.isEmptyObject(this.data) ) {
			$( tab + ' .label-warning').show();
			$(this.placeholder).parent().hide();
		} else { 
			$( tab + ' .label-warning').hide();
			$(this.placeholder).parent().show();
		}
		if (this.options.crosshair) {
		    this.options.crosshair.mode = this.data.length>1 ? 'x' : null;
	    }

		if ( this.data.length == $(this.datasets).length ) {
			$("#all").attr('checked', 'checked');
		} 
		// Preserve current zoom/pan while plotting new data
        zoomed = {};
        $.extend(zoomed, this.options);
        if (this.plot !== undefined) {
            // Get the current zoom
            var zoom = this.plot.getAxes();
            // Add the zoom to standard options
            zoomed.xaxis.min = zoom.xaxis.min;
            zoomed.xaxis.max = zoom.xaxis.max;
        } else {
            zoomed.xaxis.min = undefined;
            zoomed.xaxis.max = undefined;
        }
		this.plot = $.plot(this.placeholder, this.data, zoomed);
		if ( jQuery.isEmptyObject(this.datasets) ) { return; }
		var dataPlotted = this.plot.getData();

		for (var d in dataPlotted) {
			$("[id='" + dataPlotted[d].id+"']").children('span.legend_box_color').css('background-color', dataPlotted[d].color);
		}
	};

	this.onDataReceived = function (json, url) {
		var tab = this.placeholder.split('_chart')[0];
		var data_placeholder = $(tab + ' .data_list');
		var series = json['series'];


		if (this.options.addDynamically === false) {
			this.data = [];		// Reset data
			this.datasets = [];	
		}
	
		var n = Object.keys(this.datasets).length;
		for (var k in series) {
			current = series[k];
			if ( typeof current.id === 'undefined' ) {
				current.id = k;
			} 
			current['color'] = this.get_color(current.id); //n
			n = n + 1;
			current['url'] = url;
			/*json[k]['label'] = $('#'+k).attr('title') ;*/
			this.data.push(current);
		}

		if (this.options.addDynamically === true) {
			$.merge(this.datasets, series);
		}  else {
			this.datasets = series;
			$(data_placeholder).empty();
			
			for (var i in this.datasets) {
				current = this.datasets[i];
				$(data_placeholder).append( $("<li><a id='" + current.id + "' title='" + current.label + "' href='#' class=''><span class='legend_box_color'> </span>" + current.label + "</a></li>") );
			}
		}
		if ($("a.group").length){
    		interval = $("a.group").attr('id').split('_')[1];
	    	this.options.series.bars.barWidth = 60*60*1000*interval;
	    } 
		this.plotAccordingToChoices();
	};

	this.loadData = function(url) {
	    var that = this;
	    if ((typeof startDate !== "undefined") && (typeof endDate !== "undefined")) {
	        params = {
                from: startDate.valueOf(),
                to: endDate.valueOf(),
	        };
	        url_date = url + "&" + $.param(params);
	    } else {
	        url_date = url;
	    }
        that.n_active_operations = that.n_active_operations + 1;
        $(that.placeholder).trigger($.Event('loading',{}));
		$.ajax({
			url: url_date,
			method: 'GET',
		    dataType: 'json',
		    success: function(json) {
		        that.onDataReceived(json, url)
                that.n_active_operations = that.n_active_operations - 1;
		        if (that.n_active_operations === 0) {
                    $(that.placeholder).trigger($.Event('loaded',{}));
                }
		    },
		    error: function() {
		        that.n_active_operations = that.n_active_operations - 1;
		        if (that.n_active_operations === 0) {
                    $(that.placeholder).trigger($.Event('loaded',{}));
                }
		    },
		});
	};

	this.getData = function () {
		return this.data;
	};

	this.getObj = function (key) {
		var current;
		for (k in this.datasets) {
			current = this.datasets[k];
			if (current.id == key) {
				return current;			
			}
		}
		return undefined;
	};
	
	this.reload_all = function() {
    	this.datasets = [];
        currentData = this.data;
        this.data = [];
		for (key in currentData) {
            this.loadData(currentData[key].url);
		}
	};
	
	this.reset_zoom = function() {
	    this.plot = undefined;
	    this.plotAccordingToChoices();
	};
	
	this.get_color = function(id) {
	    max_color = 0;
	    for (var i in this.colors) {
	        if (this.colors[i].id === id) { // Former color
	            return this.colors[i].color;
	        } else if (this.colors[i].color > max_color) {
	            max_color = this.colors[i].color;
	        }
	    }
        new_element = {'id':id, 'color':max_color+1};
	    this.colors.push(new_element);
	    return new_element.color;
	};
	
	this.options = $.extend(this.default_options, options);
	this.placeholder = ("#" + ph);
	var tab = this.placeholder.split('_chart')[0];

	$(tab).on('click', '.data_list a', $.proxy(function(event) {
    	var element = event.target;
		var key = $(element).attr("id");	
		$(element).toggleClass('muted');	
		var current = this.getObj(key);
		var index = jQuery.inArray(current, this.data);
		if ( index > -1 ) {	// Current element is shown	
			$('#' + key + ' .legend_box_color').css('background-color', "rgb(204,204,204)");
			this.data.splice(index, 1);
		} else {
			this.data.push(current);
		}
		this.plotAccordingToChoices();	
	}, this));

	$(tab).on('click', '[name="all"]', function() {
		this.data = [];
		for (pos in this.datasets) {
			var current = this.datasets[pos];
			var id = current.id;
			if ( $(this).is (':checked') ) {
				$('#' + id).removeClass('muted');
				this.data.push(current);
			} else {
				$('#' + id).addClass('muted');
				$('#' + id + ' .legend_box_color').css('background-color', "rgb(204,204,204)");			
			}
		}
		this.plotAccordingToChoices();
	});



	/*this.init = function(placeholder) {
    };
	this.init();*/
}
