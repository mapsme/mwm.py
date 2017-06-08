#!/usr/bin/env python
import sys
import os.path
import random
import json
import argparse
from . import MWM, Osm2Ft


def dump_mwm(args):
    mwm = MWM(args.mwm)
    if os.path.exists(args.types):
        mwm.read_types(args.types)

    print('Tags:')
    tvv = sorted([(k, v[0], v[1]) for k, v in mwm.tags.items()], key=lambda x: x[1])
    for tv in tvv:
        print('  {0:<8}: offs {1:9} len {2:8}'.format(tv[0], tv[1], tv[2]))
    v = mwm.read_version()
    print('Format: {0}, version: {1}'.format(v['fmt'], v['date'].strftime('%Y-%m-%d %H:%M')))
    print('Header: {0}'.format(mwm.read_header()))
    print('Region Info: {0}'.format(mwm.read_region_info()))
    print('Metadata count: {0}'.format(len(mwm.read_metadata())))

    cross = mwm.read_crossmwm()
    if cross:
        print('Outgoing points: {0}, incoming: {1}'.format(len(cross['out']), len(cross['in'])))
        print('Outgoing regions: {0}'.format(set(cross['neighbours'])))

    # Print some random features using reservoir sampling
    count = 5
    sample = []
    for i, feature in enumerate(mwm.iter_features()):
        if i < count:
            sample.append(feature)
        elif random.randint(0, i) < count:
            sample[random.randint(0, count-1)] = feature

    print('Feature count: {0}'.format(i))
    print('Sample features:')
    for feature in sample:
        print(json.dumps(feature, ensure_ascii=False))


def find_feature(args):
    mwm = MWM(args.mwm)
    mwm.read_header()
    if os.path.exists(args.types):
        mwm.read_types(args.types)
    if args.iname:
        args.iname = args.iname.lower()

    for i, feature in enumerate(mwm.iter_features(metadata=True)):
        if args.fid and i != args.fid:
            continue
        if args.name or args.iname:
            if 'name' not in feature['header']:
                continue
            found = False
            for value in feature['header']['name'].values():
                if args.name and args.name in value:
                    found = True
                elif args.iname and args.iname in value.lower():
                    found = True
            if not found:
                continue
        if args.type or args.exact_type:
            found = False
            for t in feature['header']['types']:
                if t == args.type or t == args.exact_type:
                    found = True
                elif args.type and args.type in t:
                    found = True
            if not found:
                continue
        if args.meta and ('metadata' not in feature or args.meta not in feature['metadata']):
            continue
        print(json.dumps(feature, ensure_ascii=False, sort_keys=True))


def ft2osm(args):
    ft2osm = Osm2Ft(args.osm2ft, True)
    code = 0
    type_abbr = {'n': 'node', 'w': 'way', 'r': 'relation'}
    for ftid in args.ftid:
        if ftid in ft2osm:
            print('https://www.openstreetmap.org/{}/{}'.format(type_abbr[ft2osm[ftid][0]], ft2osm[ftid][1]))
        else:
            print('Could not find osm id for feature {}'.format(ftid))
            code = 2
    return code


def main():
    parser = argparse.ArgumentParser(description='Toolbox for MWM files.')
    parser.add_argument('--types', default=os.path.join(os.path.dirname(sys.argv[0]), '..', '..', '..', '..', 'data', 'types.txt'), help='path to types.txt')
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True
    parser_dump = subparsers.add_parser('dump', help='Dumps some structures.')
    parser_dump.add_argument('mwm', type=argparse.FileType('rb'), help='file to browse')
    parser_dump.set_defaults(func=dump_mwm)
    parser_find = subparsers.add_parser('find', help='Finds features in a file.')
    parser_find.add_argument('mwm', type=argparse.FileType('rb'), help='file to search')
    parser_find.add_argument('-t', dest='type', help='look inside types ("-t hwtag" will find all hwtags-*)')
    parser_find.add_argument('-et', dest='exact_type', help='look for a type ("-et shop won\'t find shop-chemist)')
    parser_find.add_argument('-n', dest='name', help='look inside names, case-sensitive ("-n Starbucks" for all starbucks)')
    parser_find.add_argument('-in', '-ni', dest='iname', help='look inside names, case-insensitive ("-in star" will find Starbucks)')
    parser_find.add_argument('-m', dest='meta', help='look for a metadata key ("m flats" for features with flats)')
    parser_find.add_argument('-id', dest='fid', type=int, help='look for a feature id ("-id 1234 for feature #1234)')
    parser_find.set_defaults(func=find_feature)
    parser_osm = subparsers.add_parser('osm', help='Displays an OpenStreetMap link for a feature id.')
    parser_osm.add_argument('osm2ft', type=argparse.FileType('rb'), help='.mwm.osm2ft file')
    parser_osm.add_argument('ftid', type=int, nargs='+', help='feature id')
    parser_osm.set_defaults(func=ft2osm)

    args = parser.parse_args()
    code = args.func(args)
    if code is not None:
        sys.exit(code)


if __name__ == '__main__':
    main()
