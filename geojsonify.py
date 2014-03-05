#!/usr/bin/env python
"""
geojsonify
Given a JSON file with a simple list of points, convert to a GeoJSON file.  Assumes WGS84 datum, optionally supports factorial lat/long (like Google Maps API).
Copyright 2014 Michael Farrell <http://micolous.id.au>

License: 3-clause BSD, see COPYING
"""

# Require simplejson for Decimal serialisation.
import geojson, geojson.crs, argparse, simplejson, io, sys, uuid
from decimal import Decimal

def geojsonifyme(input_f, output_f):
	input_obj = simplejson.load(input_f, use_decimal=True)
	output_layer = geojson.FeatureCollection([])
	# assume WGS84 CRS
	output_layer.crs = geojson.crs.Named('urn:ogc:def:crs:OGC:1.3:CRS84')
	
	# load what the fields in this array are
	first_keys = set(input_obj[0].keys())
	
	# find a lat value
	id_key = lat_key = long_key = None
	for k in first_keys:
		if lat_key is None and k.startswith('lat'):
			lat_key = k
		elif long_key is None and (k.startswith('lon') or k.startswith('lng')):
			long_key = k
		elif id_key is None and (k.startswith('id') or k.startswith('uuid') or k.startswith('guid')):
			id_key = k
		if lat_key is not None and long_key is not None and id_key is not None:
			# we're done, drop out now
			break
	
	if lat_key is None:
		raise ValueError, 'Could not guess key with latitude'
	if long_key is None:
		raise ValueError, 'Could not guess key with longitude'
	if id_key is None:
		print >> sys.stderr, "Warning: `id` field not found in source file. Will generate GUIDs automatically instead."

	# we have some candidates, lets find out if they're raw or factorial
	lat_factor = long_factor = 1
	if 'E' in lat_key:
		# this is a factorial, parse it
		lat_factor = lat_key.split('E', 2)[1]
		lat_factor = 10 ** int(lat_factor)

	if 'E' in long_key:
		# this is a factorial, parse it
		long_factor = lat_key.split('E', 2)[1]
		long_factor = 10 ** int(long_factor)

	# we have some factors, lets parse the rest of this stuff
	for point in input_obj:
		# get properties without latlong
		props = dict(point)
		del props[lat_key]
		del props[long_key]

		if id_key is None:
			# no ID field, make up a UUID
			id = str(uuid.uuid4())
			# It's a UUID so mark as such
			props['uuid'] = id
		else:
			# there is an ID field
			id = props[id_key]
			# Don't strip this field and instead include it twice
			# as some programs don't read from this ID field.
			

		output_layer.features.append(geojson.Feature(
			geometry=geojson.Point(
				coordinates=(
					(Decimal(point[long_key]) / long_factor),
					(Decimal(point[lat_key]) / lat_factor)
				)
			),
			properties=props,
			id=id
		))

	# now serialise this data
	geojson.dump(output_layer, output_f)


def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('input', nargs=1, help='Input JSON file')
	parser.add_argument('-o', '--output', required=True, type=argparse.FileType('wb'), help='Output GeoJSON file')

	options = parser.parse_args()

	# Files written by Windows sometimes have Unicode BOMs which
	# cause parse failures
	input_f = io.open(options.input[0], 'r', encoding='utf-8-sig')

	# We don't care so much about the encoding output, we always
	# use utf-8 with no BOM.
	geojsonifyme(input_f, options.output)


if __name__ == '__main__':
	main()