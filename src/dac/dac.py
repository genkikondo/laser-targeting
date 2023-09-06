from abc import ABC, abstractmethod


class LaserDAC(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def set_color(self, r, g, b, i):
        pass

    @abstractmethod
    def add_point(self, x, y):
        pass

    @abstractmethod
    def clear_points(self):
        pass

    @abstractmethod
    def play(self, fps, pps, transition_duration_ms):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def close(self):
        pass
