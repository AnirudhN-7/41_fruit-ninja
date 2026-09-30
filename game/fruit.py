import math


class Fruit:
    def __init__(self, x, y, vx, vy, gravity, radius=28, kind="fruit"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.gravity = gravity
        self.radius = radius
        self.kind = kind  # "fruit" or "bomb"
        self.sliced = False

    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy

    def contains_point(self, x, y):
        return math.hypot(self.x - x, self.y - y) <= self.radius

    def intersects_segment(self, start, end):
        """
        Check whether the line segment from start to end
        intersects the circular fruit.

        This handles fast mouse swipes where the mouse can
        move from one side of the fruit to the other between
        two MOUSEMOTION events.
        """

        x1, y1 = start
        x2, y2 = end

        cx = self.x
        cy = self.y

        dx = x2 - x1
        dy = y2 - y1

        # If there was effectively no movement,
        # fall back to checking the point.
        length_squared = dx * dx + dy * dy

        if length_squared == 0:
            return self.contains_point(x1, y1)

        # Project the fruit center onto the line segment.
        t = (
            (cx - x1) * dx +
            (cy - y1) * dy
        ) / length_squared

        # Clamp projection to the actual segment.
        t = max(0.0, min(1.0, t))

        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        distance = math.hypot(
            cx - closest_x,
            cy - closest_y
        )

        return distance <= self.radius

    def off_screen(self, height):
        return self.y - self.radius > height
