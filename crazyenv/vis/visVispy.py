import os
import math
import numpy as np

from vispy import scene, app, io
from vispy.color import Color
from vispy.visuals import transforms
from vispy.scene.cameras import TurntableCamera


class VisVispy:
    def __init__(self):
        self.canvas = scene.SceneCanvas(keys='interactive', size=(1900, 1145), show=True, config=dict(samples=4), resizable=True)

        # Set up a viewbox to display the cube with interactive arcball
        self.view = self.canvas.central_widget.add_view()
        self.view.bgcolor = '#efefef'
        self.view.camera = TurntableCamera(fov=60.0, elevation=30.0, azimuth=280.0)

        # add a colored 3D axis for orientation
        axis = scene.visuals.XYZAxis(parent=self.view.scene)
        self.cfs = []
        self.spheres = []

        # ground = scene.visuals.Plane(6.0, 6.0, direction="+z", color=(0.3, 0.3, 0.3, 1.0), parent=self.view.scene)


    def update(self, t, crazyflies, spheres=[]):
        if len(self.cfs) == 0:
            verts, faces, normals, nothin = io.read_mesh(os.path.join(os.path.dirname(__file__), "crazyflie2.obj.gz"))
            for i in range(0, len(crazyflies)):
                mesh = scene.visuals.Mesh(vertices=verts, shading='smooth', faces=faces, parent=self.view.scene)
                mesh.transform = transforms.MatrixTransform()
                self.cfs.append(mesh)

        if spheres:
            if not self.spheres:
                for i,s in enumerate(spheres):
                    self.spheres.append(scene.visuals.Sphere(radius=.02, color='#FF0000' if i else '#0000FF', parent=self.view.scene))
                    self.spheres[-1].transform = transforms.STTransform(translate=s)
            for i,s in enumerate(spheres):
                self.spheres[i].transform.translate = s

        for i in range(0, len(self.cfs)):
            x, y, z = crazyflies[i].position(t)
            roll, pitch, yaw = crazyflies[i].rpy(t)
            self.cfs[i].transform.reset()
            self.cfs[i].transform.rotate(90, (1, 0, 0))
            self.cfs[i].transform.rotate(math.degrees(roll), (1, 0, 0))
            self.cfs[i].transform.rotate(math.degrees(pitch), (0, 1, 0))
            self.cfs[i].transform.rotate(math.degrees(yaw), (0, 0, 1))
            self.cfs[i].transform.scale((0.001, 0.001, 0.001))
            self.cfs[i].transform.translate((x, y, z))

        self.canvas.app.process_events()

    def close(self):
        self.canvas.close()
