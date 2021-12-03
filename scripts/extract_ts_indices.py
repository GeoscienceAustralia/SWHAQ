import numpy as np
import os
import xarray as xr
from calendar import monthrange
from mpi4py import MPI
import time

references = 'Copernicus Climate Change Service (C3S) (2017): ERA5: Fifth generation of ECMWF atmospheric reanalyses of the global climate'

licence = """
I. Licence to Use Copernicus Products

1. Definitions

1.1. ‘Licensor’ means the European Union, represented by the European Centre for Medium-Range Weather Forecasts (ECMWF).

1.2. ‘Licensee’ means all natural or legal persons who agree to the terms of this Licence.

1.3. ‘Licence’ means this license agreement between the Licensor and the Licensee as amended from time to time.

1.4. ‘Copernicus Services’ means:

1.4.1. the Copernicus Atmosphere Monitoring Service (CAMS), which is to provide information on air quality on a local, national, and European scale, and the chemical composition of the atmosphere on a global scale.

1.4.2. the Copernicus Climate Change Service (C3S), which is to provide information to increase the knowledge base to support policies on adaptation to and mitigation of climate change

1.5. ‘Copernicus Products’ means all products listed in the C3S or CAMS Service Product Specification or any other items available through an ECMWF Copernicus portal, except those items which are labelled/flagged as being subject to their own separate terms of use.

1.6. ‘Intellectual Property Rights’ refers to intellectual property rights of all kinds,

1.6.1. including: all patents; rights to inventions; copyright and related rights; moral rights; trademarks and service marks; trade names and domain names; rights in get-up; rights to goodwill or to sue for passing off or unfair competition; rights in designs; rights in computer software; database rights; rights in confidential information (including know-how and trade secrets); any other rights in the nature of intellectual property rights;

1.6.2. in each case whether registered or unregistered and including all applications (or rights to apply) for, and renewals or extensions of, such rights and all similar or equivalent rights or forms of protection which subsist or will subsist now or in the future in any part of the world together with all rights of action in relation to the infringement of any of the above.

1.7. ‘Copernicus Contractor’ refers to providers of Copernicus related goods and services to ECMWF, including information and data, to the Licensor and/or to the users.

1.8. ‘Copernicus Regulations’ refers to Regulation (EU) No 377/2014 of the European Parliament and of the Council of 3 April 2014 establishing the Copernicus Programme.

1.9. ‘ECMWF Agreement’ refers to the agreement between the European Commission and ECMWF dated 11 November 2014 on the implementation of CAMS and C3S.

2. Introduction

Copernicus is funded under the Copernicus Regulation and operated by ECMWF under the ECMWF Agreement. Access to all Copernicus (previously known as GMES or Global Monitoring for Environment and Security) Information and Data is regulated under Regulation (EU) No 1159/2013 of the European Parliament and of the Council of 12 July 2013 on the European Earth monitoring programme, under the ECMWF Agreement and under the European Commission’s Terms and Conditions. Access to all Copernicus information is regulated under Regulation (EU) No 1159/2013 and under the ECMWF Agreement.

3. Terms of the Licence

This Licence sets out the terms for use of Copernicus Products. By agreeing to these terms, the Licensee agrees to abide by all of the terms and conditions in this Licence for the use of Copernicus Products.

4. Licence Permission

4.1. This Licence is free of charge, worldwide, non-exclusive, royalty free and perpetual.

4.2. Access to Copernicus Products is given for any purpose in so far as it is lawful, whereas use may include, but is not limited to: reproduction; distribution; communication to the public; adaptation, modification and combination with other data and information; or any combination of the foregoing.

5. Attribution

5.1. All users of Copernicus Products must provide clear and visible attribution to the Copernicus programme. The Licensee will communicate to the public the source of the Copernicus Products by crediting the Copernicus Climate Change and Atmosphere Monitoring Services:

5.1.1. Where the Licensee communicates or distributes Copernicus Products to the public, the Licensee shall inform the recipients of the source by using the following or any similar notice:
• 'Generated using Copernicus Climate Change Service information [Year]' and/or
• 'Generated using Copernicus Atmosphere Monitoring Service information [Year]'.

5.1.2. Where the Licensee makes or contributes to a publication or distribution containing adapted or modified Copernicus Products, the Licensee shall provide the following or any similar notice:
• 'Contains modified Copernicus Climate Change Service information [Year]'; and/or
• 'Contains modified Copernicus Atmosphere Monitoring Service information [Year]'

5.1.3. Any such publication or distribution covered by clauses 5.1.1 and 5.1.2 shall state that neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.

6. Intellectual Property Rights

6.1. All Intellectual Property Rights in the Copernicus Products belong, and will continue to belong, to the European Union.

6.2. All Intellectual Property Rights of new items created as a result of modifying or adapting the Copernicus Products through the applications and workflows accessible on the ECMWF Copernicus portals (e.g. through the CDS Toolbox) will belong to the European Union.

6.3. All other new Intellectual Property Rights created as a result of modifying or adapting the Copernicus information will be owned by the creator.

7. Provision of Third Party Information and Data

This Licence only covers Copernicus Products. Access to third party products, information, and data related to Copernicus information to which the Licensee is directed or which can be directly accessed through any Copernicus portal will be subject to different licence terms.

8. Disclaimers

8.1. Neither the Licensor nor ECMWF warrant that Copernicus Products will be free from errors or omissions or that such errors or omissions can or will be rectified, or that the Licensee will have uninterrupted, continuous, or timely access to Copernicus Products.

8.2. The Licensor, as well as ECMWF, exclude all warranties, conditions, terms, undertakings, obligations whether express or implied by statute including but not limited to the implied warranties of satisfactory quality and fitness for a particular purpose or otherwise to the fullest extent permitted by law.

9. Liabilities

Neither the Licensor nor ECMWF will accept liability for any damage, loss whether direct, indirect or consequential resulting from the Licensee’s use of the Copernicus Products.

10. Termination of and Changes to this Licence

The Licensor may terminate this licence if the Licensee breaches its obligations under these terms. The Licensor may revise this Licence at any time and will notify the Licensee of any revisions.

11. Arbitration Clause and Governing Law

In the event of a dispute arising in connection with this License, the parties shall attempt to settle their differences in an amicable manner. If any dispute cannot be so settled, it shall be settled under the Rules of Arbitration of the International Chamber of Commerce by one arbitrator appointed in accordance with the said rules sitting in London, United Kingdom. The proceedings shall be in the English language. The right of appeal by either party to regular Courts on a question of law arising in the course of any arbitral proceedings or out of an award made in any arbitral proceedings is hereby agreed to be excluded.

It is the intention of the parties that this License shall comprehensively govern the legal relations between the parties to the Licence, without interference or contradiction by any unspecified law. However, where a matter is not specifically covered by these terms or a provision of the Licence terms is ambiguous or unclear, resolution shall be found by reference to the laws of England and Wales, including any relevant law of the European Union.

Nothing stated in this License shall be construed as a waiver of any privileges or immunities of the Licensor or of ECMWF.

Version 1.2 (November 2019)
"""

