# MWM Reader Module
import struct
import math


class OsmIdCode(object):
    NODE = 0x4000000000000000
    WAY = 0x8000000000000000
    RELATION = 0xC000000000000000
    RESET = ~(NODE | WAY | RELATION)

    @staticmethod
    def is_node(code):
        return code & OsmIdCode.NODE == OsmIdCode.NODE

    @staticmethod
    def is_way(code):
        return code & OsmIdCode.WAY == OsmIdCode.WAY

    @staticmethod
    def is_relation(code):
        return code & OsmIdCode.RELATION == OsmIdCode.RELATION

    @staticmethod
    def get_type(code):
        if OsmIdCode.is_relation(code):
            return 'r'
        elif OsmIdCode.is_node(code):
            return 'n'
        elif OsmIdCode.is_way(code):
            return 'w'
        return None

    @staticmethod
    def get_id(code):
        return code & OsmIdCode.RESET

    @staticmethod
    def unpack(num):
        if num < 0:
            num = (-1 - num) ^ (2**64 - 1)
        typ = OsmIdCode.get_type(num)
        if typ is None:
            return None
        return typ, OsmIdCode.get_id(num)

    @staticmethod
    def pack(osm_type, osm_id, int64=False):
        if osm_type is None or len(osm_type) == 0:
            return None
        typ = osm_type[0].lower()
        if typ == 'r':
            result = osm_id | OsmIdCode.RELATION
        elif typ == 'w':
            result = osm_id | OsmIdCode.WAY
        elif typ == 'n':
            result = osm_id | OsmIdCode.NODE
        else:
            return None
        if int64 and result >= 2**63:
            result = -1 - (result ^ (2**64 - 1))
        return result


