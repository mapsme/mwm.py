mwm.py
======

It is a python library to read contents of MAPS.ME mwm files. Not
everything is supported, but you can get at least all the features and
their attributes. We at MAPS.ME use this script to do analytics and
maintenance.

Installation
------------

::

    pip install mwm

Usage
-----

Just add ``import mwm`` to your script, and read an mwm file with:

.. code:: python

    with open('file.mwm', 'rb') as f:
        data = mwm.MWM(f)

Tools
-----

The package installs the ``mwmtool`` command-line script. It shows
statistics about an MWM file, can search for features or convert ids.
Run it with ``-h`` to see a list of options.

The script source can serve as a library usage example.

License
-------

Written by Ilya Zverev for MAPS.ME. Published under the Apache License
2.0.