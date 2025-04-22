import sys
sys.path.append('../python')
from python.utils.reconstruction import CurrentCoils

shotn: int = 41114
times: list[float] = [201, 204, 207, 210, 213, 216, 219, 222, 225]

cfm = CurrentCoils.CCM(shotn=shotn)

data = []

for time in times:
    time *= 1e-3
    t_ind: int = 0
    for t_ind in range(len(cfm.timestamps) - 1):
        if cfm.timestamps[t_ind] <= time < cfm.timestamps[t_ind + 1]:
            if (time - cfm.timestamps[t_ind]) >= (cfm.timestamps[t_ind + 1] - time):
                t_ind += 1
            break
    if len(cfm.data['boundary']['rbdy']['variable'][t_ind]) == 0:
        fuck
    cfm.data['boundary']['rbdy']['variable'][t_ind], cfm.data['boundary']['zbdy']['variable'][t_ind] = \
        cfm.clockwise(cfm.data['boundary']['rbdy']['variable'][t_ind],
                                cfm.data['boundary']['zbdy']['variable'][t_ind],
                                t_ind)

    data.append((cfm.data['boundary']['rbdy']['variable'][t_ind], cfm.data['boundary']['zbdy']['variable'][t_ind]))


for surf_i in range(len(data[-1][0])):
    line = ''
    for time_i in range(len(data)):
        line += '%.2f %.2f ' % (data[time_i][0][surf_i], data[time_i][1][surf_i])
    print(line[:-1])

print('Code OK')
