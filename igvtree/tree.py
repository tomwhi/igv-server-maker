from collections import defaultdict
import functools


class TreeLevel:
    def __init__(self, name, regexs):
        '''
        name: Descriptive name of this tree level
        regexs: Regular expressions used to define nodes at this tree level,
            when given a set of input filenames
        attrs: Dictionary of string->string attribute names and values, providing
            features associated with this tree level; e.g. to be used in styling
            leaf nodes under this tree level.
        '''
        self.name = name
        self.regexs = regexs
        self.node_value_to_filenames = defaultdict(set)
        self.filename_to_node_value = defaultdict(set)

    def assign_filename(self, filename):
        '''
        Apply each regex for this tree level to the filename.

        Record the match information as follows:
        - No match -> Store under "NoMatch" node
        - Single value in regexs -> Store under value of the string matching the regex
        - Multiple values in regexs -> Store under the matching regex itself
        '''

        found_match = False
        for regex in self.regexs:
            match = regex.search(filename)
            if match != None:
                found_match = True
                matching_nodename = match.group()
                if len(self.regexs) > 1:
                    # More than one regexs are explicitly stated for this
                    # tree level => Each regex will be a separate node, rather
                    # than each match being a separate node:
                    matching_nodename = regex.pattern
                self.node_value_to_filenames[matching_nodename].add(filename)
                assert filename not in self.filename_to_node_value
                self.filename_to_node_value[filename] = matching_nodename

        if not found_match:
            self.node_value_to_filenames["NoMatch"].add(filename)
            self.filename_to_node_value[filename] = "NoMatch"


class FilenamesNode:
    def __init__(self, name, parent, filename=None, attrs=[]):
        self.name = name
        self.parent = parent
        self.childname_to_child = {}
        # Attributes of this node
        self.attrs = attrs
        # Filename should only be set for leaf nodes:
        self.filename = filename

    def print_text(self, indent):
        '''
        Print a text representation of this node and it's children (recursively) to
        stdout, with the specified indentation level.
        '''
        print("  " * indent + self.name)
        for child in self.childname_to_child.values():
            child.print_text(indent + 1)
        if self.filename:
            print("  " * (indent + 1) + self.filename.split("/")[-1])

    def get_ancestors(self):
        if self.parent == None:
            return []
        else:
            return [self.parent] + self.parent.get_ancestors()

    # FIXME: Probably refactor to at least use XML ElementTree
    def print_xml(self, indent):

        total_indent = ("  " * indent)
        if len(self.childname_to_child) > 0:
            if self.parent == None:
                print("<Global name=\"%s\">" % self.name)
            else:
                print("%s<Category name=\"%s\">" % (total_indent, self.name))
            for child in self.childname_to_child.values():
                child.print_xml(indent + 1)
            if self.parent == None:
                print("</Global>")
            else:
                print("%s</Category>" % (total_indent))
            assert self.filename == None
        else:
            assert self.filename != None
            # Condense attribute lists of this node and all parents into a single set:
            attr_lists = [node.attrs for node in [self] + self.get_ancestors()]
            combined_attrs = set(functools.reduce(lambda l1, l2: l1 + l2, attr_lists))
            attr_string = " ".join(combined_attrs)
            print("%s<Resource name=\"%s\" %s>" % (total_indent, self.name, attr_string))
            print("%spath=\"%s\">" % (("  " * (indent + 1)), self.filename))
            print("%s</Resource>" % (total_indent))


class FilenamesTree:
    def __init__(self, root_name, tree_levels):
        self.root = FilenamesNode(root_name, None)
        self.levels = tree_levels

    def insert_filename(self, filename, node_attrs):
        curr_node = self.root
        for level_name, tree_level in self.levels.items():
            selected_child_name = tree_level.filename_to_node_value[filename]
            selected_child = None

            # Retrieve or create + register a child node for this filename at this
            # tree level:
            if selected_child_name in curr_node.childname_to_child:
                selected_child = curr_node.childname_to_child[selected_child_name]
            else:
                child_node_attrs = []
                if selected_child_name in node_attrs:
                    child_node_attrs = node_attrs[selected_child_name]
                selected_child = FilenamesNode(selected_child_name, curr_node, attrs=child_node_attrs)
                curr_node.childname_to_child[selected_child_name] = selected_child
            curr_node = selected_child
        curr_node.filename = filename

    def print_text(self):
        indent = 0
        self.root.print_text(indent)

    # FIXME: Perhaps need to refactor this for better separation of concerns.
    def print_xml(self):
        print('<?xml version="1.0" encoding="UTF-8"?>')
        indent = 0
        self.root.print_xml(indent)
