import os
import sys
import logging
import time
from calendar import monthrange
import xarray as xr
import metpy
from metpy.units import units
import numpy as np
import time
from mpi4py import MPI

comm = MPI.COMM_WORLD

logging.basicConfig(filename='extract_dowdy_ts_index.log', level=logging.DEBUG)

pl_prefix = "/g/data/rt52/era5/pressure-levels/reanalysis"
sl_prefix = "/g/data/rt52/era5/single-levels/reanalysis"
outpath = "/g/data/w85/QFES_SWHA/hazard/input/tsindices/"

def main():
    """
    Handle command line arguments and call processing functions

    """

    if comm.rank == 0:
        master_process()
    else:
        slave_process()


def master_process():
    for year in range(1980, 2021):
        for month in range(1, 13):
            process(year, month)
            break
        break


def slave_process():
    data = comm.recv(source=0)
    coords, u_profiles, v_profiles, height_profiles, temp_profiles, rh_profiles = data
    outarray = np.zeros((u_profiles.shape[0], u_profiles.shape[2], u_profiles.shape[3]))
    prssure_profile = coords['pressure'].data

    for i in range(u_profiles.shape[0]):
        for j in range(u_profiles.shape[2]):
            for k in range(u_profiles.shape[3]):
                u_profile = u_profiles[i, :, j, k]
                v_profile = v_profiles[i, :, j, k]
                height_profile = height_profiles[i, :, j, k]
                temp_profile = temp_profiles[i, :, j, k]
                rh_profile = rh_profiles[i, :, j, k]

                outarray[i, j, k] = calc_dowdy(
                    u_profile, v_profile, prssure_profile,
                    temp_profile, height_profile, rh_profile

                )

    return outarray


