import raw

poly_ind = 9
#event_ind = 58
xlim = (70, 120)
ylim = (-50, 1500)

indexes = [39, 45, 50, 58]

for event_ind in indexes:
    raw.plot(poly_ind, event_ind, xlim, ylim)
    raw.csv(poly_ind, event_ind)

raw.integrator.cleanup()