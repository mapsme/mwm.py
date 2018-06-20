# mwm.py Change Log

## master branch

## 0.10.1

_Released 2018-06-20_

* Better support for Python 2.7.
* Encoding and decoding int64 negative ids.
* Allow short form for id: `mwmtool id way/123456`.

## 0.10.0

_Released 2018-06-18_

* Extracted osm id encoding methods to `OsmIdCode` class.
* Added id decoding to mwmtool.
* Fixed printing utf-8 characters under Python 2 in mwmtool.
* Python 2.6 is not supported officially.
* Package `types.txt` to eliminate the need to check out omim repository.
* `dump -s` will skip reading all the features.

## 0.9.0

_Released 2017-06-08_

The initial release with some features.