def process(year: int, month: int):
    t0 = time.time()

    print(f"Started processing {month}/{year}")
    logging.info(f"Started processing {month}/{year}")

    long_slice = slice(148, 154)
    lat_slice = slice(-24, -33)

    days = monthrange(year, month)[1]
    ufile = f"{pl_prefix}/u/{year}/u_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
    vfile = f"{pl_prefix}/v/{year}/v_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
    zfile = f"{pl_prefix}/z/{year}/z_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
    tfile = f"{pl_prefix}/t/{year}/t_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
    rhfile = f"{pl_prefix}/r/{year}/r_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"

    u = xr.open_dataset(ufile).u.sel(longitude=long_slice, latitude=lat_slice)
    v = xr.open_dataset(vfile).v.sel(longitude=long_slice, latitude=lat_slice)
    z = xr.open_dataset(zfile).z.sel(longitude=long_slice, latitude=lat_slice)
    temp = xr.open_dataset(tfile).t.sel(longitude=long_slice, latitude=lat_slice)
    rh = xr.open_dataset(rhfile).r.sel(longitude=long_slice, latitude=lat_slice)

    nt = len(u.coords['time'])
    num_cores = comm.size - 1
    idxs = -1 * np.ones(num_cores + 1)
    idxs[:-1] = np.arange(0, nt, (nt // num_cores) + 1)
    status = MPI.Status()

    outarray = np.zeros((u.data.shape[0], u.data.shape[2], u.data.shape[3]))

    for rank in range(1, comm.size):
        start_idx = idxs[rank - 1]
        stop_idx = idxs[rank]
        u_profiles = u.data[start_idx:stop_idx, ...]
        v_profiles = v.data[start_idx:stop_idx, ...]
        height_profiles = z.data[start_idx:stop_idx, ...] / 9.80665
        temp_profiles = temp.data[start_idx:stop_idx, ...]
        rh_profiles = rh.data[start_idx:stop_idx, ...]

        data = (u.coords, u_profiles, v_profiles, height_profiles, temp_profiles, rh_profiles)
        comm.send(data, dest=rank)

    terminated = 0
    while terminated < comm.size - 1:
        result = comm.recv(source=MPI.ANY_SOURCE, status=status)
        rank = status.source
        start_idx = idxs[rank - 1]
        stop_idx = idxs[rank]
        outarray[start_idx:stop_idx, ...] = result

        terminated += 1

    print(f"Finished processing {month}/{year}. Took {np.round(time.time() - t0)}s")
    logging.info(f"Finished processing {month}/{year}. Took {np.round(time.time() - t0)}s")
    time_days = u.coords['time'].data.reshape((-1, 24))[:, 0]

    outarray = outarray.reshape((-1, 24, outarray.shape[1], outarray.shape[2])).max(axis=1)
    data_vars = {
        'dowdy': (('time', 'latitude', 'longitude'), outarray),
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

    ds['dowdy'].attrs = {
        'long_name': 'Dowdy et. al. (2021) Thunderstorm Index',
        'units': 'm/s',
        'cell_methods': 'time: daily maximum'
    }

    ds.to_netcdf(outpath + f"dowdy_ts_index_{year}{month:02d}01-{year}{month:02d}{days}.nc")


def calc_lr13(height_profile, temp_profile):
    idx = np.where(height_profile <= 1_000)[0][0]
    temp_1 = temp_profile[idx] * (1_000 - height_profile[idx])
    temp_1 += temp_profile[idx - 1] * (height_profile[idx - 1] - 1_000)
    temp_1 /= height_profile[idx - 1] - height_profile[idx]

    idx = np.where(height_profile <= 3_000)[0][0]
    temp_3 = temp_profile[idx] * (3_000 - height_profile[idx])
    temp_3 += temp_profile[idx - 1] * (height_profile[idx - 1] - 3_000)
    temp_3 /= height_profile[idx - 1] - height_profile[idx]

    return (temp_3 - temp_1) / 3


def calc_rhmin13(height_profile, rh_profile):
    mask = (1_000 <= height_profile) & (height_profile <= 3_000)
    return rh_profile[mask].min()


def calc_melting_point_mixing_ratio(relative_humidity, pressure, temperature, dewpoint):
    wetbulb = metpy.calc.wet_bulb_temperature(pressure, temperature, dewpoint)
    idx = np.where(wetbulb <= 0)[0][-1]
    mixing_ratio_1 = metpy.calc.mixing_ratio_from_relative_humidity(
        pressure[idx], temperature[idx], relative_humidity[idx]
    )

    mixing_ratio_2 = metpy.calc.mixing_ratio_from_relative_humidity(
        pressure[idx + 1], temperature[idx + 1], relative_humidity[idx + 1]
    )

    mixing_ratio = mixing_ratio_1 * (wetbulb[idx + 1] - 0) + mixing_ratio_2 * (0 - wetbulb[idx])
    mixing_ratio /= wetbulb[idx + 1] - wetbulb[idx]
    return mixing_ratio


def calc_dewpoint(pressure, temperature, relative_humidity):
    mixing_ratio = metpy.calc.mixing_ratio_from_relative_humidity(
        pressure, temperature, relative_humidity
    )
    vapor_pressure = metpy.calc.vapor_pressure(pressure, mixing_ratio)
    dewpoint = metpy.calc.dewpoint(vapor_pressure)
    return dewpoint


def calc_effective_layer(pressure, temperature, dewpoint):

    bottom_idx = None
    top_idx = 0

    # start at ground level and increment pressure levels
    for parcel_idx in range(len(pressure) - 1, -1, -1):
        p, t, td, mu_profile = metpy.calc.parcel_profile_with_lcl(
            pressure[parcel_idx:], temperature[parcel_idx:], dewpoint[parcel_idx:]
        )

        cape, cin = metpy.calc.cape_cin(p, t, td, mu_profile)

        if (cape > 100) and (cin > -250):
            # if this is the first pressure level (from ground) to satisfy the constraints
            # this is the bottom of the inflow layer
            if bottom_idx is None:
                bottom_idx = parcel_idx
        else:
            # if this is the first pressure level (from base of inflow level) that violates
            # the constraints this is the end of the inflow layer
            if bottom_idx is not None:
                top_idx = parcel_idx
                break

    return bottom_idx, top_idx


def calc_windpeed_mean(u, v, pressure):
    mask = (600 <= pressure) & (pressure <= 800)
    umean = metpy.calc.mean_pressure_weighted(
        pressure[mask], u[mask]
    )
    vmean = metpy.calc.mean_pressure_weighted(
        pressure[mask], v[mask]
    )
    windspeed_mean = metpy.calc.wind_speed(umean, vmean)
    return windspeed_mean


def calc_dowdy(u, v, pressure, temperature, height, relative_humidity):
    windspeed_mean = calc_windpeed_mean(u, v, pressure)
    lr13 = calc_lr13(height, temperature)
    rhmin13 = calc_rhmin13(height, relative_humidity)

    # find effective layer
    dewpoint = calc_dewpoint(pressure, temperature, relative_humidity)
    qmelt = calc_melting_point_mixing_ratio(relative_humidity, pressure, temperature, dewpoint)

    bottom_idx, top_idx = calc_effective_layer(pressure, temperature, dewpoint)

    if bottom_idx is None:
        srhe, shear, mixed_parcel, efflcl = 0, 0, 0, 0
    else:
        srhe = metpy.calc.storm_relative_helicity(
            height[top_idx:bottom_idx], u[top_idx:bottom_idx], v[top_idx:bottom_idx]
        )

        shear = metpy.calc.wind_speed(
            *metpy.calc.bulk_shear(
                pressure[top_idx:bottom_idx], u[top_idx:bottom_idx], v[top_idx:bottom_idx]
            )
        )

        mixed_parcel = metpy.cacl.mixed_parcel(
            pressure[top_idx:bottom_idx], temperature[top_idx:bottom_idx], dewpoint[top_idx:bottom_idx]
        )
        efflcl = metpy.calc.lcl(*mixed_parcel)

    dowdy = 6.1e-02 * shear + 1.5e-1 * windspeed_mean + 9.4e-1 * lr13 + 3.9e-2 * rhmin13
    dowdy += 1.7e-02 * srhe + 3.8e-1 * qmelt + 4.7e-4 * efflcl - 1.3e1
    dowdy = 1 / (1 + dowdy.exp())

    return dowdy


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


if __name__ == "__main__":
    main()