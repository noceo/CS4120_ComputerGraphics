"""
Created on 25.04.2019

@author: Paul Schade
"""

import numpy as np
import multiprocessing as mp
import time
from PIL import Image

WIDTH = 400
HEIGHT = 400

REFLECTION_DEPTH = 2

PROCESSES = 4


class Scene:
    def __init__(self, width, height, object_list, light_list, camera=None):
        """Creates a scene with all its required components"""

        self.camera = camera
        self.object_list = object_list
        self.light_list = light_list
        self.width = width
        self.height = height
        self.image = Image.new("RGB", (self.width, self.height), 0)

    def render(self, pixel):
        """Renders the given pixel"""
        x = pixel % self.width
        y = int(pixel / self.width)

        ray = camera.build_ray(x, y)
        color = self.shoot_ray(ray)

        return color

    def shoot_ray(self, ray, reflection_depth=0, max_reflection_depth=REFLECTION_DEPTH):
        """
        Shoots a ray through the scene and computes the color
        at the point of intersection with other objects of the scene

        @return: Color of the computed pixel
        """
        color = np.array([0, 0, 0])

        if reflection_depth >= max_reflection_depth:
            return color

        intersection = self.check_intersection(ray)
        if intersection is None:
            return color

        obj, hit_dist = intersection

        # calculateColor at IntersectionPoint
        intersection_point = ray.point_at_parameter(hit_dist)
        surface_norm_vector = obj.normal_at(intersection_point)

        intersection_point += (0.00001 * surface_norm_vector)

        material_color = obj.material.color_at(intersection_point)

        # Ambient lighting
        if reflection_depth == 0:
            color = color + material_color * obj.material.ambient
        elif reflection_depth > 0:
            color = np.multiply(material_color * obj.material.ambient, color)

        # Lambert shading
        for light in self.light_list:
            light = array_from_list(light)
            vec_point_to_light = normalize_rows(light - intersection_point)
            ray_point_to_light = Ray(intersection_point, vec_point_to_light)

            if self.check_intersection(ray_point_to_light) is None:
                shading_intensity = surface_norm_vector.dot(vec_point_to_light)
                if shading_intensity > 0:
                    color = color + material_color * obj.material.lambert * shading_intensity

        # reflective lighting (specular)
        reflected_ray = Ray(intersection_point, normalize_rows(reflection(ray.direction, surface_norm_vector)))
        color = color + self.shoot_ray(reflected_ray, reflection_depth + 1) * obj.material.specular

        return color

    def check_intersection(self, ray):
        """
        Checks if there is an intersection between
        the given ray and an object of the scene

        @return: point of intersection (if there is one)
        """

        intersection = None
        for obj in self.object_list:
            hit_dist = obj.intersection_parameter(ray)
            if hit_dist and hit_dist > 0 and (intersection is None):
                intersection = obj, hit_dist
        return intersection


class Camera:

    def __init__(self, e, up, c, field_of_view):
        """
        Creates a camera and all of its components

        @param e: point where the camera is mounted
        @param up: up-vector of the camera
        @param c: middle of the scene
        @param field_of_view: focal length
        """
        self.e = array_from_list(e)
        self.up = array_from_list(up)
        self.c = array_from_list(c)
        self.fieldOfView = field_of_view

        self.f = normalize_rows(self.c - self.e)
        self.s = normalize_rows(np.cross(self.f, self.up))
        self.u = np.cross(self.s, self.f)

        self.width = scene.width
        self.height = scene.height
        self.half_width = 0
        self.half_height = 0
        self.pixel_width = 0
        self.pixel_height = 0

        self.compute_pixel_size()
        if not scene.camera:
            scene.camera = self

    def compute_pixel_size(self):
        """Computes the size of one pixel"""

        alpha = self.fieldOfView / 2.0
        ratio = self.width / float(self.height)

        self.half_height = np.tan(alpha)
        self.half_width = ratio * self.half_height
        self.pixel_width = self.half_width / (self.width - 1) * 2
        self.pixel_height = self.half_height / (self.height - 1) * 2

    def build_ray(self, x, y):
        """Builds a ray"""
        x_comp = self.s * (x * self.pixel_width - self.half_width)
        y_comp = self.u * (y * self.pixel_height - self.half_height)
        return Ray(self.e, self.f + x_comp + y_comp)


class Material(object):
    def __init__(self, color, ambient=0.2, specular=0.5, lambert=0.8):
        """
        @param color: basic color
        @param ambient: ambient part of the texture
        @param specular: specular part of the texture (for reflections)
        @param lambert: lambert shading intensity
        """
        self.color = array_from_list(color)
        self.ambient = ambient
        self.specular = specular
        self.lambert = lambert

    def color_at(self, p):
        return self.color


class CheckedMaterial(object):
    def __init__(self, ambient=0.5, specular=0, lambert=0.8):
        """
        Checked texture

        @param ambient: ambient part of the texture
        @param specular: specular part of the texture (for reflections)
        @param lambert: lambert shading intensity
        """
        self.base_color = array_from_list([200, 200, 200])
        self.other_color = array_from_list([0, 0, 0])
        self.ambient = ambient
        self.specular = specular
        self.lambert = lambert
        self.check_size = 1

    def color_at(self, p):
        """Returns the color at the given point p (black or white)"""
        p * (1.0 / self.check_size)
        if np.mod((np.abs(p) + 0.5).astype(int).sum(), 2):
            return self.other_color
        return self.base_color


