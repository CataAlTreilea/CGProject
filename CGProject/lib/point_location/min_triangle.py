from math import sqrt, ceil, floor
from typing import Optional

from .geo.shapes import Point, Line, Triangle, Polygon, ccw, Shape2d
from .geo.spatial import convex_hull



def min_bounding_triangle(poly: Polygon) -> Optional[Triangle]:
   
    if not poly.is_convex():
        poly = convex_hull(poly.points)

    n = poly.n
    points = poly.points

   
    if n < 3:
        raise ValueError("Polygon must have at least three vertices.")
    elif n == 3:
        return Triangle(poly.points[0], poly.points[1], poly.points[2])

    def side(idx: int) -> Line:
         return Line(points[(idx - 1) % n], points[idx % n])

    def is_valid_triangle(vertex_a: Point, vertex_b: Point, vertex_c: Point,
                          _a: int, _b: int, _c: int) -> bool:
        if not (vertex_a and vertex_b and vertex_c):
            return False

        if vertex_a.close_to(vertex_b) or vertex_a.close_to(vertex_c) or vertex_b.close_to(vertex_c):
            return False

        midpoint_a = Line(vertex_c, vertex_b).midpoint()
        midpoint_b = Line(vertex_a, vertex_c).midpoint()
        midpoint_c = Line(vertex_a, vertex_b).midpoint()

        def validate_midpoint(midpoint: Point, index: int) -> bool:
           
            s = side(index)

          
            epsilon = 0.01

            if s.vertical:
                if midpoint.x != s.p1.x:
                    return False
                max_y = max(s.p1.y, s.p2.y) + epsilon
                min_y = min(s.p1.y, s.p2.y) - epsilon
                if not (max_y >= midpoint.y >= min_y):
                    return False

                return True
            else:
                max_x = max(s.p1.x, s.p2.x) + epsilon
                min_x = min(s.p1.x, s.p2.x) - epsilon
           
                if not (max_x >= midpoint.x >= min_x):
                    return False

                if not s.at_x(midpoint.x).close_to(midpoint):
                    return False

                return True

        return (validate_midpoint(midpoint_a, _a) and validate_midpoint(midpoint_b, _b)
                and validate_midpoint(midpoint_c, _c))

    def triangle_for_index(_c: int, _a: int, _b: int) -> tuple[Optional[Triangle], int, int]:
    
        _a = max(_a, _c + 1) % n
        _b = max(_b, _c + 2) % n
        side_c = side(_c)

        def h(point: Point | int, _side: Line) -> float:
          
            if isinstance(point, Point):
                return _side.distance(point)
            elif isinstance(point, int):
                return _side.distance(points[point])

        def gamma(point: Point, on: Line, base: Line) -> Point:
           
            intersection = on.intersection(base)
            dist = 2 * h(point, base)
          
            if on.vertical:
                d_dist = h(Point(intersection.x, intersection.y + 1), base)
                guess = Point(intersection.x, intersection.y + dist / d_dist)
                if ccw(base.p1, base.p2, guess) != ccw(base.p1, base.p2, point):
                    guess = Point(intersection.x,
                                  intersection.y - dist / d_dist)
                return guess
            else:
                d_dist = h(on.at_x(intersection.x + 1), base)
                guess = on.at_x(intersection.x + dist / d_dist)
                if ccw(base.p1, base.p2, guess) != ccw(base.p1, base.p2, point):
                    guess = on.at_x(intersection.x - dist / d_dist)
                return guess

     
        def high(__b: int, __gamma_b: Point) -> bool:
    
            if ccw(__gamma_b, points[__b], points[(__b - 1) % n]) ==\
                    ccw(__gamma_b, points[__b], points[(__b + 1) % n]):
                return False

     
            if ccw(points[(__b - 1) % n], points[(__b + 1) % n], __gamma_b) ==\
                    ccw(points[(__b - 1) % n], points[(__b + 1) % n], points[__b]):
                return h(__gamma_b, side_c) > h(__b, side_c)
            return False

        def low(__b: int, __gamma_b: Point) -> bool:
     
            if ccw(__gamma_b, points[__b], points[(__b - 1) % n]) ==\
                    ccw(__gamma_b, points[__b], points[(__b + 1) % n]):
                return False


            if ccw(points[(__b - 1) % n], points[(__b + 1) % n], __gamma_b) ==\
                    ccw(points[(__b - 1) % n], points[(__b + 1) % n], points[__b]):
                return False
            else:
                return h(__gamma_b, side_c) > h(__b, side_c)

        def on_left_chain(__b: int) -> bool:
            return h((__b + 1) % n, side_c) >= h(__b, side_c)

        def increment_low_high(__a: int, __b: int, __c: int) -> tuple[int, int]:
            _gamma_a = gamma(points[__a], side(__a), side_c)

            if high(__b, _gamma_a):
                __b = (__b + 1) % n
            else:
                __a = (__a + 1) % n
            return __a, __b

        def tangency(__a: int, __b: int):
            _gamma_b = gamma(points[__b], side(__a), side_c)
            return h(__b, side_c) >= h((__a - 1) % n, side_c) and high(__b, _gamma_b)

        
        while on_left_chain(_b):
            _b = (_b + 1) % n

 
        while h(_b, side_c) > h(_a, side_c):
            _a, _b = increment_low_high(_a, _b, _c)

       
        while tangency(_a, _b):
            _b = (_b + 1) % n

        gamma_b = gamma(points[_b], side(_a), side_c)
      
        if low(_b, gamma_b) or h(_b, side_c) < h((_a - 1) % n, side_c):
            side_b = side(_b)
            side_a = side(_a)
            side_b = Line(side_c.intersection(side_b),
                          side_a.intersection(side_b))

            if h(side_b.midpoint(), side_c) < h((_a - 1) % n, side_c):
                gamma_a = gamma(points[(_a - 1) % n], side_b, side_c)
                side_a = Line(gamma_a, points[(_a - 1) % n])
        else:
            gamma_b = gamma(points[_b], side(_a), side_c)
            side_b = Line(gamma_b, points[_b])
            side_a = Line(gamma_b, points[(_a - 1) % n])

       
        vertex_a = side_c.intersection(side_b)
        vertex_b = side_c.intersection(side_a)
        vertex_c = side_a.intersection(side_b)

        if not is_valid_triangle(vertex_a, vertex_b, vertex_c, _a, _b, _c):
            _triangle = None
        else:
            _triangle = Triangle(vertex_a, vertex_b, vertex_c)

        return _triangle, _a, _b

    triangles = []
    a = 1
    b = 2
    for i in range(n):
        triangle, a, b = triangle_for_index(i, a, b)
        if triangle:
            triangles.append(triangle)

    if not triangles:
        return None

    areas = [triangle.area() for triangle in triangles]
    return triangles[areas.index(min(areas))]


