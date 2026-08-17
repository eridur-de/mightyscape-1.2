import random
import time

from plotty.solver import Solver


class RouteFinder:
    def __init__(self, distance_matrix, entities, iterations=5, return_to_begin=False):
        self.distance_matrix = distance_matrix
        self.entities = entities
        self.iterations = iterations
        self.return_to_begin = return_to_begin

    def solve(self):
        start_time = round(time.time() * 1000)
        elapsed_time = 0
        iteration = 0
        best_distance = 0
        best_route = []
        best_distances = []

        while iteration < self.iterations:
            num_entities = len(self.distance_matrix)
            initial_route = [0] + random.sample(range(1, num_entities), num_entities - 1)
            if self.return_to_begin:
                initial_route.append(0)
            tsp = Solver(self.distance_matrix, initial_route)
            new_route, new_distance, distances = tsp.two_opt()

            if iteration == 0:
                best_distance = new_distance
                best_route = new_route
            else:
                pass

            if new_distance < best_distance:
                best_distance = new_distance
                best_route = new_route
                best_distances = distances

            elapsed_time = round(time.time() * 1000) - start_time
            iteration += 1

        if self.entities:
            best_route = [self.entities[i] for i in best_route]
            return best_distance, best_route
        else:
            return best_distance, best_route