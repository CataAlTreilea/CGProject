import shapefile
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent

from lib.point_location.kirkpatrick import MultiPolygonLocator
from lib.point_location.geo.shapes import Point, Polygon

matplotlib.use('TkAgg')

# Add global flag for edge visibility
show_edges = False  # You can change this to False to hide edges

if __name__ == '__main__':
    fig = plt.figure()

    with shapefile.Reader(f'data/forma.shp') as reader:
        shapes = reader.shapes()

    locator = MultiPolygonLocator()

    continents_polygons = [Polygon([Point(p[0], p[1]) for p in island.points[:-1]]) for island in shapes[:10]]

    skipped = locator.add_regions(continents_polygons)

    for i, continent in enumerate(continents_polygons):
        if i in skipped:
            continue
        plt.plot(continent.x, continent.y, 'b-')

    def on_click(event: MouseEvent):
        ex, ey = event.xdata, event.ydata
        point = Point(ex, ey)
        is_valid = False
        if locator.has_first_point():
            res = locator.get_shortest_path(point)
            if res:
                passthrough_edges, path = res
                # Only plot edges if show_edges is True
                if show_edges:
                    for edge in passthrough_edges:
                        plt.plot(edge['x'], edge['y'], 'g-')  # Green lines for edges
                # Plot the final path in red
                plt.plot(path['x'], path['y'], 'r-')  # Red line for final path
                is_valid = True
        elif locator.set_first_point(point):
            is_valid = True
        if is_valid:
            msg = f'VALID: received user coordinates: {ex}, {ey}'
            plt.plot(ex, ey, 'k.')
            plt.show()
        else:
            msg = f'INVALID: received user coordinates: {ex}, {ey}'
        print(msg)
        return

    fig.canvas.mpl_connect('button_press_event', on_click)

    plt.show()


fig.canvas.mpl_connect('button_press_event', on_click)

plt.show()