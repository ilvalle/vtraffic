// Map
jQuery.fn.add_os_map = function() {
	var placeHolder = $(this[0]);

	var zoom = 17;
	var lon  = 43.0000;//{{=park['longitude']}};
	var lat  = 11.0000;//{{=park['latitude']}};
	var map = new OpenLayers.Map($(this).attr('id'), {
		projection: "EPSG:900913",
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
