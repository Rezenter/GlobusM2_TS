import math

std = 2.55

err2 = math.pow(std, 2) * 6715 * 0.0625 - 1.14e4 * 0.0625

print(math.sqrt(err2))