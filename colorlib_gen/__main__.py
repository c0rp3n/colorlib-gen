#! /usr/bin/env python3

import argparse
import os

import yaml

from jinja2 import Environment, PackageLoader
from colorlib_gen.char_group import CharGroup
from colorlib_gen.defs import DEFAULT_COLOR, ENGINE_COLORS, TARGETS

COLORS = []
COLOR_ENUM_NAMES = {}
ENUM_NAME = ''
FUNCTION_NAME = ''
TERMINATOR_CHAR = 0

def get_hex(i : int, n : int = 2) -> str:
    """Returns a hex representation of a char."""

    return '0x' + '{:0{}x}'.format(i, n).upper()

def group_till_unique(in_group : list, i : int = 0) -> dict:
    """
    Recursively splits a list into a tree,
    where each node is a char in the leafs.
    """

    groups = {}
    for (key, group) in group_by_char_at(in_group, i).items():
        if isinstance(group, list):
            groups[key] = group_till_unique(group, i + 1)
        else:
            groups[key] = group

    return groups

def group_by_char_at(colors : list, i : int = 0) -> dict:
    """
    Returns a dictionary of strings from a list,
    grouped by the char at \'i\'.
    """

    # construnct a dictionary of strings
    # examples:
    # colors = ['default', 'darkred', 'red']
    # group_by_char_at(colors, 0)
    # { 'd': ['default', 'darkred'], 'r': ['red'] }
    #
    # colors = ['grey', 'grey2']
    # group_by_char_at(colors, 4)
    # { 0: ['grey'], '2': ['grey2'] }

    groups = {}
    for color in colors:
        if len(color) == i:
            # index greater than length of string so use null terminator
            groups[TERMINATOR_CHAR] = color
        elif color[i] in groups:
            if isinstance(groups[color[i]], list):
                groups[color[i]].append(color)
            else:
                groups[color[i]] = [groups[color[i]], color]
        else:
            groups[color[i]] = color

    return groups

def skip_redundant_decisions(group : dict, depth : int = 0):
    """Optimisation step which skips redundant decisions."""

    # FROM:
    # 't':
    # {
    #     'e':
    #     {
    #         'a':
    #         {
    #             'm':
    #             {
    #                 ' ':
    #                 {
    #                     '0': ['team 0'],
    #                     '1': ['team 1'],
    #                     '2': ['team 2']
    #                 },
    #                 'c': ['teamcolor']
    #             }
    #         }
    #     }
    # }
    # TO:
    # (0)
    # 't':
    # {   (4)
    #     ' ':
    #     {
    #         (5)
    #         '0': ['team 0'],
    #         '1': ['team 1'],
    #         '2': ['team 2']
    #     },
    #     'c': ['teamcolor']
    # }

    if isinstance(group, dict):
        if len(group) == 1:
            for (_, value) in group.items():
                char_group = skip_redundant_decisions(value, depth + 1)
        else:
            new_group = {}
            for (key, value) in group.items():
                new_group[key] = skip_redundant_decisions(value, depth + 1)

            char_group = CharGroup(depth, new_group)
    else:
        char_group = group

    return char_group

def to_decisions(group : CharGroup) -> list:
    """Converts the char groups into a list of recursive tuples for Jinja2."""

    tuples = []
    for (key, value) in group.children.items():
        if isinstance(value, CharGroup):
            t = (group.depth, key, 0, to_decisions(value))
        else:
            length = len(value) + 1 # length of color code + terminator
            t = (group.depth, key, length, COLOR_ENUM_NAMES[value])

        tuples.append(t)

    return tuples

def get_enums() -> list:
    """Creates the enum values for the color codes of the mapping function."""

    enums = []
    for color in COLORS:
        name = color[0].replace(' ', '_').capitalize()
        value = get_hex(color[1])
        COLOR_ENUM_NAMES[color[0]] = name
        enums.append((name, value))

    return enums

