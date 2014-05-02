// Map
jQuery.fn.add_os_map = function() {
	OpenLayers.ImgPath = "static/js/img/";
	var placeHolder = $(this[0]);

	var zoom = 17;
	var lon  = 43.0000;//{{=park['longitude']}};
	var lat  = 11.0000;//{{=park['latitude']}};
	var map = new OpenLayers.Map($(this).attr('id'), {
		projection: "EPSG:900913",
		theme: null,
	});
	var fromProjection = new OpenLayers.Projection("EPSG:4326");   // Transform from WGS 1984
	var toProjection   = new OpenLayers.Projection("EPSG:900913"); // to Spherical Mercator Projection
	var position       = new OpenLayers.LonLat(lon, lat).transform( fromProjection, toProjection);

	// layers
	var layer_osm = new OpenLayers.Layer.OSM();
	var layer_markers = new OpenLayers.Layer.Markers( "Markers" );

	map.addLayer(layer_osm);
	map.addLayer(layer_markers);
	map.setCenter(position, zoom );
	return map;
}

function add_os_marker(layer, lat, lon) {
	var fromProjection = new OpenLayers.Projection("EPSG:4326");   // Transform from WGS 1984
	var toProjection   = new OpenLayers.Projection("EPSG:900913"); // to Spherical Mercator Projection
	var position       = new OpenLayers.LonLat(lon, lat).transform( fromProjection, toProjection);
	m = new OpenLayers.Marker(position);
	layer.addMarker(m);
	return m;
}

function add_after_form(xhr, target) {
    html = $.parseHTML(xhr.responseText, document, true);
    t = $('#' + target );
    t.siblings().remove();
    t.after(html);
    $.web2py.trap_form("", 'select_frontend');
}

function append_to_sidebar(xhr, target) {
    html = $.parseHTML(xhr.responseText, document, true);
    t = $('#' + target);
    t.append(html);
}

    
function onEachFeature (feature, layer) {
    if (feature.properties && feature.properties.popupContent) {
        popupContent = feature.properties.popupContent;
    }

    layer.bindPopup(popupContent);
}


(function ($, undefined) {
	$(document).on('click', '#period a', function(e) {
		e.preventDefault();
		anchor = $('li.active a[data-toggle="tab"]').attr('href');
		url    = $(this).attr('href');
		window.location = url + anchor;
	});
	
})(jQuery);
