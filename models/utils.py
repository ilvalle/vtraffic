openstreatmap_static_link="http://ojw.dev.openstreetmap.org/StaticMap/?lat=%(lat)s&lon=%(lon)s&mlat0=%(lat)s&att=none&mlon0=%(lon)s&z=%(zoom)s&h=%(height)s&w=%(width)s&layer=mapnik&mode=Export&show=1"

def get_static_img(lat, lon, width='150', height='150', zoom=15):
	if not(lat and lon): return ''
	url = openstreatmap_static_link % {'lon':lon, 'lat':lat, 'height':150, 'width':width, 'zoom':zoom}
	return str(IMG(_src=url))
