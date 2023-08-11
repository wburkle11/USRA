
from goes2go import GOES
from goes2go.data import goes_timerange
from datetime import datetime
import pandas as pd

## Specify start/end time as a panda-parsable string
start = "2018-01-01 00:00"
end = "2019-01-01 00:00"
print('Locked In Time-Range')

G = goes_timerange(start, end, satellite= "goes16", product="ABI-L2-MCMIP", return_as="filelist", save_dir='/ThomasEnvUSRA/USRA/GOES/GOES_Output/')
print('Pulled Dataset')