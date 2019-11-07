import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np

control_points = []
bspline_points = []

mode = 1

DEFAULT_N = 2
n = DEFAULT_N

m = 50

curve_points = 2

degree = 3


class GLFWWindow:
    def __init__(self):
        # save current working directory
        cwd = os.getcwd()

        # Initialize the library
        if not glfw.init():
            return

        # restore cwd
        os.chdir(cwd)

        # buffer hints
        glfw.window_hint(glfw.DEPTH_BITS, 32)
        glfw.window_hint(glfw.RESIZABLE, False)

        # define desired frame rate
        self.frame_rate = 100

        # make a window
        self.width, self.height = 600, 600
        self.aspect = self.width / float(self.height)
        self.window = glfw.create_window(self.width, self.height, "BSplineViewer", None, None)
        if not self.window:
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(self.window)

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)
        glfw.set_cursor_pos_callback(self.window, self.mouse_moved)
        glfw.set_key_callback(self.window, self.on_keyboard)

        # exit flag
        self.exitNow = False

        # show polygon
        self.show_control_polygon = True

        # shift_pressed flag
        self.left_shift_pressed = False

        # translation flag
        self.do_translation = False

        self.control_index = None

        self.mouse_pos = None

        # set up opengl stuff
        glEnable(GL_LINE_SMOOTH)
        glClearColor(1, 1, 1, 1)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.width, self.height, 0)
        glMatrixMode(GL_MODELVIEW)

        # set point size
        glPointSize(10)

        print_status()

    def on_mouse_button(self, win, button, action, mods):
        global n, m, mode
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                x, y = glfw.get_cursor_pos(win)
                if not control_points:
                    control_points.append([x, y])
                    n += 10
                    m += 10

                else:
                    self.control_index = None
                    for p in control_points:
                        if (p[0] - 10) < x < (p[0] + 10) and (p[1] - 10) < y < (p[1] + 10):
                            self.control_index = control_points.index([p[0], p[1]])
                            self.do_translation = True

                    if self.control_index is None:
                        control_points.append([x, y])
                        n += 10
                        m += 10
                        draw_curve(mode)

            if action == glfw.RELEASE:
                self.do_translation = False
                self.control_index = None

        if button == glfw.MOUSE_BUTTON_RIGHT:
            if action == glfw.PRESS:
                if self.control_index is not None:
                    control_points.pop(self.control_index)
                    draw_curve(mode)

    def mouse_moved(self, win, x, y):
        if self.do_translation:
            control_points[self.control_index] = [x, y]
            draw_curve(mode)

        self.mouse_pos = [x, y]
        self.control_index = None
        for p in control_points:
            if (p[0] - 10) < x < (p[0] + 10) and (p[1] - 10) < y < (p[1] + 10):
                self.control_index = control_points.index([p[0], p[1]])

    def on_keyboard(self, win, key, scancode, action, mods):
        global m, n, degree, mode

        if key == glfw.KEY_LEFT_SHIFT:
            if action == glfw.PRESS:
                self.left_shift_pressed = True
            elif action == glfw.RELEASE:
                self.left_shift_pressed = False

        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True

            if key == glfw.KEY_C:
                n = DEFAULT_N
                control_points.clear()
                bspline_points.clear()
                self.show_control_polygon = True

            if key == glfw.KEY_H:
                self.show_control_polygon = not self.show_control_polygon

            if key == glfw.KEY_BACKSPACE:
                control_points.pop(-1)
                draw_curve(mode)

            if key == glfw.KEY_M:
                if self.left_shift_pressed:
                    n += 10
                    m += 10
                    draw_curve(mode)
                    print_amount_points()
                else:
                    if mode:
                        if m > len(control_points):
                            m -= 10
                    else:
                        if n > len(control_points):
                            n -= 10
                    draw_curve(mode)
                    print_amount_points()

            if key == glfw.KEY_K:
                if self.left_shift_pressed:
                    degree += 1
                    draw_curve(mode)
                    print_degree()
                else:
                    if degree > 2:
                        degree -= 1
                    draw_curve(mode)
                    print_degree()

            if key == glfw.KEY_1:
                mode = not mode
                draw_curve(mode)
                print_mode()

            if key == glfw.KEY_S:
                print_status()

    def run(self):
        # initializer timer
        glfw.set_time(0.0)
        t = 0.0
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # update every x seconds
            curr_t = glfw.get_time()
            if curr_t - t > 1.0 / self.frame_rate:
                # update time
                t = curr_t

                glClear(GL_COLOR_BUFFER_BIT)
                glLineWidth(1)
                glEnableClientState(GL_VERTEX_ARRAY)

                # draw spline
                glVertexPointerf(bspline_points)
                glLineWidth(4)
                #glDrawArrays(GL_POINTS, 0, len(bspline_points))
                glDrawArrays(GL_LINE_STRIP, 0, len(bspline_points))

                # draw points
                glColor3f(0, 0, 1)
                glVertexPointerf(control_points)
                if self.show_control_polygon:
                    if len(control_points) >= 2:
                        # draw control polygon
                        glLineWidth(1)
                        glDrawArrays(GL_LINE_STRIP, 0, len(control_points))

                    # draw regular control points
                    glDrawArrays(GL_POINTS, 0, len(control_points))

                    # draw
                    if self.control_index is not None:
                        # draw mouse control point
                        glColor3f(1, 0.5, 0)
                        glPointSize(20)
                        glDrawArrays(GL_POINTS, self.control_index, 1)
                        glColor3f(0, 0, 1)
                        glPointSize(10)

                glDisableClientState(GL_VERTEX_ARRAY)
                glfw.swap_buffers(self.window)

                # Poll for and process events
                glfw.poll_events()
        # end
        glfw.terminate()


