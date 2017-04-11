# mwm.py

It is a python library to read contents of MAPS.ME mwm files. Not everything
is supported, but you can get at least all the features and their attributes.
We at MAPS.ME use this script to do analytics and maintenance.

## Installation

    pip install mwm

## Usage

Just add `import mwm` to your script, and read an mwm file with:

```python
with open('file.mwm', 'rb') as f:
    data = mwm.MWM(f)
```

## Tools

There are some useful tools in the relevant directory, which can serve as
the library usage examples:

* `dump_mwm.py` prints the header and some statistics on an mwm file.
* `find_feature.py` can find features inside an mwm by type or name.
* `ft2osm.py` converts a feature id to an OSM website link.

## License

Written by Ilya Zverev for MAPS.ME. Published under the Apache License 2.0.
