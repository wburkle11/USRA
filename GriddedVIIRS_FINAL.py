#THIS IS A SCRIPT VERSION OF THE GriddedVIIRS function: 
import argparse
import glob
import geopandas as gpd
import numpy as np
import xarray as xr
from scipy.spatial.distance import cdist
import pandas as pd 
import datetime 


def nearest(coord, dpoint, shape, mag=10):
    # dpoint: np.array [1, 2]
    # coord: np.array [N, 2]
    dpoint = np.array([dpoint['longitude'], dpoint['latitude']])[None]
    dist = cdist(dpoint, coord, metric="euclidean")
    indices = dist.argsort()[0][:mag]
    lat_indices = np.unravel_index(indices, shape)[0]
    lon_indices = np.unravel_index(indices, shape)[1]
    return lat_indices, lon_indices

def nearest2(x, y, dpoint, mag=10):
    '''
    This function takes coordinate grids and a point data sample
    and returns the index of 'mag'-closest coordinates.
    '''
    lat = dpoint['latitude']
    lon = dpoint['longitude']
    lat_ind = np.argsort(np.abs(y[:, 0] - lat))[:mag]
    lon_ind = np.argsort(np.abs(x[0, :] - lon))[:mag]
    return lat_ind, lon_ind

def gridVIIRS(gdf, day, xlim, ylim, res, out=None):
    '''
    Assigns the data from rows to a uniform grid whose bounds
    and resolution are specified by xlim, ylim, and res.
    Return the gridded data as an xarray dataset. If save is
    True, save result to disk in compressed netCDF format.
    '''
    DD = gdf[gdf['acq_date'] == day]
    print(DD)
    date = DD.iloc[0].loc['acq_date']
    date = pd.to_datetime(date)
    year, month, day = date.year, date.month, date.day
    print('Aquired Date') 
    y, x = np.mgrid[(ylim[1] - res/2):ylim[0]:-res,
                    (xlim[0] + res/2):xlim[1]:res]
    FRP = np.zeros_like(x)
    brightness = np.zeros_like(x)
    bright_t31 = np.zeros_like(x)
    confidence = np.zeros_like(x, dtype=np.int8)
    coord = np.array([x.flatten(), y.flatten()]).T
    print("Completed Initialization") 
    # Assign each row's data values to nearest grid point
    for index, dpoint in DD.iterrows():
        print("Preparing for Nearest Function")
        lati, loni = nearest(coord, dpoint, shape = x.shape, mag = 10)
        print("Nearest Function Complete") 
        FRP[lati, loni] = dpoint['frp']
        brightness[lati, loni] = dpoint['bright_ti4']
        bright_t31[lati, loni] = dpoint['bright_ti5']
        if dpoint['confidence'] == 'l':
            conf = 1
        elif dpoint['confidence'] == 'n':
            conf = 2
        elif dpoint['confidence'] == 'h':
            conf = 3
        else:
            conf = -1    # Indicates unexpected confidence value
        confidence[lati, loni] = conf
    #Naming Convention:
    #VIIRS_SNPP_Fire_375m_Gridded_v1.0_YYYY-MM-DD.nc
         #YYYY = year
         #MM   = month
         #DD   = day of month
        #VIIRS_SNPP_FIRE_375m_Gridded_2018
    fname = f"VIIRS_SNPP_Fire_375m_Gridded_v1.0_{year}_{month:02}_{day:02}.nc"
    print('Loaded Filename')
    dl = xr.Dataset(
                data_vars = dict(
                    FRP = (['lat', 'lon'], FRP),
                    brightness = (['lat', 'lon'], brightness),
                    bright_t31 = (['lat', 'lon'], bright_t31),
                    confidence = (['lat', 'lon'], confidence)
                ),
                coords = dict(
                    lat = y[: ,0],
                    lon = x[0, :]
                ),
                attrs = dict(
                    title = 'VIIRS 375m Gridded Fire Data',
                    description = ('Gridded version of VIIRS 375m fire data. '
                                'Data was downloaded from LANCE FIRMS archive download '
                                'tool in shapefile format then gridded to a 375m grid '
                                'with grid_VIIRS.py.'),
                    version = 'v1.0',
                    institution = 'USRA',
                    technical_contact_email = 'aakbariasanjan@usra.edu',
                    ACQ_DATE = day,
                    dataset_name = fname,
                    wkt = ('GEOGCRS["WGS 84",DATUM["World Geodetic System 1984",'
                        'ELLIPSOID["WGS 84",6378137,298.257223563,'
                        'LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,'
                        'ANGLEUNIT["degree",0.0174532925199433]],'
                        'CS[ellipsoidal,2],AXIS["geodetic latitude (Lat)",north,ORDER[1],'
                        'ANGLEUNIT["degree",0.0174532925199433]],'
                        'AXIS["geodetic longitude (Lon)",east,ORDER[2],'
                        'ANGLEUNIT["degree",0.0174532925199433]],'
                        'USAGE[SCOPE["unknown"],AREA["World"],'
                        'BBOX[20,-135,50,-65]],ID["EPSG",4326]]'
                        )
                )            
            )
    conf_legend = '-1: "unexpected value", 0: "no data", 1: "low", 2: "nominal", 3: "high"'
    dl['confidence'].attrs['legend'] = conf_legend
    
    if out:
        dl.to_netcdf('%s/%s' % (out, fname), engine="netcdf4",
                encoding = {
                    "FRP": {
                        "dtype": "float32",
                        "zlib": True,
                        "complevel": 9
                    },
                    "brightness": {
                        "dtype": "float32",
                        "zlib": True,
                        "complevel": 9
                    },
                    "bright_t31": {
                        "dtype": "float32",
                        "zlib": True,
                        "complevel": 9
                    },
                    "confidence": {
                        "dtype": "int8",
                        "zlib": True,
                        "complevel": 9
                    },
                    "lat": {
                        "dtype": "float64",
                        "zlib": True,
                        "complevel": 9
                    },
                    "lon": {
                        "dtype": "float64",
                        "zlib": True,
                        "complevel": 9
                    }
                })
    return dl
    print('Returned Output VIIRS File') 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Grid VIIRS 375m Active Fire Data.')
    parser.add_argument('-i', dest='input_dir', required=True,
                        help='input directory containing VIIRS shapefiles',
                        metavar='IN_DIR')
    parser.add_argument('-o', dest='output_dir', required=True,
                        help='output directory for gridded files',
                        metavar='OUT_DIR')
    args = parser.parse_args()
    print('\n    Searching for shapefiles in directory %s.' % args.input_dir)
    shapefiles = glob.glob('/ThomasEnvUSRA/USRA/VIIRS/VIIRS_Input/')
    print('    %d shapefiles found.' % len(shapefiles))
    for shp in shapefiles:
        print('\tProcessing file %s.' % shp.split('\\')[-1])
        gdf = gpd.read_file(shp)
        days = list(gdf['acq_date'].value_counts().index)
        days.sort()
        for day in days:
            print('\t    Gridding date %s.' % day)
            gridVIIRS(gdf, day, xlim=[-174.155441, -67.073578], ylim=[19.011648, 70.405228], res=0.00375,
                        out=args.output_dir)
    print('    done.')