class MWMFile(object):
    # coding/multilang_utf8_string.cpp
    languages = ["default",
                 "en", "ja", "fr", "ko_rm", "ar", "de", "int_name", "ru", "sv", "zh", "fi", "be", "ka", "ko",
                 "he", "nl", "ga", "ja_rm", "el", "it", "es", "zh_pinyin", "th", "cy", "sr", "uk", "ca", "hu",
                 "hsb", "eu", "fa", "br", "pl", "hy", "kn", "sl", "ro", "sq", "am", "fy", "cs", "gd", "sk",
                 "af", "ja_kana", "lb", "pt", "hr", "fur", "vi", "tr", "bg", "eo", "lt", "la", "kk", "gsw",
                 "et", "ku", "mn", "mk", "lv", "hi"]

    def __init__(self, f):
        self.f = f
        self.tags = {}
        self.coord_size = None
        self.base_point = (0, 0)

    def read_tags(self):
        self.f.seek(0)
        self.f.seek(self.read_uint(8))
        cnt = self.read_varuint()
        for i in range(cnt):
            name = self.read_string(plain=True)
            offset = self.read_varuint()
            length = self.read_varuint()
            self.tags[name] = (offset, length)

    def has_tag(self, tag):
        return tag in self.tags and self.tags[tag][1] > 0

    def seek_tag(self, tag):
        self.f.seek(self.tags[tag][0])

    def tag_offset(self, tag):
        return self.f.tell() - self.tags[tag][0]

    def inside_tag(self, tag):
        pos = self.tag_offset(tag)
        return pos >= 0 and pos < self.tags[tag][1]

    def read_uint(self, bytelen=1):
        if bytelen == 1:
            fmt = 'B'
        elif bytelen == 2:
            fmt = 'H'
        elif bytelen == 4:
            fmt = 'I'
        elif bytelen == 8:
            fmt = 'Q'
        else:
            raise Exception('Bytelen {0} is not supported'.format(bytelen))
        res = struct.unpack(fmt, self.f.read(bytelen))
        return res[0]

    def read_varuint(self):
        res = 0
        shift = 0
        more = True
        while more:
            b = self.f.read(1)
            if not b:
                return res
            try:
                bc = ord(b)
            except TypeError:
                bc = b
            res |= (bc & 0x7F) << shift
            shift += 7
            more = bc >= 0x80
        return res

    @staticmethod
    def zigzag_decode(uint):
        res = uint >> 1
        return res if uint & 1 == 0 else -res

    def read_varint(self):
        return self.zigzag_decode(self.read_varuint())

    class GeomType:
        POINT = 0
        LINE = 1 << 5
        AREA = 1 << 6
        POINT_EX = 3 << 5

    @staticmethod
    def unpack_osmid(num):
        typ = OsmIdCode.get_type(num)
        if typ is None:
            return None
        return typ, OsmIdCode.get_id(num)

    def read_osmid(self, as_tuple=True):
        osmid = self.read_uint(8)
        return self.unpack_osmid(osmid) if as_tuple else osmid

    def mwm_unshuffle(self, x):
        x = ((x & 0x22222222) << 1) | ((x >> 1) & 0x22222222) | (x & 0x99999999)
        x = ((x & 0x0C0C0C0C) << 2) | ((x >> 2) & 0x0C0C0C0C) | (x & 0xC3C3C3C3)
        x = ((x & 0x00F000F0) << 4) | ((x >> 4) & 0x00F000F0) | (x & 0xF00FF00F)
        x = ((x & 0x0000FF00) << 8) | ((x >> 8) & 0x0000FF00) | (x & 0xFF0000FF)
        return x

    def mwm_bitwise_split(self, v):
        hi = self.mwm_unshuffle(v >> 32)
        lo = self.mwm_unshuffle(v & 0xFFFFFFFF)
        x = ((hi & 0xFFFF) << 16) | (lo & 0xFFFF)
        y = (hi & 0xFFFF0000) | (lo >> 16)
        return (x, y)

    def mwm_decode_delta(self, v, ref):
        x, y = self.mwm_bitwise_split(v)
        return ref[0] + self.zigzag_decode(x), ref[1] + self.zigzag_decode(y)

    def read_point(self, ref, packed=True):
        """Reads an unsigned point, returns (x, y)."""
        if packed:
            u = self.read_varuint()
        else:
            u = self.read_uint(8)
        return self.mwm_decode_delta(u, ref)

    def to_4326(self, point):
        """Convert a point in maps.me-mercator CS to WGS-84 (EPSG:4326)."""
        if self.coord_size is None:
            raise Exception('Call read_header() first.')
        merc_bounds = (-180.0, -180.0, 180.0, 180.0)  # Xmin, Ymin, Xmax, Ymax
        x = point[0] * (merc_bounds[2] - merc_bounds[0]) / self.coord_size + merc_bounds[0]
        y = point[1] * (merc_bounds[3] - merc_bounds[1]) / self.coord_size + merc_bounds[1]
        y = 360.0 * math.atan(math.tanh(y * math.pi / 360.0)) / math.pi
        return (x, y)

    def read_coord(self, packed=True):
        """Reads a pair of coords in degrees mercator, returns (lon, lat)."""
        point = self.read_point(self.base_point, packed)
        return self.to_4326(point)

    def read_bounds(self):
        """Reads mercator bounds, returns (min_lon, min_lat, max_lon, max_lat)."""
        rmin = self.mwm_bitwise_split(self.read_varint())
        rmax = self.mwm_bitwise_split(self.read_varint())
        pmin = self.to_4326(rmin)
        pmax = self.to_4326(rmax)
        return (pmin[0], pmin[1], pmax[0], pmax[1])

    def read_string(self, plain=False, decode=True):
        length = self.read_varuint() + (0 if plain else 1)
        s = self.f.read(length)
        return s.decode('utf-8') if decode else s

    def read_uint_array(self):
        length = self.read_varuint()
        result = []
        for i in range(length):
            result.append(self.read_varuint())
        return result

    def read_numeric_string(self):
        sz = self.read_varuint()
        if sz & 1 != 0:
            return str(sz >> 1)
        sz = (sz >> 1) + 1
        return self.f.read(sz).decode('utf-8')

    def read_multilang(self):
        def find_multilang_next(s, i):
            i += 1
            while i < len(s):
                try:
                    c = ord(s[i])
                except:
                    c = s[i]
                if c & 0xC0 == 0x80:
                    break
                if c & 0x80 == 0:
                    pass
                elif c & 0xFE == 0xFE:
                    i += 6
                elif c & 0xFC == 0xFC:
                    i += 5
                elif c & 0xF8 == 0xF8:
                    i += 4
                elif c & 0xF0 == 0xF0:
                    i += 3
                elif c & 0xE0 == 0xE0:
                    i += 2
                elif c & 0xC0 == 0xC0:
                    i += 1
                i += 1
            return i

        s = self.read_string(decode=False)
        langs = {}
        i = 0
        while i < len(s):
            n = find_multilang_next(s, i)
            try:
                lng = ord(s[i]) & 0x3F
            except TypeError:
                lng = s[i] & 0x3F
            if lng < len(self.languages):
                langs[self.languages[lng]] = s[i+1:n].decode('utf-8')
            i = n
        return langs
