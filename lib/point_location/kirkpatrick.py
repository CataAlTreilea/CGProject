from functools import reduce
from typing import Optional, Iterable


from lib.point_location.geo.spatial import convex_hull
from lib.point_location.geo.shapes import Point, Polygon, Triangle, Shape2d
from . import min_triangle
from lib.point_location.geo.graph import UndirectedGraph, DirectedGraph
from lib.path_finding.path_tools import DCEL


class BoundingTriangleCreationError(Exception):
    pass


class SinglePolygonLocator:

    def __init__(self, regions: list[Triangle], outline=None):
        self.triangles: dict[int, Triangle] = {hash(t): t for t in regions}
        self.dcel = DCEL(regions)
        self._preprocess(regions, outline)
        self.__starting_point = None
        self.__starting_triangle = None

    def _preprocess(self, regions: list[Triangle], outline=None):
        def process_boundary(__regions: list[Triangle], __outline=None):
           
            def add_bounding_triangle(poly: Polygon):
            

                bounding_tri = min_triangle.larger_bounding_triangle(poly.points)
                if not bounding_tri:
                    return None, []
                bounding_regions = bounding_tri.triangulate_polygon(poly.points)
               
                return bounding_tri, bounding_regions

            if not __outline:
                points = reduce(lambda ps, r: ps + r.points, __regions, [])
                __outline = convex_hull(points)
            return add_bounding_triangle(__outline)

        def triangulate_regions(__regions: list[Shape2d]):
            
            __frontier = []

            for region in __regions:
                self.dag.add_node(region)
                
                if region.n < 3:
                    raise ValueError(f"Region with points: {region.points} has "
                                     f"less than 3 points.")
                
                if isinstance(region, Polygon):
                    
                    if region.n > 3:
                        triangles = region.triangulation
                        for triangle in triangles:
                            
                            self.dag.add_node(triangle)
                            self.dag.connect(triangle, region)
                        
                            __frontier.append(triangle)
                    else:
                        if tri := region.to_triangle():
                            __frontier.append(tri)
                elif region.n == 3 and isinstance(region, Triangle):
                    __frontier.append(region)
                else:
                    raise ValueError(f"Region with points: {region.points} cannot be "
                                     f"converted to a triangle.")

            return __frontier

        def remove_independent_set(__regions: list[Triangle]):
          
            points_to_regions = {}
            for __idx, __region in enumerate(__regions):
                for point in __region.points:
                    if point in points_to_regions:
                        points_to_regions[point].add(__idx)
                        continue

                    points_to_regions[point] = {__idx}

            # Connect graph
            g = UndirectedGraph()
            for __region in __regions:
                for __idx in range(__region.n):
                    __u = __region.points[__idx % __region.n]
                    __v = __region.points[(__idx + 1) % __region.n]
                    if not g.contains(__u):
                        g.add_node(__u)
                    if not g.contains(__v):
                        g.add_node(__v)
                    g.connect(__u, __v)

            
            removal = g.independent_set(8, avoid=bounding_triangle.points)

         
            unaffected_regions = set([i for i in range(len(__regions))])
            new_regions = []
            for p in removal:
             
                affected_regions = points_to_regions[p]
                unaffected_regions.difference_update(points_to_regions[p])

                def calculate_bounding_polygon(__p: Point, __affected_regions):
                    edges = []
                    point_locations = {}
                    for __j, __i in enumerate(__affected_regions):
                        edge = set(__regions[__i].points)
                        edge.remove(__p)
                        edges.append(edge)
                        for v in edge:
                            if v in point_locations:
                                point_locations[v].add(__j)
                            else:
                                point_locations[v] = {__j}

                    __boundary = []
                    edge = edges.pop()
                    for v in edge:
                        point_locations[v].remove(len(edges))
                        __boundary.append(v)
                    for k in range(len(__affected_regions) - 2):
                        v = __boundary[-1]
                        __i = point_locations[v].pop()
                        edge = edges[__i]
                        edge.remove(v)
                        u = edge.pop()
                        point_locations[u].remove(__i)
                        __boundary.append(u)

                    return Polygon(__boundary)

          
                poly = calculate_bounding_polygon(p, affected_regions)
                triangles = poly.triangulation
                for triangle in triangles:
                    self.dag.add_node(triangle)
                    for j in affected_regions:
                        __region = __regions[j]
                        self.dag.connect(triangle, __region)
                    new_regions.append(triangle)

            for i in unaffected_regions:
                new_regions.append(__regions[i])

            return new_regions

        self.dag = DirectedGraph()

      
        self.regions = regions

  
        bounding_triangle, boundary = process_boundary(regions, outline)
        if bounding_triangle is None:
            raise BoundingTriangleCreationError("Could not calculate the bounding triangle.")

        
        self.boundary = boundary

        frontier = triangulate_regions(regions + boundary)
        while len(frontier) > 1:
            frontier = remove_independent_set(frontier)
        return

    def locate(self, p: Point) -> Optional[Triangle]:
        
        polygon, valid = self.annotated_locate(p)

     
        if not valid:
            return None

        return polygon

    def annotated_locate(self, p: Point) -> (Optional[Triangle], bool):
 
        curr = self.dag.root()
        if not curr.contains_point(p):
            return None, False

        children = self.dag.e[curr]
        while children:
            for region in children:
                if region.contains_point(p):
                    curr = region
                    break

            children = self.dag.e[curr]

        
        return curr, curr in self.regions

    def find_path(self, tri_1: Triangle, tri_2: Triangle) -> Optional[list[int]]:
        if not (hash(tri_1) in self.triangles and hash(tri_2) in self.triangles):
            return None
        return self.dcel.bfs(tri_1, tri_2)

    def funnel(self, triangle_hashes: list[int], start: Point, end: Point):
        return self.dcel.funnel(triangle_hashes, start, end)

    def set_first_point(self, point: Point, triangle: Triangle = None):
        if triangle is not None:
            if triangle.contains_point(point):
                self.__starting_point = point
                self.__starting_triangle = triangle
                return True

            self.__starting_triangle = None
            self.__starting_point = None
            return False

        if (tri := self.locate(point)) is not None:
            self.__starting_triangle = tri
            self.__starting_point = point
            return True

        self.__starting_triangle = None
        self.__starting_point = None
        return False

    def get_shortest_path(self, end_point: Point):
        if self.__starting_point is None:
            return None
        if (tri := self.locate(end_point)) is None:
            return None

        if (tri_path := self.dcel.bfs(self.__starting_triangle, tri)) is None:
            return None

        res = self.dcel.funnel(tri_path, self.__starting_point, end_point)

        self.__starting_triangle = None
        self.__starting_point = None
        return res

    pass


