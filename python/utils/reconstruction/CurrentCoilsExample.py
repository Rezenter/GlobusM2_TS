import python.utils.reconstruction.CurrentCoils as cfm

shotn: int = 42862
requested_time: float = 180e-3 # s


def process(data):
    error = cfm_data.error
    if error is not None:
        return {
            'error': cfm_data.error
        }

    t_ind = 0
    for t_ind in range(len(cfm_data.timestamps) - 1):
        if cfm_data.timestamps[t_ind] <= requested_time < cfm_data.timestamps[t_ind + 1]:
            if (requested_time - cfm_data.timestamps[t_ind]) >= (
                    cfm_data.timestamps[t_ind + 1] - requested_time):
                t_ind += 1
            break
    if len(cfm_data.data['boundary']['rbdy']['variable'][t_ind]) == 0:
        return {
            'error': 'no boundary'
        }
    for i in range(len(cfm_data.data['boundary']['zbdy']['variable'][t_ind])):
        if cfm_data.data['boundary']['zbdy']['variable'][t_ind][i] * \
                cfm_data.data['boundary']['zbdy']['variable'][t_ind][i - 1] < 0:
            break
    else:
        print('bad plasma: LCFS does not cross equator')
        return {
            'error': 'bad plasma: LCFS does not cross equator'
        }

    cfm_data.data['boundary']['rbdy']['variable'][t_ind], cfm_data.data['boundary']['zbdy']['variable'][
        t_ind] = \
        cfm_data.clockwise(cfm_data.data['boundary']['rbdy']['variable'][t_ind],
                           cfm_data.data['boundary']['zbdy']['variable'][t_ind],
                           t_ind)

    # print('clockwise')

    return {
        'summary': cfm_data.get_surface_parameters(t_ind=t_ind),
        'rbdy': cfm_data.data['boundary']['rbdy']['variable'][t_ind],
        'zbdy': cfm_data.data['boundary']['zbdy']['variable'][t_ind]
    }

cfm_data = cfm.CCM(shotn)
out = process(cfm_data)
print(out)
print('\nOK')

