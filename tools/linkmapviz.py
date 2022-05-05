# Link Map Visualizer
# Regex to match symbol found in file: "(\w)\] ([_a-zA-Z0-9\-.]+) \((\w+),(\w+)\) found in ([_a-zA-Z0-9\-.]+)"
# Regex to match symbol found as a linker generated symbol: "(\w)\] ([_a-zA-Z0-9\-.]+) found as linker generated symbol"
import re
import json

# Assumptions
# GALE01.map exists within build
GALE01 = 'build/ssbm.us.1.2/GALE01.map'

def tokens2obj(tokens, item):
    # structure of tokens:
    # [ raw level, identifier, '(<type>,<scope>)', drop, drop, file object ]
    assert(len(tokens) == 6)
    raw_level, iden, _ctype_scope, _, _, file_obj = tokens
    level = int(raw_level[:-1])
    _ctype_scope = _ctype_scope[1:-1]
    ctype, scope = _ctype_scope.split(',')

    return {'level': level, 'item': item, 'id': iden, 'ctype': ctype, 'scope': scope, 'objfile': file_obj}

def tokens2symbol(tokens, item):
    # structure of tokens:
    # [ raw level, identifier, drop, drop, drop, drop, drop]
    assert(len(tokens) == 7)
    raw_level, iden, _, _, _, _, _ = tokens
    level = int(raw_level[:-1])

    return {'level': level, 'item': item, 'id': iden, 'ctype': 'linkersymbol'}

# sequential order of link map
parsed = []

# open file and start iterating
item = 0
with open(GALE01) as file:
    while line := file.readline():
        tokens = line.split()

        # pass on empty line
        if (len(tokens) != 0):
            head, *tail = tokens
            if (']' in head):
                if (len(tokens) == 6):
                    # take tokens and create the storage object
                    obj = tokens2obj(tokens, item)
                    parsed.append(obj)
                    item = item + 1
                elif (len(tokens) == 7):
                    # take tokens are create generated symbol object
                    obj = tokens2symbol(tokens, item)
                    parsed.append(obj)
                    item = item + 1
                else:
                    pass

def obj2treeobj(obj, idx, parent_idx):
    tree_obj = {'obj': obj, 'index': idx, 'parent': parent_idx}

    return tree_obj

# link the parsed sequence together
def linker(parsed):
    # link map object
    # obj = { level, item #, id, ctype, [scope, objfile]}
    # link map tree
    # tree = [{ link map object, current index, parent index }]
    tree = []

    # build 'starting tree'
    for i in range(len(parsed)):
        obj = parsed[i]
        tree_obj = obj2treeobj(obj, i, i)
        tree.append(tree_obj)

        assert(obj['item'] == tree_obj['index'])
        assert(obj == tree_obj['obj'])

    # go through tree and update the parent references
    for i in range(len(tree) - 1):
        first = tree[i]
        second = tree[i + 1]

        first_level = first['obj']['level']
        second_level = second['obj']['level']

        # are we trying to find the parent of a level 1?
        if (second_level == 1):
            # yes -> level 1 parent = itself
            second['parent'] == second['index']
        else:
            # no -> start casing
            if (first_level < second_level):
                # case 1: first level < second level -> first is parent of second
                second['parent'] = first['index']
            elif (first_level > second_level):
                # case 2: first level > second level -> moved to different branch, so search for parent of second
                searcher = second['index'] - 1
                while (searcher > -1):
                    potential = tree[searcher]
                    potential_level = potential['obj']['level']

                    if (potential_level == second_level - 1):
                        # we have found the parent of second
                        second['parent'] = potential['index']
                        break

                    searcher = searcher - 1
            else:
                # case 3: first level == second level -> same level so same parent
                second['parent'] = first['parent']

    return tree

tree = linker(parsed)
treemap = json.dumps(tree)
print(treemap)

# TODO make command line utility for this
# what do we want to search it?
#   - search by label id
#   - search by object file