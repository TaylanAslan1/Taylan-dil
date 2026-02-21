import math

__all__ = [
    "mat_topla",
    "mat_cikar",
    "mat_carp",
    "mat_bol",
    "mat_us",
    "mat_kok",
]


def mat_topla(a, b):
    return a + b


def mat_cikar(a, b):
    return a - b


def mat_carp(a, b):
    return a * b


def mat_bol(a, b):
    return a / b


def mat_us(a, b):
    return a ** b


def mat_kok(a):
    return math.sqrt(a)
