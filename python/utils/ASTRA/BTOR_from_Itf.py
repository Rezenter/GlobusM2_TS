import math

Itf = 91096
Bt: float = Itf * 1.26e-6 * 16 / (math.tau * 0.36)
#                  vacuum   coils            R

print(Bt)
