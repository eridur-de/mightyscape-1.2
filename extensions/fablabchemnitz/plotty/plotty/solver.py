import itertools
import numpy as np


class Solver:
    def __init__(self, distance_matrix, initial_route):
        self.distance_matrix = distance_matrix
        self.num_cities = len(self.distance_matrix)
        self.initial_route = initial_route
        self.best_route = []
        self.best_distance = 0
        self.distances = []

    def update(self, new_route, new_distance):
        self.best_distance = new_distance
        self.best_route = new_route
        return self.best_distance, self.best_route

    def exhaustive_search(self):
        self.best_route = [0] + list(range(1, self.num_cities))
        self.best_distance = self.calculate_path_dist(self.distance_matrix, self.best_route)

        for new_route in itertools.permutations(list(range(1, self.num_cities))):
            new_distance = self.calculate_path_dist(self.distance_matrix, [0] + list(new_route[:]))

            if new_distance < self.best_distance:
                self.update([0] + list(new_route[:]), new_distance)
                self.distances.append(self.best_distance)

        return self.best_route, self.best_distance, self.distances

    def two_opt(self, improvement_threshold=0.01):
        self.best_route = self.initial_route
        self.best_distance = self.calculate_path_dist(self.distance_matrix, self.best_route)
        improvement_factor = 1
        
        while improvement_factor > improvement_threshold:
            previous_best = self.best_distance
            for swap_first in range(1, self.num_cities - 2):
                for swap_last in range(swap_first + 1, self.num_cities - 1):
                    before_start = self.best_route[swap_first - 1]
                    start = self.best_route[swap_first]
                    end = self.best_route[swap_last]
                    after_end = self.best_route[swap_last+1]
                    before = self.distance_matrix[before_start][start] + self.distance_matrix[end][after_end]
                    after = self.distance_matrix[before_start][end] + self.distance_matrix[start][after_end]
                    if after < before:
                        new_route = self.swap(self.best_route, swap_first, swap_last)
                        new_distance = self.calculate_path_dist(self.distance_matrix, new_route)
                        self.update(new_route, new_distance)

            improvement_factor = 1 - self.best_distance/previous_best
        return self.best_route, self.best_distance, self.distances

    @staticmethod
    def calculate_path_dist(distance_matrix, path):
        """
        This method calculates the total distance between the first city in the given path to the last city in the path.
        """
        path_distance = 0
        for ind in range(len(path) - 1):
            path_distance += distance_matrix[path[ind]][path[ind + 1]]
        return float("{0:.2f}".format(path_distance))

    @staticmethod
    def swap(path, swap_first, swap_last):
        path_updated = np.concatenate((path[0:swap_first],
                                       path[swap_last:-len(path) + swap_first - 1:-1],
                                       path[swap_last + 1:len(path)]))
        return path_updated.tolist()
