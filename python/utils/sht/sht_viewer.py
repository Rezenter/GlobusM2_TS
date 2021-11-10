import shtRipper

SHT_LOCATION = 'Z:/'


class sht:
    def __init__(self, shotn: int):
        self.shotn: int = shotn
        self.data = shtRipper.ripper.read('%ssht%d.SHT' % (SHT_LOCATION, shotn))

    def get_names(self) -> list[str]:
        return list(self.data.keys())

    def get_sig(self, key: str) -> dict:
        if key in self.data:
            return self.data[key]
        else:
            return {
                'ok': False,
                'error': 'No signal "%s" in sht' % key
            }
