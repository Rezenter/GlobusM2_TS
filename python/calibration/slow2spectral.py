from pathlib import Path
import json

#change this line only
cal_name: str = '2023.10.06'

cal_dir: Path = Path('d:/data/db/calibration/spectral/%s/' % cal_name)
if not cal_dir.is_dir():
    fuck

config = None
with open('', 'r') as file:
    config = json.load(file)