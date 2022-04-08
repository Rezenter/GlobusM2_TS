import math
import numpy


class ErrorTS:
    def __init__(self, signal_file_1: str, signal_file_2: str) -> None:
        print('begin')
        self.error: str = ''

        self.ne = 1

        self.__res: dict = {
            'te_grid': [],
            '64': {
                'signal': [],
                'err': []
            },
            '47': {
                'signal': [],
                'err': []
            },
            'Te_err': [1e100],
            'gamma_err': [1e100]
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
                #fuck
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

        print('end')

    def __stage1(self):
        with open('out/expected_error_stage1.csv', 'w') as file:
            header = 'T_e, err, gamma_err, '
            units = 'eV, %, %, '

            file.write(header[:-2] + '\n')
            file.write(units[:-2] + '\n')

            for temp_ind in range(1, len(self.__res['te_grid']) - 1):
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

                    err = f * math.sqrt(
                        pow(self.__res['64']['err'][ch][temp_ind] / self.__res['64']['signal'][ch][temp_ind], 2) +
                        pow(self.__res['47']['err'][ch][temp_ind] / self.__res['47']['signal'][ch][temp_ind], 2))

                    err2 = err * err

                    f_sum += math.pow(f, 2) / err2
                    df_sum += math.pow(der_f, 2) / err2
                    fdf_sum += f * der_f / err2
                    nf_sum += f * f / err2


                self.__res['Te_err'].append(
                    math.sqrt(f_sum / (f_sum * df_sum - math.pow(fdf_sum, 2))))
                self.__res['gamma_err'].append(math.sqrt(df_sum / (nf_sum * df_sum - math.pow(fdf_sum, 2))))

                file.write('%.3f, %.3f, %.3f\n' % (self.__res['te_grid'][temp_ind],
                                                             self.__res['Te_err'][-1] * 100 / self.__res['te_grid'][
                                                                 temp_ind],
                                                             self.__res['gamma_err'][-1] * 100
                                                             ))

    def __a(self, ch_ind: int, las_ind: str, te_ind: int) -> float:
        A = 1
        E = 1
        ne = self.ne
        return A * \
               E * \
               ne * \
               self.__res[las_ind]['signal'][ch_ind][te_ind]

    def __b(self, ch_ind: int, las_ind: str, te_ind: int) -> float:
        A = 1
        E = 1
        C = 1 # C_i is considered 1!
        return A * \
               E * \
               C * \
               self.__res[las_ind]['signal'][ch_ind][te_ind]

    def __weight(self, ch_ind: int, te_ind: int, las_ind: str) -> float:
        der_f = (self.__res['64']['signal'][ch_ind][te_ind + 1] /
                 self.__res['47']['signal'][ch_ind][te_ind + 1] -
                 self.__res['64']['signal'][ch_ind][te_ind - 1] /
                 self.__res['47']['signal'][ch_ind][te_ind - 1]) / \
                (self.__res['te_grid'][te_ind + 1] - self.__res['te_grid'][te_ind - 1])
        s1 = math.pow(self.__res[las_ind]['err'][ch_ind][te_ind], 2)
        s2 = 0#math.pow(1 * 1 * der_f * self.__res['Te_err'][te_ind], 2)
        s3 = 0#math.pow(1 * self.__res['64']['signal'][ch_ind][te_ind] / self.__res['47']['signal'][ch_ind][te_ind] * self.__res['gamma_err'][te_ind], 2)
        #print(s1, s2, s3)
        if s2 < 100:
            #print(te_ind, self.__res['te_grid'][te_ind], der_f, self.__res['Te_err'][te_ind])
            pass
        return s1 + s2 + s3

    def __cross_der(self, ch_ind: int, te_ind: int) -> float:
        # C_i is considered 1!
        res: float = 0
        lasers = ['64', '47']
        for las in lasers:
            res += self.__a(ch_ind=ch_ind, las_ind=las, te_ind=te_ind) * \
                   self.__b(ch_ind=ch_ind, las_ind=las, te_ind=te_ind) / \
                   self.__weight(ch_ind=ch_ind, las_ind=las, te_ind=te_ind)
        return 2 * res

    def __ne2_der(self, te_ind: int) -> float:
        # C_i is considered 1!
        res: float = 0
        lasers = ['64', '47']
        for ch_ind in range(self.ch_count):
            for las in lasers:
                res += math.pow(self.__b(ch_ind=ch_ind, las_ind=las, te_ind=te_ind), 2) /\
                   self.__weight(ch_ind=ch_ind, las_ind=las, te_ind=te_ind)
        return 2 * res

    def __c2_der(self, ch_ind: int, te_ind: int) -> float:
        res: float = 0
        lasers = ['64', '47']
        for las in lasers:
            res += math.pow(self.__a(ch_ind=ch_ind, las_ind=las, te_ind=te_ind), 2) /\
                   self.__weight(ch_ind=ch_ind, las_ind=las, te_ind=te_ind)
        return 2 * res

    def __der_matrix(self, te_ind: int) -> numpy.ndarray:
        # row = first index
        # col = second index
        res: numpy.ndarray = numpy.zeros(
            [
                1 + self.ch_count,
                1 + self.ch_count
            ], dtype=numpy.double)

        res[0, 0] = self.__ne2_der(te_ind=te_ind)
        for ch_ind in range(self.ch_count):
            # top + left
            res[1 + ch_ind, 0] = self.__cross_der(ch_ind=ch_ind, te_ind=te_ind)
            res[0, 1 + ch_ind] = res[1 + ch_ind, 0]

            # rest of the main diagonal
            res[1 + ch_ind, 1 + ch_ind] = self.__c2_der(ch_ind=ch_ind, te_ind=te_ind)
        return res

    def __stage2(self):
        with open('out/expected_error_stage2.csv', 'w') as file:
            header = 'T_e, ne_err, '
            units = 'eV, %, '
            for ch in range(self.ch_count):
                header += 'C_%d_err, ' % (ch + 1)
                units += ', '
            file.write(header[:-2] + '\n')
            file.write(units[:-2] + '\n')

            for temp_ind in range(1, len(self.__res['te_grid']) - 1):
                te_entry: dict = {}
                dm = self.__der_matrix(te_ind=temp_ind)

                try:
                    #rev_m = numpy.linalg.inv(dm)
                    rev_m = numpy.linalg.pinv(dm)
                except numpy.linalg.LinAlgError:
                    print('skipped: %d' % temp_ind)
                    #te_entry['ne_err']: float = 1e100
                    #te_entry['c_err']: list[float] = [
                    #    1e100
                    #    for ch_ind in range(self.ch_count)
                    #]
                    fuck
                    continue

                te_entry['ne_err']: float = \
                    numpy.sqrt(2 * rev_m[0][0], dtype=float) * 100 / self.ne
                if numpy.isnan(te_entry['ne_err']):
                    te_entry['ne_err'] = 1e100
                if numpy.isinf(te_entry['ne_err']):
                    te_entry['ne_err'] = 2e100

                te_entry['c_err']: list[float] = [
                    math.sqrt(2 * rev_m[1 + ch_ind, 1 + ch_ind]) * 100
                    for ch_ind in range(self.ch_count)
                ]

                te_entry['c_err']: list[float] = [
                    numpy.sqrt(2 * rev_m[1 + ch_ind][1 + ch_ind], dtype=float) * 100
                    for ch_ind in range(self.ch_count)
                ]

                tail = ''
                for ch_ind in range(self.ch_count):

                    if numpy.isnan(te_entry['c_err'][ch_ind]):
                        te_entry['c_err'][ch_ind] = 1e100
                    if numpy.isinf(te_entry['c_err'][ch_ind]):
                        te_entry['c_err'][ch_ind] = 2e100

                    tail += '%.3e, ' % te_entry['c_err'][ch_ind]
                #te_entry['der_matrix']: list[float] = dm.astype(float).tolist()
                te_entry['der_matrix']: list[float] = dm

                for row in te_entry['der_matrix']:
                    for col_ind in range(len(row)):
                        if numpy.isnan(row[col_ind]):
                            row[col_ind] = 1e100
                        if numpy.isinf(row[col_ind]):
                            row[col_ind] = 2e100

                file.write('%.3e, %.3e, %s\n' % (self.__res['te_grid'][temp_ind],
                                                             te_entry['ne_err'],
                                                             tail[:-2]))

    def __calculate(self) -> bool:
        print('begin')

        self.__stage1()
        self.__stage2()

        print('end')
        return True


expected_err = ErrorTS('phel_1064.csv', 'phel_1047.csv')
print('Code OK')
