# OSM2FT Reader
from .mwmfile import MWMFile


class Osm2Ft(MWMFile):
    def __init__(self, f, ft2osm=False, tuples=True):
        MWMFile.__init__(self, f)
        self.read(ft2osm, tuples)

    def read(self, ft2osm=False, tuples=True):
        """Reads mwm.osm2ft file, returning a dict of feature id <-> osm way id."""
        count = self.read_varuint()
        self.data = {}
        self.ft2osm = ft2osm
        for i in range(count):
            osmid = self.read_osmid(tuples)
            fid = self.read_uint(4)
            self.read_uint(4)  # filler
            if osmid is not None:
                if ft2osm:
                    self.data[fid] = osmid
                else:
                    self.data[osmid] = fid

    def __getitem__(self, k):
        return self.data.get(k)

    def __repr__(self):
        return '{} with {} items'.format('ft2osm' if self.ft2osm else 'osm2ft', len(self.data))

    def __len__(self):
        return len(self.data)

    def __contains__(self, k):
        return k in self.data

    def __iter__(self):
        return iter(self.data)