def larger_bounding_triangle(points: list[Point], factor: int = 10) -> Optional[Polygon]:
    def expand(poly: Shape2d, _factor: int) -> Polygon:
   
        def bisect(__a: Point, __b: Point, __c: Point) -> Point:
            # Define vector operations
            def magnitude(__v: list[float]) -> float:
                return sqrt(sum([__x * __x for __x in __v]))

            def normalize(__v: list[float]) -> list[float]:
                mag = magnitude(__v)
                return [__x / mag for __x in __v]

            def median(__u: list[float], __v: list[float]):
                return [(__x[0] + __x[1]) / 2 for __x in zip(__u, __v)]

            def reverse(__v: list[float]):
                return [-__x for __x in __v]

  
            v_b = [__b.x - __a.x, __b.y - __a.y]
            v_c = [__c.x - __a.x, __c.y - __a.y]
            v_b = normalize(v_b)
            v_c = normalize(v_c)
            bisector = reverse(median(v_b, v_c))

            x = __a.x + _factor * bisector[0]
            y = __a.y + _factor * bisector[1]

            def abs_round(n: float) -> int:
                if n < 0:
                    return floor(n)
                return ceil(n)

            x = abs_round(x)
            y = abs_round(y)

            return Point(x, y)

        def adjust(i: int) -> Point:
            __a = poly.points[i % poly.n]
            __b = poly.points[(i - 1) % poly.n]
            __c = poly.points[(i + 1) % poly.n]
            return bisect(__a, __b, __c)

        expanded_points = [adjust(i) for i in range(poly.n)]
        return Polygon(expanded_points)

    tri = min_bounding_triangle(Polygon(points))
    if not tri:
        return None

    return expand(tri, factor)


