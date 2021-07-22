import json
import os.path


class DB:
    def __init__(self, plasma_path):
        self.plasma = plasma_path
        print('ok')

    def get_shot(self, shotn):
        folder = '%sresult/%05d/' % (self.plasma, shotn)
        if not os.path.isdir(folder):
            return {
                'ok': False,
                'description': 'No such shot in database: "%05d"' % shotn
            }
        if not os.path.isfile('%s%05d.json' % (folder, shotn)):
            return {
                'ok': False,
                'description': 'No such shot in database (internal error): "%05d"' % shotn
            }
        data = {}
        with open('%s%05d.json' % (folder, shotn), 'r') as file:
            data = json.load(file)
        return {
            'ok': True,
            'data': data
        }
