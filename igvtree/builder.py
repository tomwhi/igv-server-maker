import json, logging, os, re
import click
from igvtree.tree import TreeLevel, FilenamesTree


def define_tree_levels(rules):
    return {level_name: TreeLevel(level_name, node_mappings)
            for level_name, node_mappings in rules.items()}


@click.command()
@click.option('--loglevel', default='INFO', help='level of logging')
@click.option('--name', default='Base', help='Base name for the XML tree')
@click.argument('file-list', type=click.File('r'))
@click.argument('rules-json', type=click.File('r'))
@click.argument('node-attrs-json', type=click.File('r'))
def build_tree(loglevel, file_list, rules_json, node_attrs_json, name):
    setup_logging(loglevel)

    filenames = [line.strip() for line in file_list]

    rule_dict = json.load(rules_json)

    node_attrs = json.load(node_attrs_json)

    tree_levels = define_tree_levels(rule_dict)

    # Record which node values map to which filenames and vice-versa, for each node level...
    for level_name, tree_level in tree_levels.items():
        for filename in filenames:
            tree_level.assign_filename(filename)

    filenames_tree = FilenamesTree(name, tree_levels)
    for filename in filenames:
        filenames_tree.insert_filename(filename, node_attrs)

    filenames_tree.print_xml()


def setup_logging(loglevel="INFO"):
    """
    Set up logging
    :param loglevel: loglevel to use, one of ERROR, WARNING, DEBUG, INFO (default INFO)
    :return:
    """
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level,
                        format='%(levelname)s %(asctime)s %(funcName)s - %(message)s')
    logging.debug("Started log with loglevel %(loglevel)s" % {"loglevel": loglevel})


@click.command()
@click.option('--loglevel', default='INFO', help='level of logging')
@click.option('--basedir', default='/scratch/tmp/thowhi/liqbio_full_pipeline_tests',
              help='LIQBIO autoseq output folder, containing outputs for various patient SDIDs.')
@click.argument('pattern-list-file', type=click.File('r'))
@click.argument('output_filename', type=click.Path())
def list_files_eg(loglevel, basedir, pattern_list_file, output_filename):
    setup_logging(loglevel)

    pattern_list = [line.strip() for line in pattern_list_file.readlines()]
    with open(output_filename, 'w') as output_file:
        for root, dirs, files in os.walk(basedir):
            for contained_file in files:
                for pattern in pattern_list:
                    path = os.path.join(root, contained_file)
                    if re.search(pattern, path):
                        print(path, file=output_file)