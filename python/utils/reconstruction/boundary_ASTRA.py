import python.utils.reconstruction.CurrentCoils as ccm

shotn: int = 42611
requested_time: float = 190.4  # ms

ccm_data = ccm.CCM(shotn)

t_ind = 0
for t_ind in range(len(ccm_data.timestamps) - 1):
    if ccm_data.timestamps[t_ind] <= requested_time < ccm_data.timestamps[t_ind + 1]:
        if (requested_time - ccm_data.timestamps[t_ind]) >= (ccm_data.timestamps[t_ind + 1] - requested_time):
            t_ind += 1
        break
ccm_data.data['boundary']['rbdy']['variable'][t_ind], ccm_data.data['boundary']['zbdy']['variable'][t_ind] = \
    ccm_data.clockwise(ccm_data.data['boundary']['rbdy']['variable'][t_ind],
                            ccm_data.data['boundary']['zbdy']['variable'][t_ind],
                            t_ind)

out: str = ''
count = 0
for i in range(0, len(ccm_data.data['boundary']['rbdy']['variable'][t_ind]), 2):
    out += '%.3f        %.3f\n' % (ccm_data.data['boundary']['rbdy']['variable'][t_ind][i] * 0.01, ccm_data.data['boundary']['zbdy']['variable'][t_ind][i] * 0.01)
    count += 1

print('NAMEXP BND	NTIMES	1	POINTS %d' % count)
print('0.0')
print(out)