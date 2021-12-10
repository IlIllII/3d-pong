import pygame
from OpenGL.GL import *

from python_graphics_3d.core.base import Base
from python_graphics_3d.core.camera import Camera
from python_graphics_3d.core.mesh import Mesh
from python_graphics_3d.core.render_target import RenderTarget
from python_graphics_3d.core.renderer import Renderer
from python_graphics_3d.core.scene import Scene
from python_graphics_3d.effects.additive_blend_effect import AdditiveBlendEffect
from python_graphics_3d.effects.horizontal_blur_effect import HorizontalBlurEffect
from python_graphics_3d.effects.vertical_blur_effect import VerticalBlurEffect
from python_graphics_3d.extras.movement_rig import MovementRig
from python_graphics_3d.extras.postprocessor import Postprocessor
from python_graphics_3d.geometries.box_geometry import BoxGeometry
from python_graphics_3d.geometries.sphere_geometry import SphereGeometry
from python_graphics_3d.lights.point_light import PointLight
from python_graphics_3d.materials.lambert_material import LambertMaterial
from python_graphics_3d.materials.phong_material import PhongMaterial
from python_graphics_3d.materials.surface_material import SurfaceMaterial

CAMERA_DISTANCE = 10
BALL_RADIUS = 0.25
TABLE_HEIGHT = 10
TABLE_WIDTH = 15
TABLE_DEPTH = 1
WALL_WIDTH = TABLE_WIDTH
WALL_HEIGHT = 1
WALL_DEPTH = 1
PADDLE_WIDTH = 1
PADDLE_HEIGHT = 3
PADDLE_DEPTH = 1
PLAYER_X = -((TABLE_WIDTH / 2) + (PADDLE_WIDTH / 2))
CPU_X = (TABLE_WIDTH / 2) + (PADDLE_WIDTH / 2)
TOP_WALL_POSITION = (TABLE_HEIGHT / 2) + (WALL_HEIGHT / 2)
BOTTOM_WALL_POSITION = -(TABLE_HEIGHT / 2) - (WALL_HEIGHT / 2)

GLOW_ON = True
BLUR_RADIUS = 25
GLOW_STRENGTH = 3
BALL_SPEED = 30


point_light_attenuation = [1, 0, 0.0]

ball_colors = [
    [1, 1, 1],
    [1, 0, 0],
    [1, 1, 0],
    [1, 0, 1],
    [0, 1, 0],
    [0, 1, 1],
    [0, 0, 1],
]


