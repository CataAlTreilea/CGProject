from collections import deque
from dataclasses import dataclass
from typing import Optional, Iterable

from lib.point_location.geo.shapes import Point, Triangle
from lib.point_location.geo.shapes import ccw


def point_pair_hash(p1: Point, p2: Point):
   
    return hash(hash(p1) + hash(p2))


def retrieve_path(graph: dict[int, Optional[int]], s: int) -> list[int]:

    node = s
    path = []
    while True:
        if node not in graph:
            return []

        path.append(node)
        if graph[node] is None:
            return list(reversed(path))

        node = graph[node]


def find_common_element(l1: Iterable, l2: Iterable):
   
    for i in l1:
        for j in l2:
            if i == j:
                return i
    return None


@dataclass()
class TriangleInfo:
    triangle: Triangle
    edges: set[int]
    neighbors: set[int]
    pass


class DCEL:
    def __init__(self, triangles: Iterable[Triangle]):
        self.triangles: dict[int, TriangleInfo] = dict()
        self.edges: dict[int, Edge] = dict()
        self._create_graph(triangles)
        return

    def _create_graph(self, triangles: Iterable[Triangle]):
        for t in triangles:
            edges = set()
            neighbors = set()
            this_triangle_hash = hash(t)
            for i in range(3):
                hash_e = point_pair_hash(t.points[i], t.points[(i + 1) % 3])
                if hash_e not in self.edges.keys():
                    self.edges[hash_e] = Edge(t.points[i], t.points[(i + 1) % 3], this_triangle_hash)
                else:
                    other_triangle_hash = self.edges[hash_e].add_triangle(t)
                    neighbors.add(other_triangle_hash)
                    self.triangles[other_triangle_hash].neighbors.add(this_triangle_hash)
                edges.add(hash_e)
            self.triangles[this_triangle_hash] = TriangleInfo(t, edges, neighbors)
        return

    def bfs(self, p1_triangle: Triangle, p2_triangle: Triangle) -> list[int]:

        p1_hash = hash(p1_triangle)
        p2_hash = hash(p2_triangle)

        graph = self.triangles
        visited = [p1_hash]
        queue = [p1_hash]

        traversal = {p1_hash: None}

        while queue:
            s = queue.pop(0)
  
            if s == p2_hash:
                return retrieve_path(traversal, s)

            for neighbour in graph[s].neighbors:
                if neighbour not in visited:
                    traversal[neighbour] = s
                    visited.append(neighbour)
                    queue.append(neighbour)

    def presentable_form(self, triangle_hashes: list[int]):
        triangles = []
        for h in triangle_hashes:
            t = self.triangles[h].triangle
            triangles.append({'x': [p.x for p in t.points], 'y': [p.y for p in t.points]})
        return triangles

    def retrieve_triangles(self, triangle_hashes):
        return [self.triangles[h].triangle for h in triangle_hashes]

    def funnel(self, triangle_hashes: list[int], start: Point, end: Point):
        
        edges = []
        for i in range(len(triangle_hashes) - 1):
            edge_hash = find_common_element(self.triangles[triangle_hashes[i]].edges,
                                            self.triangles[triangle_hashes[i + 1]].edges)
            edges.append(self.edges[edge_hash])

        passthrough_edges = []
        for e in edges:
            passthrough_edges.append({'x': [e.p1.x, e.p2.x], 'y': [e.p1.y, e.p2.y]})
        
        if not passthrough_edges:
            return {'x': [start.x, end.x], 'y': [start.y, end.y]}

       
        pl, pr = edges[0].p1, edges[0].p2
        if not ccw(pl, start, pr):
            pl, pr = pr, pl

        prev_edge = edges.pop(0)

        tail = deque((start,))  
        left = deque((pl,))    
        right = deque((pr,))    

        def finalize():

            if right and right[0] in tail:
                queues = [right, left]
            else:
                queues = [left, right]

            for q in queues:
                while q:
                    item = q.popleft()
                    if q is left:
                        if ccw(tail[-1], item, end):
                            tail.append(item)
                    else:
                        if ccw(end, item, tail[-1]):
                            tail.append(item)

            tail.append(end)

            return {'x': [p.x for p in tail], 'y': [p.y for p in tail]}

        print("\noperation 0")

      
        for edge in edges:

            
            last_points = [prev_edge.p1, prev_edge.p2]


            if edge.p1 in last_points:
                bound_point, free_point = edge.p1, edge.p2
            elif edge.p2 in last_points:
                bound_point, free_point = edge.p2, edge.p1
            else:
                raise ValueError("No common points between 2 consecutive edges.")

            if bound_point == left[-1]:
                

                if bound_point == tail[-1]:
                    print("op[right]: tail=left_bound")

           
                    right.clear()
                elif right[0] == tail[-1]:
                    print("op[right]: tail=right_last")
                    right.popleft()
                elif not ccw(left[0], tail[-1], free_point):
                   
                    print("op[right]: crossing")

       
                    last_left_point = None
                    while left and not ccw(left[0], tail[-1], free_point):
                        last_left_point = left.popleft()
                        tail.append(last_left_point)

                    if not left and last_left_point is not None:
                        left.append(last_left_point)

                    
                    right.clear()
                elif not ccw(tail[-1], right[-1], free_point):
             
                    print("op[right]: widening")
                else:
                    
                    print("op[right]: narrowing")

                 
                    while right and ccw(tail[-1], right[-1], free_point):
                        right.pop()
                    pass
               
                right.append(free_point)
            elif bound_point == right[-1]:
                
                if bound_point == tail[-1]:
                    print("op[left]: tail=right_bound (narrowing)")

                   
                    left.clear()
                elif left[0] == tail[-1]:
                    print("op[left]: tail=left_last")
                    left.popleft()
                elif not ccw(free_point, tail[-1], left[0]):
                  
                    print("op[left]: crossing")

                    last_right_point = None
                    while right and not ccw(free_point, tail[-1], right[0]):
                        last_right_point = right.popleft()
                        tail.append(last_right_point)

                    if not right and last_right_point is not None:
                        right.append(last_right_point)

                 
                    left.clear()
                elif ccw(tail[-1], left[-1], free_point):
                   
                    print("op[left]: widening")
                else:
                    
                    print("op[left]: narrowing")

                  
                    while left and not ccw(tail[-1], left[-1], free_point):
                        left.pop()
                    pass

               
                left.append(free_point)
            else:
                raise ValueError("No common bound point.")
                pass

           
            prev_edge = edge

           
            pass

        return passthrough_edges, finalize()
    pass


class Edge:
    def __init__(self, p1: Point, p2: Point, triangle):
        self.p1 = p1
        self.p2 = p2
        if triangle is None:
            raise ValueError("Received None")
        self.triangles = [triangle]
        return

    def __hash__(self):
        return point_pair_hash(self.p1, self.p2)

    def add_triangle(self, triangle):
        if len(self.triangles) > 1:
            raise IndexError("Attempted to assign a third triangle to an edge")
        self.triangles.append(triangle)
        return self.triangles[0]
