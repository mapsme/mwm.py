from setuptools import setup
from os import path
from mwm import __version__

here = path.abspath(path.dirname(__file__))

setup(
    name='mwm',
    version=__version__,
    author='Ilya Zverev',
    author_email='ilya@zverev.info',
    packages=['mwm'],
    package_data={'mwm': ['types.txt']},
    url='https://github.com/mapsme/mwm.py',
    license='Apache License 2.0',
    description='Library to read binary MAPS.ME files.',
    long_description=open(path.join(here, 'README.rst')).read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    entry_points={
        'console_scripts': ['mwmtool = mwm.mwmtool:main']
    },
)