class MultiPolygonLocator:
    def __init__(self) -> None:
        self.locators = set()
        self.all_triangles: dict[int, Triangle] = dict()
        self.triangle_owners: dict[int, SinglePolygonLocator] = dict()

        self.__starting_point = None
        self.__starting_triangle = None
        self.__current_locator = None
        pass
    
   
    def add_regions(self, region_outlines: Iterable[Polygon]) -> Optional[set[int]]:
        tri_triangles = {**self.all_triangles}
        tri_locators = {**self.triangle_owners}

        skipped = set()
        for i, region in enumerate(region_outlines):

            triangulation = region.triangulation
            try:
                locator = SinglePolygonLocator(triangulation, region)
            except BoundingTriangleCreationError:
                skipped.add(i)
                continue
            for triangle in triangulation:
                if (h := hash(triangle)) in tri_triangles:
                    return None
                tri_triangles[h] = triangle
                tri_locators[h] = locator
            else:
                self.locators.add(locator)
            pass

        self.all_triangles = tri_triangles
        self.triangle_owners = tri_locators
        return skipped

    def locate(self, p: Point, previous_triangle: Triangle = None) -> Optional[Triangle]:
        if previous_triangle is not None:
            if (locator := self.triangle_owners.get(hash(previous_triangle))) is None:
                return None
            return locator.locate(p)
        for locator in self.locators:
            if (triangle := locator.locate(p)) is not None:
                return triangle
        return None

    def set_first_point(self, point: Point) -> bool:

        self.__starting_point = None
        self.__starting_triangle = None
        self.__current_locator = None

        if (tri := self.locate(point)) is None:
            return False
        h = hash(tri)
        locator = self.triangle_owners[h]

        if locator.set_first_point(point, tri):
            self.__starting_point = point
            self.__starting_triangle = tri
            self.__current_locator = locator
            return True
        return False

    def has_first_point(self):
        return not not self.__starting_point

    def get_shortest_path(self, end_point: Point):
        if (tri := self.locate(end_point)) is None:
            return None

        h = hash(tri)
        locator = self.triangle_owners[h]

        if locator is not self.__current_locator:
            return None

        self.__starting_point = None
        self.__starting_triangle = None
        self.__current_locator = None

        return locator.get_shortest_path(end_point)
    pass
        
