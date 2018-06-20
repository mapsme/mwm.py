# MWM Reader Module
from .mwmfile import MWMFile
from datetime import datetime
import os

# Unprocessed sections: geomN, trgN, idx, sdx (search index),
# addr (search address), offs (feature offsets - succinct)

# TODO:
# - Predictive reading of LineStrings
# - Find why polygon geometry is incorrect in iter_features()


class MWM(MWMFile):
    # indexer/feature_meta.hpp
    metadata = ["0",
                "cuisine", "open_hours", "phone_number", "fax_number", "stars",
                "operator", "url", "website", "internet", "ele",
                "turn_lanes", "turn_lanes_forward", "turn_lanes_backward", "email", "postcode",
                "wikipedia", "maxspeed", "flats", "height", "min_height",
                "denomination", "building_levels", "test_id", "ref:sponsored", "price_rate",
                "rating", "banner_url", "level"]

    regiondata = ["languages", "driving", "timezone", "addr_fmt", "phone_fmt",
                  "postcode_fmt", "holidays", "housenames"]

    def __init__(self, f):
        MWMFile.__init__(self, f)
        self.read_tags()
        self.read_header()
        self.type_mapping = []
        self.read_types(os.path.join(
            os.getcwd(), os.path.dirname(__file__), 'types.txt'))

    def read_types(self, filename):
        if not os.path.exists(filename):
            return
        self.type_mapping = []
        with open(filename, 'r') as ft:
            for line in ft:
                if len(line.strip()) > 0:
                    self.type_mapping.append(line.strip().replace('|', '-'))

    def read_version(self):
        """Reads 'version' section."""
        self.seek_tag('version')
        self.f.read(4)  # skip prolog
        fmt = self.read_varuint() + 1
        version = self.read_varuint()
        if version < 161231:
            vdate = datetime(2000 + int(version / 10000), int(version / 100) % 100, version % 100)
        else:
            vdate = datetime.fromtimestamp(version)
            version = int(vdate.strftime('%y%m%d'))
        return {'fmt': fmt, 'version': version, 'date': vdate}

    def read_header(self):
        """Reads 'header' section."""
        if not self.has_tag('header'):
            # Stub for routing files
            self.coord_size = (1 << 30) - 1
            return {}
        self.seek_tag('header')
        result = {}
        coord_bits = self.read_varuint()
        self.coord_size = (1 << coord_bits) - 1
        self.base_point = self.mwm_bitwise_split(self.read_varuint())
        result['basePoint'] = self.to_4326(self.base_point)
        result['bounds'] = self.read_bounds()
        result['scales'] = self.read_uint_array()
        langs = self.read_uint_array()
        for i in range(len(langs)):
            if i < len(self.languages):
                langs[i] = self.languages[langs[i]]
        result['langs'] = langs
        map_type = self.read_varint()
        if map_type == 0:
            result['mapType'] = 'world'
        elif map_type == 1:
            result['mapType'] = 'worldcoasts'
        elif map_type == 2:
            result['mapType'] = 'country'
        else:
            result['mapType'] = 'unknown: {0}'.format(map_type)
        return result

    # COMPLEX READERS

    def read_region_info(self):
        if not self.has_tag('rgninfo'):
            return {}
        fields = {}
        self.seek_tag('rgninfo')
        sz = self.read_varuint()
        if sz:
            for i in range(sz):
                t = self.read_varuint()
                t = self.regiondata[t] if t < len(self.regiondata) else str(t)
                fields[t] = self.read_string()
                if t == 'languages':
                    fields[t] = [self.languages[ord(x)] for x in fields[t]]
        return fields

    def read_metadata(self):
        """Reads 'meta' and 'metaidx' sections."""
        if not self.has_tag('metaidx'):
            return {}
        # Metadata format is different since v8
        fmt = self.read_version()['fmt']
        # First, read metaidx, to match featureId <-> metadata
        self.seek_tag('metaidx')
        ftid_meta = []
        while self.inside_tag('metaidx'):
            ftid = self.read_uint(4)
            moffs = self.read_uint(4)
            ftid_meta.append((moffs, ftid))
        # Sort ftid_meta array
        ftid_meta.sort(key=lambda x: x[0])
        ftpos = 0
        # Now read metadata
        self.seek_tag('meta')
        metadatar = {}
        while self.inside_tag('meta'):
            tag_pos = self.tag_offset('meta')
            fields = {}
            if fmt >= 8:
                sz = self.read_varuint()
                if sz:
                    for i in range(sz):
                        t = self.read_varuint()
                        t = self.metadata[t] if t < len(self.metadata) else str(t)
                        fields[t] = self.read_string()
                        if t == 'fuel':
                            fields[t] = fields[t].split('\x01')
            else:
                while True:
                    t = self.read_uint(1)
                    is_last = t & 0x80 > 0
                    t = t & 0x7f
                    t = self.metadata[t] if t < len(self.metadata) else str(t)
                    l = self.read_uint(1)
                    fields[t] = self.f.read(l).decode('utf-8')
                    if is_last:
                        break

            if len(fields):
                while ftpos < len(ftid_meta) and ftid_meta[ftpos][0] < tag_pos:
                    ftpos += 1
                if ftpos < len(ftid_meta):
                    if ftid_meta[ftpos][0] == tag_pos:
                        metadatar[ftid_meta[ftpos][1]] = fields
        return metadatar

    def read_crossmwm(self):
        """Reads 'chrysler' section (cross-mwm routing table)."""
        if not self.has_tag('chrysler'):
            return {}
        self.seek_tag('chrysler')
        # Ingoing nodes: array of (nodeId, coord) tuples
        incomingCount = self.read_uint(4)
        incoming = []
        for i in range(incomingCount):
            nodeId = self.read_uint(4)
            point = self.read_coord(False)
            incoming.append((nodeId, point))
        # Outgoing nodes: array of (nodeId, coord, outIndex) tuples
        # outIndex is an index in neighbours array
        outgoingCount = self.read_uint(4)
        outgoing = []
        for i in range(outgoingCount):
            nodeId = self.read_uint(4)
            point = self.read_coord(False)
            outIndex = self.read_uint(1)
            outgoing.append((nodeId, point, outIndex))
        # Adjacency matrix: costs of routes for each (incoming, outgoing) tuple
        matrix = []
        for i in range(incomingCount):
            sub = []
            for j in range(outgoingCount):
                sub.append(self.read_uint(4))
            matrix.append(sub)
        # List of mwms to which leads each outgoing node
        neighboursCount = self.read_uint(4)
        neighbours = []
        for i in range(neighboursCount):
            size = self.read_uint(4)
            neighbours.append(self.f.read(size).decode('utf-8'))
        return {'in': incoming, 'out': outgoing, 'matrix': matrix, 'neighbours': neighbours}

    def iter_features(self, metadata=False):
        """Reads 'dat' section."""
        if not self.has_tag('dat'):
            return
        # TODO: read 'offs'?
        md = {}
        if metadata:
            md = self.read_metadata()
        self.seek_tag('dat')
        ftid = -1
        while self.inside_tag('dat'):
            ftid += 1
            feature = {'id': ftid}
            feature_size = self.read_varuint()
            next_feature = self.f.tell() + feature_size
            feature['size'] = feature_size

            # Header
            header = {}
            header_bits = self.read_uint(1)
            types_count = (header_bits & 0x07) + 1
            has_name = header_bits & 0x08 > 0
            has_layer = header_bits & 0x10 > 0
            has_addinfo = header_bits & 0x80 > 0
            geom_type = header_bits & 0x60
            types = []
            for i in range(types_count):
                type_id = self.read_varuint()
                if type_id < len(self.type_mapping):
                    types.append(self.type_mapping[type_id])
                else:
                    types.append(str(type_id + 1))  # So the numbers match with mapcss-mapping.csv
            header['types'] = types
            if has_name:
                header['name'] = self.read_multilang()
            if has_layer:
                header['layer'] = self.read_uint(1)
            if has_addinfo:
                if geom_type == MWM.GeomType.POINT:
                    header['rank'] = self.read_uint(1)
                elif geom_type == MWM.GeomType.LINE:
                    header['ref'] = self.read_string()
                elif geom_type == MWM.GeomType.AREA or geom_type == MWM.GeomType.POINT_EX:
                    header['house'] = self.read_numeric_string()
            feature['header'] = header

            # Metadata
            if ftid in md:
                feature['metadata'] = md[ftid]

            # Geometry
            geometry = {}
            if geom_type == MWM.GeomType.POINT or geom_type == MWM.GeomType.POINT_EX:
                geometry['type'] = 'Point'
            elif geom_type == MWM.GeomType.LINE:
                geometry['type'] = 'LineString'
            elif geom_type == MWM.GeomType.AREA:
                geometry['type'] = 'Polygon'
            if geom_type == MWM.GeomType.POINT:
                geometry['coordinates'] = list(self.read_coord())

            # (flipping table emoticon)
            feature['geometry'] = geometry
            if False:
                if geom_type != MWM.GeomType.POINT:
                    polygon_count = self.read_varuint()
                    polygons = []
                    for i in range(polygon_count):
                        count = self.read_varuint()
                        buf = self.f.read(count)
                        # TODO: decode
                    geometry['coordinates'] = polygons
                    feature['coastCell'] = self.read_varint()

                # OSM IDs
                count = self.read_varuint()
                osmids = []
                for i in range(count):
                    osmid = self.read_osmid()
                    osmids.append('{0}{1}'.format(osmid[0], osmid[1]))
                feature['osmIds'] = osmids

            if self.f.tell() > next_feature:
                raise Exception('Feature parsing error, read too much')
            yield feature
            self.f.seek(next_feature)
