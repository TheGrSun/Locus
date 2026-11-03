"""Sample textbook motion from formulas. Angles are degrees. Time is seconds."""

import math

import numpy as np

from .formulas import T, parse_component


def _column(values) -> list[float | None]:
    cleaned: list[float | None] = []
    for value in np.ravel(values):
        number = float(value)
        cleaned.append(round(number, 6) if math.isfinite(number) else None)
    return cleaned


def projectile(speed: float, angle_degrees: float, gravity: float = 9.81, samples: int = 240) -> dict:
    if not all(math.isfinite(value) for value in (speed, angle_degrees, gravity)):
        raise ValueError("Projectile inputs must be finite numbers.")
    if speed <= 0 or speed > 10000 or gravity <= 0 or gravity > 1000:
        raise ValueError("Use a positive launch speed and gravity, for example speed 20 and g 9.81.")
    if not -89 <= angle_degrees <= 90:
        raise ValueError("Launch angle must be between -89 and 90 degrees.")
    angle = math.radians(angle_degrees)
    vx = speed * math.cos(angle)
    vy = speed * math.sin(angle)
    if vy > 0:
        duration = 2 * vy / gravity
        assumptions = "Flat ground, no air resistance, y is up, launch from the origin."
    else:
        # vy <= 0 never returns to the ground; drawing an extra second would disagree with the flight.
        duration = 0.0
        assumptions = "The launch does not rise, so it leaves the ground immediately and the plot stays at the origin."
    times = np.linspace(0, duration, samples)
    xs = vx * times
    ys = vy * times - 0.5 * gravity * times**2
    return {
        "scenario": "projectile",
        "assumptions": assumptions,
        "time": _column(times),
        "x": _column(xs),
        "y": _column(ys),
        "time_of_flight": round(duration, 6),
        "range": round(vx * duration, 6),
        "max_height": round((vy * vy) / (2 * gravity), 6) if vy > 0 else 0.0,
        "gravity": gravity,
    }


def oscillator(amplitude: float, angular_frequency: float, phase: float = 0.0, cycles: float = 2.0, samples: int = 240) -> dict:
    if not all(math.isfinite(value) for value in (amplitude, angular_frequency, phase, cycles)):
        raise ValueError("Oscillator inputs must be finite numbers.")
    if angular_frequency == 0 or abs(angular_frequency) > 10000 or abs(amplitude) > 10000 or not 0.25 <= cycles <= 8:
        raise ValueError("Use a nonzero angular frequency and between 0.25 and 8 cycles.")
    period = 2 * math.pi / abs(angular_frequency)
    times = np.linspace(0, cycles * period, samples)
    xs = amplitude * np.cos(angular_frequency * times + phase)
    return {
        "scenario": "oscillator",
        "assumptions": "x = A cos(omega t + phase), drawn on the x axis. No damping.",
        "time": _column(times),
        "x": _column(xs),
        "y": _column(np.zeros_like(xs)),
        "period": round(period, 6),
        "amplitude": amplitude,
        "angular_frequency": angular_frequency,
    }


def motion(x_formula: str, y_formula: str, t_range: list[float], samples: int = 240) -> dict:
    xs_expr = parse_component(x_formula)
    ys_expr = parse_component(y_formula)
    times = np.linspace(*t_range, samples)
    import sympy as sp

    def evaluate(expr):
        with np.errstate(all="ignore"):
            values = np.asarray(sp.lambdify(T, expr, modules="numpy")(times), dtype=float)
        return np.broadcast_to(values, times.shape)

    return {
        "scenario": "motion",
        "assumptions": "The expressions are positions in meters with t in seconds.",
        "time": _column(times),
        "x": _column(evaluate(xs_expr)),
        "y": _column(evaluate(ys_expr)),
        "formulas": {"x": x_formula, "y": y_formula},
    }
