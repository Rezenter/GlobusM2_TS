import shtRipper
from pathlib import Path

#SHT_LOCATIONS = ['Z:/', 'X:/']
SHT_LOCATIONS = ['\\\\172.16.12.28\\Data\\', '\\\\172.16.12.127\\Data\\']


class sht:
    def __init__(self, shotn: int):
        self.shotn: int = shotn
        for location in SHT_LOCATIONS:
            path = Path('%ssht%d.SHT' % (location, shotn))
            #print('%ssht%d.SHT' % (location, shotn))
            if not path.is_file():
                continue
            self.data = shtRipper.ripper.read('%ssht%d.SHT' % (location, shotn), [
                    'nl 42 cm (1.5мм) 64pi',
                    'Nl_42_УПЧ',
                    'NL_42_No_Filtr',
                    'NL_42_УЛЧ'
                ])
            break
        else:
            print('Requested sht does not exist in DB.')
            self.data = {
                'ok': False,
                'description': 'Requested shotn does not exist in DB.'
            }
    def get_names(self):
        return list(self.data.keys())

    def get_sig(self, key: str) -> dict:
        if key in self.data:
            return self.data[key]
        else:
            #print(key)
            #print(self.data.keys())
            return {
                'ok': False,
                'error': 'No signal "%s" in sht' % key
            }
