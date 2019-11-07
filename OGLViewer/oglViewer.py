from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.arrays import vbo
import sys
import os
import numpy as np

EXIT = -1
FIRST = 0

model_data = []
points = []

bounding_box = ()
obj_origin = ()
scale = 0

axes = [
   np.array([-10, 0, 0]),
   np.array([10, 0, 0]),
   np.array([0, -10, 0]),
   np.array([0, 10, 0]),
   np.array([0, 0, -10]),
   np.array([0, 0, 10])
]

vectors = [
   np.array([0, 0, 0]),
   np.array([1, 0, 0]),
   np.array([0, 1, 0])
]

indices = [1, 2, 3]
index_buffer = None
vector_buffer = None

axes_buffer = None

point_buffer = None

def init(width, height):
   """ Initialize an OpenGL window """
   global point_buffer, axes_buffer, vector_buffer, index_buffer
   glClearColor(50.0, 50.0, 0.0, 0.0)       #background color
   glMatrixMode(GL_PROJECTION)              #switch to projection matrix
   glLoadIdentity()                         #set to 1
   #glOrtho(-1.5, 1.5, -1.5, 1.5, -1.0, 1.0) #multiply with new p-matrix
   gluPerspective(45, float(width) / height, 0.1, 100)
   glMatrixMode(GL_MODELVIEW)               #switch to modelview matrix
   glPointSize(2.0)
   point_buffer = vbo.VBO(np.array(points, 'f'))
   axes_buffer = vbo.VBO(np.array(axes, 'f'))

   index_buffer = vbo.VBO(np.array(indices, 'uint'))
   vector_buffer = vbo.VBO(np.array(vectors, 'f'))

   # initial translate and scale object to -1, 1 (origin)
   glScalef(scale, scale, scale)
   glTranslatef(-obj_origin[0], -obj_origin[1], -obj_origin[2])


def display():
   """ Render all objects"""
   global obj_origin, scale
   glClear(GL_COLOR_BUFFER_BIT) #clear screen
   glColor(0.0, 0.0, 1.0)       #render stuff


   # draw points
   point_buffer.bind()
   glVertexPointerf(point_buffer)
   glEnableClientState(GL_VERTEX_ARRAY)

   glDrawArrays(GL_POINTS, 0, len(points))

   point_buffer.unbind()
   glDisableClientState(GL_VERTEX_ARRAY)

   # draw coordinate axes
   glPushMatrix()
   glLoadIdentity()
   axes_buffer.bind()
   glVertexPointerf(axes_buffer)
   glEnableClientState(GL_VERTEX_ARRAY)
   glDrawArrays(GL_LINES, 0, len(axes))

   axes_buffer.unbind()
   glDisableClientState(GL_VERTEX_ARRAY)
   glPopMatrix()

   glutSwapBuffers()
   glFlush()


def reshape(width, height):
   """ adjust projection matrix to window size"""
   glViewport(0, 0, width, height)
   glMatrixMode(GL_PROJECTION)
   glLoadIdentity()
   if width <= height:
       glOrtho(-1.5, 1.5,
               -1.5*height/width, 1.5*height/width,
               -1.0, 1.0)
   else:
       glOrtho(-1.5*width/height, 1.5*width/height,
               -1.5, 1.5,
               -1.0, 1.0)
   glMatrixMode(GL_MODELVIEW)


def keyPressed(key, x, y):
   """ handle keypress events """
   if key == b'q':  # b'q' = Q
      #glDeleteBuffers(1, buffer)
      sys.exit()

   if key == b'x':
      glTranslatef(obj_origin[0], obj_origin[1], obj_origin[2])
      glRotatef(22.5, 1.0, 0, 0)
      glTranslatef(-obj_origin[0], -obj_origin[1], -obj_origin[2])
      display()
   if key == b'y':
      glTranslatef(obj_origin[0], obj_origin[1], obj_origin[2])
      glRotatef(22.5, 0, 1.0, 0)
      glTranslatef(-obj_origin[0], -obj_origin[1], -obj_origin[2])
      display()
   if key == b'z':
      glTranslatef(obj_origin[0], obj_origin[1], obj_origin[2])
      glRotatef(22.5, 0, 0, 1.0)
      glTranslatef(-obj_origin[0], -obj_origin[1], -obj_origin[2])
      display()


def mouse(button, state, x, y):
   """ handle mouse events """
   if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
       print("left mouse button pressed at ", x, y)


def mouseMotion(x,y):
   """ handle mouse motion """
   print("mouse motion at ", x, y)


def menu_func(value):
   """ handle menue selection """
   print("menue entry ", value, "choosen...")
   if value == EXIT:
       sys.exit()
   glutPostRedisplay()


def import_data(file):
   with open(file) as f:
      for line in f:
         line = list(map(float, line.strip().split()))
         model_data.append(line)
         points.append(np.array([line[0], line[1], line[2], 1]))
   compute_bounding_box()
   compute_scale()
   print("test")


def compute_bounding_box():
   global bounding_box, obj_origin
   temp = [list(map(min, zip(*model_data))), list(map(max, zip(*model_data)))]
   bounding_box = (np.array([temp[0][0], temp[0][1], temp[0][2]]), np.array([temp[1][0], temp[1][1], temp[1][2]]))

   min_array = bounding_box[0]
   max_array = bounding_box[1]

   mid_x = min_array[0] + ((max_array[0] - min_array[0]) / 2)
   mid_y = min_array[1] + ((max_array[1] - min_array[1]) / 2)
   mid_z = min_array[2] + ((max_array[2] - min_array[2]) / 2)

   obj_origin = (mid_x, mid_y, mid_z)


def compute_scale():
   global bounding_box, scale
   # calculate scale
   scaleX = abs((bounding_box[1][0] - bounding_box[0][0]))
   scaleY = abs((bounding_box[1][1] - bounding_box[0][1]))
   scaleZ = abs((bounding_box[1][2] - bounding_box[0][2]))

   scale = 2 / max(scaleX, scaleY, scaleZ)


def main():
   # Hack for Mac OS X
   cwd = os.getcwd()
   glutInit(sys.argv)
   os.chdir(cwd)

   glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
   glutInitWindowSize(500, 500)
   glutCreateWindow("OGLPointViewer")

   glutDisplayFunc(display)     #register display function
   glutReshapeFunc(reshape)     #register reshape function
   glutKeyboardFunc(keyPressed) #register keyboard function
   glutMouseFunc(mouse)         #register mouse function
   glutMotionFunc(mouseMotion)  #register motion function
   glutCreateMenu(menu_func)    #register menu function




   glutAddMenuEntry("First Entry", FIRST) #Add a menu entry
   glutAddMenuEntry("EXIT", EXIT)         #Add another menu entry
   glutAttachMenu(GLUT_RIGHT_BUTTON)     #Attach mouse button to menue

   import_data("cow_points.raw")

   init(500,500) #initialize OpenGL state

   glutMainLoop() #start even processing


if __name__ == "__main__":
   main()
