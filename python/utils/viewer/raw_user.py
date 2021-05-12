import raw

poly_ind = 1
event_ind = 100
xlim = (70, 120)
ylim = (-50, 1500)

raw.plot(poly_ind, event_ind, xlim, ylim)

raw.integrator.cleanup()