import json
import subprocess
from uuid import uuid4, UUID

import numpy as np


class Packet:
    def __init__(self, send_time, source, destination):
        self.send_time = send_time
        self.source = source
        self.destination = destination
        self.observed_trip = []


class Simulation:
    def __init__(self):
        self.nodes = []
        self.connections = []
        self.packets = dict()

    def add_node(self, x, y):
        self.nodes.append((x, y, False))

    def add_endpoint(self, x, y):
        self.nodes.append((x, y, True))

    def connect(self, i, j):
        self.connections.append((i, j))

    def add_packet(self, packet):
        new_packet_uuid = uuid4()
        self.packets[new_packet_uuid] = packet
        return new_packet_uuid

    def run(self, observer):
        json_data = {
            "nodes": [(x, 600 - y, e) for x, y, e in self.nodes],
            "cable_connections": self.connections,
            "transmissions": [(packet.send_time, packet_uuid.hex, packet.source, packet.destination)
                              for packet_uuid, packet in self.packets.items()],
        }

        process = subprocess.Popen(
            ["visualize_network", "--stdin"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        process.stdin.write(json.dumps(json_data).encode("utf-8"))
        process.stdin.flush()
        process.stdin.close()

        ms_values = []

        for line in iter(process.stdout.readline, b''):
            line = line.decode("utf-8")
            ms, _, packet_uuid, source, _, destination, _, _operation, node_id, _, interface = line.split()
            ms = int(ms)
            packet_uuid = UUID(packet_uuid)
            source, destination = int(source), int(destination)
            node_id = int(node_id)
            # self.packets[packet_uuid].observed_trip.append((source, destination, node_id, interface))
            if destination == node_id:
                ms_values.append(ms)
            if observer is not None:
                observer(packet_uuid, source, destination, node_id, interface)

        ms_values = np.array(ms_values)
        return ms_values.mean(), np.median(ms_values)
