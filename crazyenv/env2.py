#!/usr/bin/env python3

import gym
import numpy as np
from .sim import Simulator
from collections import deque

# TODO: ASSERT THAT WE START SUFFICIENTLY FAR FROM OBSTACLES.

class PFController():
    """ Potential field controller to model obstacles. """

    LAMBDA_1 = 1. # scale of A -> B field
    LAMBDA_2 = 0.02 # scale of obstacle avoidance field
    P_STAR = 1. # ignore obstacles more than this far away.
    
    def __init__(self, A, B, num_obstacles, obstacle_size_range):
        midpoint = (B + A) / 2
        location_radius = np.abs((B - A) * .2)

        self.target = B
        self.obstacles = [(np.random.normal(midpoint, location_radius),
                           np.random.normal(*obstacle_size_range))
                           for _ in range(num_obstacles)]

    def error(self, obs):
        """ calculate the error at a specified obs location. """
        f_1 = .5 * PFController.LAMBDA_1 * np.dot(self.target-obs, self.target-obs)
        f_2 = 0
        for obst in self.obstacles:
            dist = np.linalg.norm(obs - obst[0]) - np.linalg.norm(obst[1])
            if (dist < PFController.P_STAR):
                f_2 += .5 * PFController.LAMBDA_2 / (dist*dist)

        return f_1 + f_2

    def gradient(self, obs):
        """ calculate the gradient at a specified obs location. """
        v_1 = -1 * PFController.LAMBDA_1 * (obs - self.target)
        v_2 = np.array([0.]*3)
        for obst in self.obstacles:
            obst_rad = np.linalg.norm(obst[1]/2)
            dist = np.linalg.norm(obs - obst[0]) - obst_rad
            p_do = (obs - obst[0]) * (dist / (dist + obst_rad))
            if (dist < PFController.P_STAR):
                v_2 += (PFController.LAMBDA_2 / (dist**4)) * p_do
        return v_1 + v_2


class StaticObstEnv(gym.Env):
    """ Gym Env to train a single drone to travel between two arbitrary points. """

    act_dim = 3
    obs_dim = 6

    def __init__(self):
        self.max_speed = .1 #m/s in a given direction
        self.dt = 0.1

        self.renderer = None
        self.sim = Simulator(self.dt)

    def step(self, u):
        u = self.max_speed * np.array(u).astype(np.float64)
        self.sim.crazyflies[0].goTo(u, 0., 1., self.sim.t)
        self.sim.t += self.sim.dt

        obs = self._obs()
        reward = self._reward(obs, u) 
        return obs, reward, False, {}

    def _obs(self):
        pos = self.sim.crazyflies[0].position(self.sim.t)
        err = [self.pfc.error(pos)]
        grad = self.pfc.gradient(pos)
        return np.concatenate((pos, self.B, err, grad))

    def _reward(self, obs, u):
        grad = self.pfc.gradient(obs[:3])
        return -.5 * np.dot(u-grad, u-grad) # EASY MODE
        return self.pfc.error(obs[:3]) # HARD MODE

    def reset(self):
        self.sim.t = 0.
        self.B = np.random.normal([0,0,1], [.3]*3)
        self.A = np.random.normal(self.B, [2.]*3)

        while (np.linalg.norm(self.B-self.A) < 1.5 or np.linalg.norm(self.B - self.A) > 2.5):
            self.A = np.random.normal(self.B, [2.]*3)

        self.pfc = PFController(self.A, self.B, 5, [[.15]*3, [.05]*3])
        self.sim._init_cfs([{'id':1, 'pos':[self.A[0], self.A[1], 0]}])
        self.sim.crazyflies[0].takeoff(self.A[2], 10., -10)

        if self.renderer is not None:
            self.renderer.update(self.sim.t, self.sim.crazyflies)

        return self._obs()

    def render(self):
        if self.renderer is None:
            from .vis.visVispy import VisVispy
            self.renderer = VisVispy()
        self.renderer.update(self.sim.t, self.sim.crazyflies, 
            spheres=[(self.A, '#FF0000'), (self.B, '#0000FF')],
            obstacles=self.pfc.obstacles,
            crumb=self.sim.crazyflies[0].position(self.sim.t))

    def close(self): 
        if self.renderer is not None:
            self.renderer.close()
        self.renderer = None
