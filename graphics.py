from threading import Thread, Event
import pyqtgraph as pg


def show_packets_through_nodes(data):
    event = Event()

    def thread_main():
        app = pg.QtGui.QApplication([])
        window = pg.GraphicsWindow(title='Nodes Load Statistics')
        window.setFocus()

        plot = window.addPlot(title='Packets transported through nodes', row=1, col=1)
        window.setGeometry(50, 150, 300, 300)

        bar_graph_item = pg.BarGraphItem(x=[i + 1 for i in range(len(data))],
                                         height=[0 for i in range(len(data))],
                                         width=0.9, brush='b')
        plot.addItem(bar_graph_item)

        while not event.is_set():
            bar_graph_item.setOpts(height=data)
            app.processEvents()

    thread = Thread(target=thread_main)
    thread.start()

    def stopper():
        event.set()
        thread.join()

    return stopper