class Test(Base):
    def initialize(self):
        self.scene = Scene()
        self.renderer = Renderer()
        self.camera = Camera(angle_of_view=60, aspect_ratio=1920 / 1080)
        self.rig = MovementRig()
        self.rig.add(self.camera)
        self.scene.add(self.rig)
        self.rig.set_position([0, 0, CAMERA_DISTANCE])
        self.ball_speed = BALL_SPEED / self.fps
        self.ball_direction = [1, 0.5, 0]
        self.color = 0

        ball_geometry = SphereGeometry(radius=BALL_RADIUS)
        floor_geometry = BoxGeometry(TABLE_WIDTH, TABLE_HEIGHT, TABLE_DEPTH)
        wall_geometry = BoxGeometry(WALL_WIDTH, WALL_HEIGHT, WALL_DEPTH)
        paddle_geometry = BoxGeometry(PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_DEPTH)

        ball_material = (
            PhongMaterial()
        )  # SurfaceMaterial() FlatMaterial() LambertMaterial()
        floor_material = (
            LambertMaterial()
        )  # SurfaceMaterial() PhongMaterial() LambertMaterial()
        wall_material = PhongMaterial()
        paddle_material = PhongMaterial()

        floor = Mesh(floor_geometry, floor_material)
        wall_top = Mesh(wall_geometry, wall_material)
        wall_bottom = Mesh(wall_geometry, wall_material)
        self.ball = Mesh(ball_geometry, ball_material)
        self.player_paddle = Mesh(paddle_geometry, paddle_material)
        self.cpu_paddle = Mesh(paddle_geometry, paddle_material)

        self.scene.add(floor)
        self.scene.add(wall_top)
        self.scene.add(wall_bottom)
        self.scene.add(self.ball)
        self.scene.add(self.player_paddle)
        self.scene.add(self.cpu_paddle)

        floor.set_position([0, 0, -1])

        wall_top.set_position([0, TOP_WALL_POSITION, 0])
        wall_bottom.set_position([0, BOTTOM_WALL_POSITION, 0])

        self.player_paddle.set_position([PLAYER_X, 0, 0])
        self.cpu_paddle.set_position([CPU_X, 0, 0])

        # * Lights
        # self.ambient_light = AmbientLight(color=[0.1 , 0.1, 0.1])
        # self.scene.add(self.ambient_light)
        # self.directional_light = DirectionalLight(color=[0.2, 0.2, 0.2], direction=[0, 0, -1])
        # self.scene.add(self.directional_light)
        self.point_light = PointLight(attenuation=point_light_attenuation)
        self.scene.add(self.point_light)

        # * Glow scene for lighting the ball

        if GLOW_ON:
            self.glow_scene = Scene()

            self.white_material = SurfaceMaterial({"base_color": [1, 1, 1]})
            self.glow_sphere = Mesh(ball_geometry, self.white_material)
            self.glow_sphere.transform = self.ball.transform
            self.glow_scene.add(self.glow_sphere)
            self.glow_scene.add(self.cpu_paddle)
            self.glow_scene.add(self.player_paddle)
            self.glow_scene.add(self.glow_sphere)

            glow_target = RenderTarget(resolution=self.screen.get_size())
            self.glow_pass = Postprocessor(
                self.renderer, self.glow_scene, self.camera, glow_target
            )

            # Bloom effect
            # self.glow_pass.add_effect(BrightFilterEffect())
            self.glow_pass.add_effect(
                HorizontalBlurEffect(
                    texture_size=self.screen.get_size(), blur_radius=BLUR_RADIUS
                )
            )
            self.glow_pass.add_effect(
                VerticalBlurEffect(
                    texture_size=self.screen.get_size(), blur_radius=BLUR_RADIUS
                )
            )

            self.combo_pass = Postprocessor(self.renderer, self.scene, self.camera)
            self.combo_pass.add_effect(
                AdditiveBlendEffect(
                    glow_target.texture,
                    original_strength=1,
                    blend_strength=GLOW_STRENGTH,
                )
            )
            # self.combo_pass.add_effect(PixelateEffect())

    def update(self):

        mouse_y = -(
            pygame.mouse.get_pos()[1]
            / (self.screen.get_size()[1])
            * (TABLE_HEIGHT - 2 * WALL_HEIGHT)
            - ((TABLE_HEIGHT - 2 * WALL_HEIGHT) / 2)
        )

        self.player_paddle.set_position([PLAYER_X, mouse_y, 0])
        ball_x, ball_y, _ = self.ball.get_position()
        new_ball_x, new_ball_y = (
            self.ball_speed * self.ball_direction[0] + ball_x,
            self.ball_speed * self.ball_direction[1] + ball_y,
        )

        if (
            new_ball_x < -(TABLE_WIDTH / 2) + BALL_RADIUS
            and abs(new_ball_y - mouse_y) <= PADDLE_WIDTH + BALL_RADIUS
            and self.ball_direction[0] < 0
        ):
            self.ball_direction[0] *= -1

            self.color = (self.color + 1) % len(ball_colors)
            self.white_material.set_properties({"base_color": ball_colors[self.color]})
            self.point_light.color = ball_colors[self.color]

        elif new_ball_x > (TABLE_WIDTH / 2) - BALL_RADIUS:
            self.ball_direction[0] *= -1

            self.color = (self.color + 1) % len(ball_colors)
            self.white_material.set_properties({"base_color": ball_colors[self.color]})
            self.point_light.color = ball_colors[self.color]
        ball_x += self.ball_speed * self.ball_direction[0]

        if new_ball_y < -(TABLE_HEIGHT / 2):
            self.ball_direction[1] *= -1
        elif new_ball_y > (TABLE_HEIGHT / 2):
            self.ball_direction[1] *= -1
        ball_y += self.ball_speed * self.ball_direction[1]

        self.ball.set_position([ball_x, ball_y, 0])
        self.cpu_paddle.set_position([CPU_X, self.ball.get_position()[1], 0])
        self.point_light.transform = self.ball.transform
        self.rig.update(self.input, self.delta_time)
        self.renderer.render(self.scene, self.camera)

        if GLOW_ON:
            self.glow_pass.render()
            self.combo_pass.render()


Test(screen_size=[0, 0], fps=144).run()