def draw_curve(mode):
    """ draw bezier curve defined by (control-)points """
    global bspline_points, degree, m

    bezier_point_list = []
    if mode:
        knotvector = calc_knot_vector()
        if knotvector:
            for i in range(m+1):
                t = max(knotvector) * (i / m)
                r = None

                # calc parameter r
                for j in range(len(knotvector)):
                    if t == max(knotvector):
                        r = len(knotvector) - degree - 1
                        break
                    if knotvector[j] <= t < knotvector[j + 1]:
                        r = j
                        break

                boor_point = deboor(degree, np.array(control_points), knotvector, t, degree-1, r)
                bezier_point_list.append(boor_point)

    else:
        if len(control_points) > 1:
            for i in range(0, n + 1):
                t = i / n
                bezier_point_list.append(casteljau(np.array(control_points), t))

    bspline_points = [list(x) for x in bezier_point_list]


def deboor(degree, controlpoints, knot_vector, t, j, i):
    if j == 0:
        return controlpoints[i]

    if knot_vector[i - j + degree] - knot_vector[i] == 0:
        alpha = 0
    else:
        alpha = (t - knot_vector[i]) / (knot_vector[i - j + degree] - knot_vector[i])

    return (1 - alpha) * deboor(degree, controlpoints, knot_vector, t, j-1, i-1) \
        + alpha * deboor(degree, controlpoints, knot_vector, t, j-1, i)


def casteljau(bezier_points, t):
    if len(bezier_points) == 1:
        return bezier_points[0]
    new_point_list = []
    for i in range(len(bezier_points) - 1):
        new_point_list.append((1 - t) * bezier_points[i] + t * bezier_points[i + 1])

    return casteljau(new_point_list, t)


def calc_knot_vector():
    points_len = len(control_points) - 1
    if points_len < degree:
        return None

    start = [0 for x in range(degree)]
    middle = [x for x in range(1, points_len - (degree - 2))]
    end = [points_len - (degree - 2) for x in range(degree)]
    return start + middle + end


def print_status():
    print("\n------Status-------")
    print_mode()
    print_degree()
    print_amount_points()


def print_mode():
    if mode:
        print("mode: de_Boor")
    else:
        print("mode: de_Casteljau")


def print_degree():
    print("Degree:", degree-1)


def print_amount_points():
    if mode:
        print("Curve points:", m)
    else:
        print("Curve points:", n)


if __name__ == '__main__':
    render_win = GLFWWindow()
    render_win.run()
