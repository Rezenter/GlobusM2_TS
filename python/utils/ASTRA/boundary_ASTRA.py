import python.utils.reconstruction.CurrentCoils as ccm

shotn: int = 41114
requested_time: float = 213.0  # ms
requested_time *= 1e-3

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
r_prev = 0
for i in range(0, len(ccm_data.data['boundary']['rbdy']['variable'][t_ind]), 2):
    if r_prev - 0.12 <= ccm_data.data['boundary']['rbdy']['variable'][t_ind][i] <= r_prev + 0.12:
        continue
    r_prev = ccm_data.data['boundary']['rbdy']['variable'][t_ind][i]
    out += '%.4f       %.4f\n' % (ccm_data.data['boundary']['rbdy']['variable'][t_ind][i] * 0.01, ccm_data.data['boundary']['zbdy']['variable'][t_ind][i] * 0.01)
    count += 1

print('NAMEXP BND	NTIMES	1	POINTS %d' % count)
print('0.0')
print(out)