class Ray(object):
    def __init__(self, origin, direction):
        """
        Creates a ray

        @param origin: origin of the ray
        @param direction: direction vector of the ray
        """
        self.origin = array_from_list(origin)
        self.direction = normalize_rows(array_from_list(direction))

    def __repr__(self):
        return 'Ray(%s,%s)' % (repr(self.origin), repr(self.direction))

    def point_at_parameter(self, dist):
        """Returns a point on the ray at a given distance"""
        return self.origin + self.direction * dist


class Sphere(object):
    def __init__(self, center, radius, material):
        """
        Creates a sphere

        @param center: center of the sphere
        @param radius: radius of the sphere
        @param material: texture of the sphere
        """
        self.center = array_from_list(center)
        self.radius = radius
        self.material = material

    def __repr__(self):
        return 'Sphere(%s, %s)' % (repr(self.center), repr(self.radius))

    def intersection_parameter(self, ray):
        """Returns a point of intersection with the sphere if there is one"""
        co = self.center - ray.origin
        v = co.dot(ray.direction)
        discriminant = v * v - co.dot(co) + self.radius * self.radius
        if discriminant < 0:
            return None
        else:
            return v - np.sqrt(discriminant)

    def normal_at(self, p):
        """Returns the norm vector of the sphere at a given point on the surface"""
        return normalize_rows(p - self.center)


class Plane(object):
    def __init__(self, point, normal, material):
        """
        Creates a plane

        @param point: point on the plane
        @param normal: norm vector of the plane
        @param material: material of the plane
        """
        self.point = array_from_list(point)
        self.normal = array_from_list(normal)
        self.material = material

    def __repr(self):
        return 'Plane(%s,%s)' % (repr(self.point), repr(self.normal))

    def intersection_parameter(self, ray):
        """Returns a point of intersection with the plane if there is one"""
        op = ray.origin - self.point
        a = op.dot(self.normal)
        b = ray.direction.dot(self.normal)
        if b:
            return -a / b
        else:
            return None

    def normal_at(self, p):
        """Returns the norm vector of the sphere at a given point on the surface"""
        return self.normal


class Triangle(object):
    def __init__(self, a, b, c, material):
        """
        Creates a triangle

        @param a: point a
        @param b: point b
        @param c: point c
        @param material: texture of the triangle
        """
        self.a = array_from_list(a)
        self.b = array_from_list(b)
        self.c = array_from_list(c)
        self.u = self.b - self.a  # direction from point a to b
        self.v = self.c - self.a  # direction from point a to c
        self.material = material

    def __repr__(self):
        return 'Triangle(%s,%s, %s)' % (repr(self.a), repr(self.b), repr(self.c))

    def intersection_parameter(self, ray):
        """Returns a point of intersection with the triangle if there is one"""
        w = ray.origin - self.a
        dv = np.cross(ray.direction, self.v)
        dvu = dv.dot(self.u)
        if dvu == 0.0:
            return None
        wu = np.cross(w, self.u)
        r = dv.dot(w) / dvu
        s = wu.dot(ray.direction) / dvu
        if 0 <= r <= 1 and 0 <= s <= 1 and r + s <= 1:
            return wu.dot(self.v) / dvu
        else:
            return None

    def normal_at(self, p):
        """Returns the norm vector of the triangle"""
        return normalize_rows(np.cross(self.u, self.v)) * (-1)


def normalize_rows(x: np.ndarray):
    """
    Normalizes each row of the array x to have unit length

    @return: normalized array x
    """
    return x / np.linalg.norm(x, ord=None, axis=None, keepdims=True)


def reflection(ray, surface_norm_vector):
    """Returns a vector that describes the direction of a reflected ray"""
    surface_norm_vector = normalize_rows(surface_norm_vector)
    return ray - surface_norm_vector.dot(np.dot(2, ray.dot(surface_norm_vector)))


def array_from_list(lst):
    """Makes a numpy array out of a list of integers"""
    return np.array([lst[0], lst[1], lst[2]])


if __name__ == "__main__":

    start_time = time.time()

    # Create object_list
    object_list = [
        Sphere([3, 3, -10], 2, Material([255, 0, 0])),
        Sphere([-2, 3, -10], 2, Material([0, 255, 0])),
        Sphere([0.5, 7, -10], 2, Material([0, 0, 255])),
        Triangle([3, 3, -10], [-2, 3, -10], [0.5, 7, -10], Material([255, 255, 0])),
        Plane([0, 0, 0], [0, 1, 0], CheckedMaterial())
    ]

    # Create light_list
    light_list = [[30, 30, 10]]

    # Create a scene
    scene = Scene(WIDTH, HEIGHT, object_list, light_list)

    # Create a camera
    camera = Camera([1, 1.8, 10], [0, 1, 0], [1, 3, 0], 45)

    # Create a pool of processes and let them render the scene
    pool = mp.Pool(processes=PROCESSES)
    pixels = list(pool.map(scene.render, range(scene.width * scene.height)))

    # Draw the computed image and show it
    x = 0
    y = scene.height - 1
    for p in pixels:
        scene.image.putpixel((x, y), (int(p.item(0)), int(p.item(1)), int(p.item(2))))
        x += 1
        if x == scene.width:
            x = 0
            y -= 1

    scene.image.show()
    print("Time elapsed: " + str(time.time() - start_time) + " sec")
