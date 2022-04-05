import logging
import json
import math

log = logging.getLogger('expected_signal')
log.debug('begin')


class ErrorTS:
    def __init__(self, signal_file_1: str, signal_file_2: str) -> None:
        log.debug('begin')
        self.error: str = ''

        self.__res: dict = {
            'te_grid': [],
            '64': {
                'signal': [],
                'err': []
            },
            '47': {
                'signal': [],
                'err': []
            }
        }

        with open('in/%s' % signal_file_1, 'r') as file:
            self.ch_count: int = int((len(file.readline().split(',')) - 1) * 0.5)
            for ch in range(self.ch_count):
                self.__res['64']['signal'].append([])
                self.__res['64']['err'].append([])
            file.seek(0)
            for line in file:
                line_split = line.split(',')
                self.__res['te_grid'].append(float(line_split[0]))
                for ch in range(self.ch_count):
                    self.__res['64']['signal'][ch].append(float(line_split[1 + ch]))
                    self.__res['64']['err'][ch].append(float(line_split[1 + self.ch_count + ch]))

        with open('in/%s' % signal_file_2, 'r') as file:
            if self.ch_count != int((len(file.readline().split(',')) - 1) * 0.5):
                print(self.ch_count, int((len(file.readline().split(',')) - 1) * 0.5))
                fuck
            for ch in range(self.ch_count):
                self.__res['47']['signal'].append([])
                self.__res['47']['err'].append([])
            file.seek(0)
            count: int = 0
            for line in file:
                line_split = line.split(',')
                if self.__res['te_grid'][count] != float(line_split[0]):
                    fuck
                count += 1

                for ch in range(self.ch_count):
                    self.__res['47']['signal'][ch].append(float(line_split[1 + ch]))
                    self.__res['47']['err'][ch].append(float(line_split[1 + self.ch_count + ch]))

        self.__calculate()

        log.debug('end')

    def __calculate(self) -> bool:
        log.debug('begin')

        with open('out/expected_error_dual_new.csv', 'w') as file:
            header = 'T_e, err, gamma_err, '
            units = 'eV, %, %, '
            for ch in range(self.ch_count):
                header += 'ch%d, err, ' % (ch + 1)
                units += ' , , '
            file.write(header[:-2] + '\n')
            file.write(units[:-2] + '\n')

            for temp_ind in range(1, len(self.__res['te_grid']) - 1):
                tail = ''
                f_sum = 0
                df_sum = 0
                fdf_sum = 0
                nf_sum = 0
                for ch in range(self.ch_count):
                    f = self.__res['64']['signal'][ch][temp_ind] / self.__res['47']['signal'][ch][temp_ind]

                    der_f = (self.__res['64']['signal'][ch][temp_ind + 1] /
                             self.__res['47']['signal'][ch][temp_ind + 1] -
                             self.__res['64']['signal'][ch][temp_ind - 1] /
                             self.__res['47']['signal'][ch][temp_ind - 1]) / \
                            (self.__res['te_grid'][temp_ind + 1] - self.__res['te_grid'][temp_ind - 1])

                    err = f * math.sqrt(pow(self.__res['64']['err'][ch][temp_ind] / self.__res['64']['signal'][ch][temp_ind], 2) +
                               pow(self.__res['47']['err'][ch][temp_ind] / self.__res['47']['signal'][ch][temp_ind], 2))

                    err2 = err * err

                    f_sum += math.pow(f, 2) / err2
                    df_sum += math.pow(der_f, 2) / err2
                    fdf_sum += f * der_f / err2
                    nf_sum += f * f / err2

                    tail += '%.3f, %.3f, ' % (f, min(err, 1e100))

                file.write('%.3f, %.3f, %.3f, %s\n' % (self.__res['te_grid'][temp_ind],
                                                 math.sqrt(f_sum / (f_sum * df_sum - math.pow(fdf_sum, 2))) *
                                                 100 / self.__res['te_grid'][temp_ind],
                                                 math.sqrt(df_sum / (nf_sum * df_sum - math.pow(fdf_sum, 2))) *
                                                 100 / 1,
                                                 tail[:-2]))

        log.debug('end')
        return True


expected_err_1064 = ErrorTS('phel_1064.csv', 'phel_1047.csv')
print('Code OK')
