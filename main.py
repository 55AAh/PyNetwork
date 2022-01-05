import os
import random
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d
from sklearn.cluster import KMeans

from simulation import Simulation, Packet
import graphics


def sample_simulation():
    simulation = Simulation()

    simulation.add_endpoint(80, 520)
    simulation.add_node(150, 470)
    simulation.add_node(290, 550)
    simulation.add_endpoint(80, 300)
    simulation.add_endpoint(120, 90)
    simulation.add_node(200, 240)
    simulation.add_endpoint(400, 80)
    simulation.add_node(320, 320)
    simulation.add_node(480, 480)
    simulation.add_endpoint(650, 450)
    simulation.add_node(300, 230)
    simulation.add_endpoint(560, 560)
    simulation.add_node(520, 280)
    simulation.add_node(630, 240)
    simulation.add_node(640, 160)
    simulation.add_endpoint(570, 40)
    simulation.add_endpoint(760, 110)

    simulation.connect(0, 1)
    simulation.connect(1, 3)
    simulation.connect(3, 5)
    simulation.connect(4, 5)
    simulation.connect(5, 10)
    simulation.connect(10, 7)
    simulation.connect(1, 7)
    simulation.connect(1, 2)
    simulation.connect(2, 8)
    simulation.connect(8, 11)
    simulation.connect(11, 9)
    simulation.connect(6, 10)
    simulation.connect(10, 12)
    simulation.connect(7, 12)
    simulation.connect(8, 12)
    simulation.connect(12, 13)
    simulation.connect(13, 14)
    simulation.connect(14, 15)
    simulation.connect(14, 16)
    simulation.connect(9, 12)

    return simulation


def test_random(packets_count=100):
    simulation = sample_simulation()

    while True:
        simulation.packets = {}
        endpoint_nodes = np.array([(x, y) for x, y, e in simulation.nodes if e])
        router_nodes = np.array([(x, y) for x, y, e in simulation.nodes if not e])

        if len(router_nodes) <= 1:
            break

        for i in range(packets_count):
            send_time = i * 30
            endpoint_indexes = [i for i, node in enumerate(simulation.nodes) if node[2]]
            source = random.choice(endpoint_indexes)
            destination = random.choice(endpoint_indexes)
            simulation.add_packet(Packet(send_time, source, destination))

        data = [0 for _ in range(len(simulation.nodes))]
        stop = graphics.show_packets_through_nodes(data)

        def observer(_packet_uuid, _source, _destination, node_id, _interface):
            data[node_id] += 1

        ms_mean, ms_med = simulation.run(observer)
        print("MS MEAN = {}".format(round(ms_mean)))
        print("MS MED  = {}".format(round(ms_med)))
        print()

        stop()
        data = np.array(data)
        data = data / max(data) * 10

        endpoint_data = [d for i, d in enumerate(data) if simulation.nodes[i][2]]
        router_data = [d for i, d in enumerate(data) if not simulation.nodes[i][2]]
        remaining_ind = np.argpartition(router_data, len(router_data) - 1)[1:]
        plt.scatter(x=router_nodes[:, 0], y=router_nodes[:, 1], s=router_data,
                    c=[("g" if i in remaining_ind else "r") for i in range(len(router_nodes))])
        plt.scatter(x=endpoint_nodes[:, 0], y=endpoint_nodes[:, 1], s=endpoint_data,
                    c=["b" for _ in range(len(endpoint_nodes))])
        plt.plot()
        plt.show()

        k_means = KMeans(n_clusters=len(router_nodes) - 1)
        k_means.fit(router_nodes)
        k_means_cluster_centers = k_means.cluster_centers_

        vor = Voronoi(np.array([(x, y) for x, y, _e in simulation.nodes]))
        voronoi_plot_2d(vor, show_point=False, show_vertices=False, line_colors='orange',
                        line_width=2, line_alpha=0.6, point_size=2)
        plt.plot(endpoint_nodes[:, 0], endpoint_nodes[:, 1], 's', markersize=6)
        left_router_nodes = set()
        introduced_router_nodes = []
        for k in range(len(router_nodes) - 1):
            cluster_center = k_means_cluster_centers[k]
            plt.plot(cluster_center[0], cluster_center[1], 'o',
                     markeredgecolor='k', markersize=6)
            min_dist, closest_node = np.inf, None
            found_in_old = False
            for i, node in enumerate(router_nodes):
                if cluster_center[0] == node[0] and cluster_center[1] == node[1]:
                    found_in_old = True
                dist = ((np.array(cluster_center) - node) ** 2).sum()
                if dist < min_dist:
                    min_dist, closest_node = dist, i
            left_router_nodes.add(closest_node)
            if not found_in_old:
                introduced_router_nodes.append(cluster_center)
        deleted_router_nodes = np.array([node for i, node in enumerate(router_nodes) if i not in left_router_nodes])
        plt.plot(deleted_router_nodes[:, 0], deleted_router_nodes[:, 1], 'x', markersize=6)
        plt.title('KMeans Clusters')
        plt.grid(True)
        plt.show()

        # input()
        for deleted_node in deleted_router_nodes:
            for i, node in enumerate(simulation.nodes):
                introduced_router_nodes = np.array(introduced_router_nodes)
                node_p = np.array([node[0], node[1]])
                if (node_p == deleted_node).all() and not node[2]:
                    min_dist, closest_introduced = np.inf, None
                    for j, introduced_node in enumerate(introduced_router_nodes):
                        dist = ((node_p - introduced_node) ** 2).sum()
                        if dist < min_dist:
                            min_dist, closest_introduced = dist, j
                    if closest_introduced is not None:
                        simulation.nodes[i] = (
                            int(introduced_router_nodes[closest_introduced][0]),
                            int(introduced_router_nodes[closest_introduced][1]),
                            False)
                        introduced_router_nodes = list(introduced_router_nodes)
                        del introduced_router_nodes[closest_introduced]

                        for j, near_node in enumerate(simulation.nodes):
                            near_node_p = np.array([near_node[0], near_node[1]])
                            if j != i and ((near_node_p - node_p) ** 2).sum() < 500:
                                print("DELETING")
                                new_conn = []
                                for n1, n2 in simulation.connections:
                                    if n1 == i:
                                        n1 = j
                                    if n2 == i:
                                        n2 = j
                                    if n1 >= i:
                                        n1 -= 1
                                    if n2 >= i:
                                        n2 -= 1
                                    if n1 != n2 and (n1, n2) not in new_conn and (n2, n1) not in new_conn:
                                        new_conn.append((n1, n2))
                                simulation.connections = new_conn
                                del simulation.nodes[i]
                    break

    simulation.packets = {}
    simulation.add_packet(Packet(3600 * 1000, 0, 0))
    simulation.run(None)


def main():
    test_random()


if __name__ == '__main__':
    main()
