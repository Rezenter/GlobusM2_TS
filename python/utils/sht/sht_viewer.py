import shtRipper

SHT_LOCATION = 'Z:/'


class sht:
    def __init__(self, shotn: int):
        self.shotn: int = shotn
        self.data = shtRipper.ripper.read('%ssht%d.SHT' % (SHT_LOCATION, shotn), [
                'nl 42 cm (1.5мм) 64pi',
                'Nl_42_УПЧ',
                'NL_42_No_Filtr'
            ])

    def get_names(self):
        return list(self.data.keys())

    def get_sig(self, key: str) -> dict:
        if key in self.data:
            return self.data[key]
        else:
            return {
                'ok': False,
                'error': 'No signal "%s" in sht' % key
            }
