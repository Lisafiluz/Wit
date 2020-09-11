import networkx as nx
import matplotlib.pyplot as plt

data = [
    ['A', 'B'],
    ['C', 'D'],
    ['C', 'B']
]

d = [('head', '1dbf56'), ('master', '1dbf56'), ('1dbf56', '7fa1bc'), ('7fa1bc', 'ce8e3c')]

G = nx.Graph()  # new empty undirected graph
for row in d:
    src_node = row[0]
    dest_node = row[1]
    #weight = float(row[2])  # convert weight to a number
    G.add_edge(src_node, dest_node)

pos = nx.spring_layout(G)  # compute graph layout
nx.draw(G, pos, node_size=3000)  # draw nodes and edges
nx.draw_networkx_labels(G, pos)  # draw node labels/names
# draw edge weights
labels = nx.get_edge_attributes(G, 'wit graph')
nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
# show image
plt.show()