def get_decisions() -> list:
    """Creates the list of decisions for the mapping function."""

    groups = group_till_unique([c[0] for c in COLORS])
    groups = skip_redundant_decisions(groups)
    groups.sort()

    return to_decisions(groups)

def parse_config(file, include_ref_colors : bool):
    """Parses ColorGen's the YAML config file."""

    cfg = yaml.load(file, Loader=yaml.Loader)

    if 'enum_name' in cfg:
        global ENUM_NAME
        ENUM_NAME = cfg['enum_name']

    if 'function_name' in cfg:
        global FUNCTION_NAME
        FUNCTION_NAME = cfg['function_name']

    if 'terminator' in cfg:
        global TERMINATOR_CHAR
        TERMINATOR_CHAR = cfg['terminator']

    ref_colors = {}
    if 'ref_colors' in cfg:
        for (key, value) in cfg['ref_colors'].items():
            if isinstance(value, int):
                ref_colors[key] = value
            else:
                assert value not in COLORS, 'value is not a default engine color or integer value' 
                ref_colors[key] = COLORS[value]

    for (key, value) in cfg['colors'].items():
        if isinstance(value, int):
            COLORS.append((key, value))
        else:
            if value in ref_colors:
                COLORS.append((key, ref_colors[value]))
            elif value in ENGINE_COLORS:
                COLORS.append((key, ENGINE_COLORS[value]))
    
    if include_ref_colors:
        for (key, value) in ref_colors.items():
            COLORS.append((key, value))

def add_default_colors():
    """Add the default engine colors."""

    for (key, value) in ENGINE_COLORS.items():
            COLORS.append((key, value))

def main():
    parser = argparse.ArgumentParser(description='ColorLib color map creator.')
    parser.add_argument(
        '-e',
        '--include-engine-colors',
        action="store_true",
        dest='include_engine_colors'
        )
    parser.add_argument(
        '-r',
        '--include-ref-colors',
        action="store_true",
        dest='include_ref_colors'
        )
    parser.add_argument(
        '--target',
        dest='target',
        default='sourcepawn',
        choices=['cpp', 'sourcepawn', 'python']
        )
    parser.add_argument(
        '--enum-name',
        dest='enum_name',
        default=None
        )
    parser.add_argument(
        '--function-name',
        dest='function_name',
        default=None
        )
    parser.add_argument(
        '--terminator',
        dest='terminator_char',
        default=None
    )
    parser.add_argument(
        '--config',
        dest='config',
        type=argparse.FileType('r', encoding='UTF-8'),
        help='config path \'{path to config dir}/color_conf.yaml\''
        )
    parser.add_argument(
        'out',
        type=argparse.FileType('w', encoding='UTF-8'),
        help='output path \'{path to include dir}/colorlib_map.inc\''
        )

    args = parser.parse_args()

    if args.config != None:
        parse_config(args.config, args.include_ref_colors)
    else:
        COLORS.append(DEFAULT_COLOR)
    
    if args.include_engine_colors or args.config is not None:
        add_default_colors()

    if args.enum_name is not None:
        global ENUM_NAME
        ENUM_NAME = args.enum_name

    if ENUM_NAME == '':
        print('colorlib_gen: no enum name was given')
        exit()

    if args.function_name is not None:
        global FUNCTION_NAME
        FUNCTION_NAME = args.function_name

    if FUNCTION_NAME == '':
        print('colorlib_gen: no function name was given')
        exit()

    if args.terminator_char is not None:
        global TERMINATOR_CHAR
        TERMINATOR_CHAR = args.terminator_char

    enums = get_enums()
    decisions = get_decisions()

    env = Environment(loader=PackageLoader('colorlib_gen', 'templates'),
                      keep_trailing_newline=True)
    template = env.get_template(TARGETS[args.target])

    file_name = os.path.splitext(os.path.basename(args.out.name))[0]
    args.out.write(template.render(file_name=file_name,
                                   enum_name=ENUM_NAME,
                                   function_name=FUNCTION_NAME,
                                   colors=enums,
                                   decisions=decisions))
    args.out.close()

if __name__ == '__main__':
    main()
