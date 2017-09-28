from collections import defaultdict
import functools, ntpath, re


class TreeLevel:
    def __init__(self, name, node_mappings):
        """
        name: Descriptive name of this tree level
        node_mappings: Dictionary of regex string -> node name mapping
        """
        self.name = name
        self.node_mappings = node_mappings
        self.node_value_to_filenames = defaultdict(set)
        self.filename_to_node_value = defaultdict(set)

    def assign_filename(self, filename):
        """
        Apply each regex for this tree level to the filename, and thereby
        assign the filename to a single node (only by node name at this stage),
        at this tree level.

        Assigns the filename to a node as follows:
        - No match -> Assigns to a "NoMatch" node
        - Single regex provided for this tree level -> Store under value of the
            string matching the regex
        - Multiple regexs provided for this tree level -> Store under the matching
            regex itself
        """

        found_match = False
        for regex_str in self.node_mappings.keys():
            # Retrieve the node name corresponding to current regex string:
            node_name = self.node_mappings[regex_str]

            # Determine if the filename matches the current regex:
            regex = re.compile(regex_str)
            match = regex.search(filename)
            if match != None:
                found_match = True
                matching_nodename = match.group()
                if node_name != None:
                    # A node name is specifically stated for this regex =>
                    # Use that node name for this match, rather than each
                    # match being a separate node:
                    matching_nodename = node_name

                # Record the fact that the matching node (identified by name)
                # will include this filename (potentially in addition to other
                # filenames), and that this filename will belong to that matching
                # node (and no other) at this level of the tree:
                self.node_value_to_filenames[matching_nodename].add(filename)
                self.filename_to_node_value[filename] = matching_nodename

        if not found_match:
            self.node_value_to_filenames["NoMatch"].add(filename)
            self.filename_to_node_value[filename] = "NoMatch"


class FilenamesNode:
    def __init__(self, name, parent, attrs=[]):
        self.name = name
        self.parent = parent
        self.childname_to_child = {}
        # Attributes of this node
        self.attrs = attrs
        # Filename should only be set for leaf nodes:
        self.filenames = []

    def print_text(self, indent):
        """
        Print a text representation of this node and it's children (recursively) to
        stdout, with the specified indentation level.
        """
        print("  " * indent + self.name)
        for child in self.childname_to_child.values():
            child.print_text(indent + 1)
        for filename in self.filenames:
            print("  " * (indent + 1) + filename.split("/")[-1])

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
            childnames_sorted = list(self.childname_to_child.keys())
            childnames_sorted.sort()
            for childname in childnames_sorted:
                child = self.childname_to_child[childname]
                child.print_xml(indent + 1)
            if self.parent == None:
                print("</Global>")
            else:
                print("%s</Category>" % (total_indent))
            assert len(self.filenames) == 0
        else:
            assert len(self.filenames) > 0
            # Condense attribute lists of this node and all parents into a single set:
            attr_lists = [node.attrs for node in [self] + self.get_ancestors()]
            combined_attrs = set(functools.reduce(lambda l1, l2: l1 + l2, attr_lists))
            attr_string = " ".join(combined_attrs)

            for filename in self.filenames:
                print("%s<Resource name=\"%s\" %s" % (total_indent, ntpath.basename(filename), attr_string))
                print("%spath=\"%s\">" % (("  " * (indent + 1)), filename))
                print("%s</Resource>" % (total_indent))


class FilenamesTree:
    def __init__(self, root_name, tree_levels):
        self.root = FilenamesNode(root_name, None)
        self.levels = tree_levels

    def insert_filename(self, filename, node_attrs):
        """
        Insert the given filename into this tree of filenames, by consecutively
        considering each level in the tree, and assigning the filename to exactly one
        node at that tree level.

        :param filename: A string filename
        :param node_attrs: A dictionary specifying the attributes to be associated with specific
            nodes, as specified by the nodes' names
        """

        # Start out with the root node of the tree and build the actual tree
        # nodes, including assignment of parent/child relationships, level by level:
        curr_node = self.root

        # Consider each level in the tree. Each level should have been
        # computed at this point, and populated with two dictionaries indicating
        # how each nodes maps to filenames, and how filenames map to nodes.
        for level_name, tree_level in self.levels.items():

            # Retrieve the name of the node that this filename has been
            # assigned to at this level:
            selected_child_name = tree_level.filename_to_node_value[filename]

            # Either retrieve that child node (if it already exists amongst the
            # children of the current node), or else create a child node for this
            # filename at this tree level and register it:
            if selected_child_name in curr_node.childname_to_child:
                selected_child = curr_node.childname_to_child[selected_child_name]
            else:
                # Will need to create a new node to include this filename. But first,
                # retrieve the attributes specified for nodes of that name:
                child_node_attrs = []
                if selected_child_name in node_attrs:
                    child_node_attrs = node_attrs[selected_child_name]

                # Generate a new filenames node, and register it as a child of
                # the current node:
                selected_child = FilenamesNode(selected_child_name, curr_node, attrs=child_node_attrs)
                curr_node.childname_to_child[selected_child_name] = selected_child

            # Now, continue constructing the next level of the tree (if any),
            # focusing on the node obtained/created above:
            curr_node = selected_child

        # At this point, we are at the leaf-node level in the tree, and can
        # record this filename at that leaf node:
        curr_node.filenames.append(filename)

    def print_text(self):
        indent = 0
        self.root.print_text(indent)

    # FIXME: Perhaps need to refactor this for better separation of concerns.
    def print_xml(self):
        print('<?xml version="1.0" encoding="UTF-8"?>')
        indent = 0
        self.root.print_xml(indent)