def dask_index(arr, indexes):
    # assumes doing the second axis
    sz1 = arr.data.shape[1] * arr.data.shape[2] * arr.data.shape[3]
    sz2 = indexes.shape[1] * indexes.shape[2]
    idxs = indexes.data.flatten() * sz2 + sz1 * (np.arange(indexes.size) // sz2) + np.arange(indexes.size) % sz2
    # sort indices for speed
    y = idxs.argsort()
    i = np.empty_like(y)
    i[y] = np.arange(y.size)
    # return arr.data.flatten()[idxs[y]].compute(scheduler='single-threaded')[i].reshape(indexes.shape)
    return arr.data.flatten()[idxs[y]][i].reshape(indexes.shape)


def dask_interpolate(u, v, z, height):
    top = height * 9.80665
    idxs = (abs(top - z) + 1_000_000_000 * (z > top)).argmin(axis=1)#.compute(scheduler='single-threaded')
    z1 = dask_index(z, idxs)
    u1 = dask_index(u, idxs)
    v1 = dask_index(v, idxs)
    z2 = dask_index(z, idxs - 1)
    u2 = dask_index(u, idxs - 1)
    v2 = dask_index(v, idxs - 1)
    u_interp = (u2 * (top - z1) + u1 * (z2 - top)) / (z2 - z1)
    v_interp = (v2 * (top - z1) + v1 * (z2 - top)) / (z2 - z1)
    return u_interp, v_interp


comm = MPI.COMM_WORLD

pl_prefix = "/g/data/rt52/era5/pressure-levels/reanalysis"
sl_prefix = "/g/data/rt52/era5/single-levels/reanalysis"
outpath = "/g/data/w85/QFES_SWHA/hazard/input/tsindices/"

years = np.arange(1980, 2022)
rank = comm.Get_rank()
long_slice = slice(151, 154)
lat_slice = slice(-25, -29)
rank_years = years[(years % comm.size) == rank]

t0 = time.time()

for year in rank_years:
    for month in range(1, 13):
        days = monthrange(year, month)[1]

        if os.path.isfile(outpath + f"ts_indices_{year}{month:02d}01-{year}{month:02d}{days}.nc"):
            print(f"Skipping {month}/{year}")
            continue

        print(f"Loading data {month}/{year}")

        ufile = f"{pl_prefix}/u/{year}/u_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        vfile = f"{pl_prefix}/v/{year}/v_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        capefile = f"{sl_prefix}/cape/{year}/cape_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        u10file = f"{sl_prefix}/10u/{year}/10u_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        v10file = f"{sl_prefix}/10v/{year}/10v_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        totalxfile = f"{sl_prefix}/totalx/{year}/totalx_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        zfile = f"{pl_prefix}/z/{year}/z_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        print(f"Processing data {month}/{year}")
        if not os.path.isfile(ufile):
            continue

        u = xr.open_dataset(ufile, chunks='auto').u.sel(longitude=long_slice, latitude=lat_slice).compute(scheduler='single-threaded')
        v = xr.open_dataset(vfile, chunks='auto').v.sel(longitude=long_slice, latitude=lat_slice).compute(scheduler='single-threaded')
        cape = xr.open_dataset(capefile, chunks='auto').cape.sel(longitude=long_slice, latitude=lat_slice).compute(scheduler='single-threaded')
        u10 = xr.open_dataset(u10file, chunks='auto').u10.sel(longitude=long_slice, latitude=lat_slice).compute(scheduler='single-threaded')
        v10 = xr.open_dataset(v10file, chunks='auto').v10.sel(longitude=long_slice, latitude=lat_slice).compute(scheduler='single-threaded')
        totalx = xr.open_dataset(totalxfile, chunks='auto').totalx.sel(longitude=long_slice, latitude=lat_slice).compute(scheduler='single-threaded')
        z = xr.open_dataset(zfile, chunks='auto').z.sel(longitude=long_slice, latitude=lat_slice).compute(scheduler='single-threaded')

        uu = u.sel(level=500) - u10
        vv = v.sel(level=500) - v10
        mason = np.sqrt(uu ** 2 + vv ** 2) * cape ** 1.67
        mason = mason.data.reshape((-1, 24) + mason.data.shape[1:]).max(axis=1)

        totalx = totalx.data.reshape((-1, 24) + totalx.data.shape[1:]).max(axis=1)

        utop, vtop = dask_interpolate(u, v, z, height=6_000)
        uu = utop - u10
        vv = vtop - v10
        shear = np.sqrt(uu ** 2 + vv ** 2)
        allen = shear * cape ** 1.67
        allen = allen.data.reshape((-1, 24) + allen.data.shape[1:]).max(axis=1)

        umean = None # pressure weighted mean
        lr13 = None # temperature lapse rate from 1-3km
        rhmin13 = None # rel hum min 1-3km
        srhe = None # effective-layer storm relative helicity
        qmelt = None # water vapor mixing ratio at the height of the melting level
        efflcl = None # effective-layer parcel lifting condensation level

        # dowdy = 6.1e-02 * shear + 1.5e-1 * umean + 9.4e-1 * lr13 + 3.9e-2 * rhmin13
        # dowdy += 1.7e-02 * srhe + 3.8e-1 * qmelt + 4.7e-4 * efflcl -1.3e1

        time_days = u.coords['time'].data.reshape((-1, 24))[:, 0]

        data_vars = {
            'mason': (('time', 'latitude', 'longitude'), mason),
            'allen': (('time', 'latitude', 'longitude'), allen),
            'totalx': (('time', 'latitude', 'longitude'), totalx),
        }

        coords = {
            'time': time_days,
            'latitude': u.coords['latitude'].data,
            'longitude': u.coords['longitude'].data,
        }

        ds = xr.Dataset(data_vars, coords)
        ds.attrs = {
            'title': 'Thunderstorm Indices',
            'references': references,
            'license': licence,
        }

        ds['mason'].attrs = {
            'long_name': 'Mason (2021) Thunderstorm Index',
            'units': 'm/s',
            'cell_methods': 'time: daily maximum'
        }

        ds['allen'].attrs = {
            'long_name': 'Allen et. al. (2011) Thunderstorm Index',
            'units': 'm/s',
            'cell_methods': 'time: daily maximum'
        }

        ds['totalx'].attrs = {
            'long_name': 'Total totals Index',
            'units': 'm/s',
            'cell_methods': 'time: daily maximum'
        }

        ds.to_netcdf(outpath + f"ts_indices_{year}{month:02d}01-{year}{month:02d}{days}.nc")
        print(f"Finished {month}/{year}")


print("Time taken:", time.time() - t0, "s")
