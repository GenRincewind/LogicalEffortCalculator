from functools import reduce
import networkx as nx
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import json
import random
from datetime import datetime

from errno import EEXIST
from os import makedirs, path



index = 0

def calculate_capacitance(data):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # print(data)
    tG = nx.MultiDiGraph()

    capacitance_dict = {}
    print(data['ports'])

    def get_node_from_port(p):
        return data['ports'][p]["parentNodeID"]

    for k, v in reversed(list(data['nodes'].items())):
        print(k)
        tG.add_node(
            k, capacitance=v["inherent_capacitance"], node_name=v['name'])
        capacitance_dict[k] = f'{v["inherent_capacitance"]} {v["name"]}'
        for op in v['out_ports']:
            tG.add_edge(get_node_from_port(
                op['source']), get_node_from_port(op['target']), weight=1)
    print("tessss")
    print(tG.nodes)

    def update_capacitance_node_labels(tG):
        nodenames = {}
        for node in tG.nodes:
            nodenames[node] = tG.nodes[node]['node_name'] + \
                ' - ' + str(tG.nodes[node]['capacitance'])
        return nodenames

    def mkdir_p(mypath):
        '''Creates a directory. equivalent to using mkdir -p on the command line'''

        try:
            makedirs(mypath)
        except OSError as exc:  # Python >2.5
            if exc.errno == EEXIST and path.isdir(mypath):
                pass
            else:
                raise

    def draw_graph(fG, pl, text, fcapacitance_dict=None):
        global index
        if fcapacitance_dict == None:
            fcapacitance_dict = update_capacitance_node_labels(fG)
        pos = nx.spring_layout(fG)
        #subax1 = plt.subplot(pl)
        f, axs = plt.subplots(1, 1, figsize=(15, 15))
        plt.tight_layout()

        nx.draw(fG, pos, with_labels=True,
                font_weight='bold', labels=fcapacitance_dict)
        print(fG.edges)
        edge_labels = dict([((n1, n2), f'{attribute["weight"]}')
                            for n1, n2, attribute in fG.edges(data=True)])
        print(edge_labels)
        nx.draw_networkx_edge_labels(fG, pos, edge_labels=edge_labels)
        #nx.draw_shell(G, nlist=[range(5, 10), range(5)], with_labels=True, font_weight='bold')
        plt.axis('off')
        axis = plt.gca()
        axis.set_xlim([2*x for x in axis.get_xlim()])
        axis.set_ylim([2*y for y in axis.get_ylim()])
        plt.tight_layout()

        dir = f'{timestamp}/{text}'
        mkdir_p(dir)
        plt.savefig(f'{dir}/{text}{index}.png', dpi=100)
        index = index + 1

    capacitance_dict = update_capacitance_node_labels(tG)
    draw_graph(tG, 111, 'original_graph')

    def combine_capacitance(c1, c2):
        if(c1 == 0 or c2 == 0):
            return max(c1, c2)
        return c1 * c2 / (c1 + c2)

    def remove_serial(fG):
        print("serial")
        fcapacitance_dict = update_capacitance_node_labels(fG)

        currentnodes = list(fG.nodes.keys())
        print(currentnodes)
        for node in currentnodes:
            if fG.has_node(node):
                if fG.in_degree(node) == 1 and fG.out_degree(node) == 1:
                    print(node, fcapacitance_dict[node])
                    nextnode = list(fG.successors(node))[0]

                    if fG.in_degree(nextnode) == 1 and fG.out_degree(nextnode) == 1:
                        print(nextnode, fcapacitance_dict[nextnode])
                        print(node, fcapacitance_dict[node])
                        c1 = fG.nodes[nextnode]['capacitance']
                        c2 = fG.nodes[node]['capacitance']
                        fG.nodes[node]['capacitance'] = combine_capacitance(
                            c1, c2)
                        nextnextnode = list(fG.successors(nextnode))[0]

                        fG.add_edge(node, nextnextnode, weight=1)
                        fG.remove_node(nextnode)

    def remove_parallel(fG):
        print("parallel")

        fcapacitance_dict = update_capacitance_node_labels(fG)

        currentnodes = list(fG.nodes.keys())
        print(currentnodes)
        for node in currentnodes:
            node = node
            if fG.has_node(node):
                print('currentnode')
                if fG.out_degree(node) > 1:
                    print(node, capacitance_dict[node])
                    nextnodes = list(fG.successors(node))
                    cancel = False
                    newcapacitorN = nextnodes[0]
                    for nextnode in nextnodes:
                        if fG.out_degree(nextnode) > 1 or fG.out_degree(nextnode) == 0:
                            cancel = True
                            print(
                                "Canceled for having a node in parallel with multiple outs")
                            break
                    if cancel:
                        continue
                    cancel = False
                    nextnextnode = list(fG.successors(newcapacitorN))[0]
                    for nextnode in nextnodes:
                        tnextnextnode = list(fG.successors(nextnode))[0]
                        if not(tnextnextnode == nextnextnode):
                            cancel = True
                            print(
                                "Canceled for not being a bunch of nodes all in parallel towards the same one")
                            break
                    if cancel:
                        continue
                    print('parallel')
                    sum = fG.nodes[newcapacitorN]['capacitance']
                    for nextnode in nextnodes[1:]:
                        c1 = fG.nodes[nextnode]['capacitance']
                        sum = sum + c1
                        fG.remove_node(nextnode)

                    fG.nodes[newcapacitorN]['capacitance'] = sum

    def reduce_graph(fG, title):
        new_graph = fG.copy()
        fcapacitance_dict = update_capacitance_node_labels(new_graph)
        while(len(new_graph.nodes) > 3):
            remove_serial(new_graph)
            remove_parallel(new_graph)
            fcapacitance_dict = update_capacitance_node_labels(new_graph)

            draw_graph(new_graph, 111, title)
        return new_graph

    capacitance_dict = update_capacitance_node_labels(tG)

    def arbitrary_node_capacitance_to_output(tG, n1):
        reducedGraph = nx.MultiDiGraph()

        def recurse_mini_graph_create(tG, new_graph, node):
            if new_graph.has_node(node):
                return
            nextnodes = list(tG.successors(node))

            new_graph.add_node(
                node, capacitance=tG.nodes[node]['capacitance'], node_name=tG.nodes[node]['node_name'])
            for nextnode in nextnodes:
                recurse_mini_graph_create(tG, new_graph, nextnode)
                new_graph.add_edge(node, nextnode, weight=1)
        print(tG.out_degree(n1))
        if tG.out_degree(n1) > 0:
            recurse_mini_graph_create(tG, reducedGraph, n1)
        draw_graph(reducedGraph, 111, "arbitrary_node_" +
                   tG.nodes[n1]['node_name'])
        reducedGraph = reduce_graph(
            reducedGraph, 'arbitrary_node_reduction_' + tG.nodes[n1]['node_name'])

        nextnode = list(reducedGraph.successors(n1))[0]

        return reducedGraph.nodes[nextnode]['capacitance']

    reducG = reduce_graph(tG, 'total_graph')
    draw_graph(reducG, 111, 'final_reduce_total')

    out_capacitance_graph = {}
    out_capacitance_graph_labels = {}
    for node in tG.nodes:
        if tG.out_degree(node) > 0:
            capacitance = arbitrary_node_capacitance_to_output(tG, node)
            print('capacitance', capacitance)
            out_capacitance_graph[node] = capacitance
            out_capacitance_graph_labels[node] = f'{capacitance}{tG.nodes[node]["node_name"]}'
        else:
            out_capacitance_graph[node] = 0
            out_capacitance_graph_labels[node] = f'{tG.nodes[node]["node_name"]}'

    draw_graph(tG, 111, 'finalgraphwithalloutputcapacitances',
               out_capacitance_graph_labels)
    return out_capacitance_graph
    
if __name__ == '__main__':
    data = {}
    with open('testnetworknewformat.json') as f:
        data = json.load(f)
    calculate_capacitance(data)
