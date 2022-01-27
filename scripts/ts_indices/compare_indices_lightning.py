import rasterio
from rasterio.plot import show
import os
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt

DATA_DIR = "/g/data/w85/QFES_SWHA/hazard/input/tsindices"
OUT_PATH = os.path.expanduser("/g/data/w85/QFES_SWHA/hazard/output/plots")

# load in and plot indices

dsidx = xr.load_dataset(os.path.join(DATA_DIR, "ts_index_climatology.nc"))

extent = [dsidx.longitude.data.min(), dsidx.longitude.data.max(),
          dsidx.latitude.data.min(), dsidx.latitude.data.max()]

plt.figure(figsize=(10, 10))
plt.title('Allen')
plt.imshow(dsidx.allen.data, extent=extent)
plt.savefig(os.path.join(OUT_PATH, 'allen-clim-SEQLD.png'))

plt.figure(figsize=(10, 10))
plt.title('Mason')
plt.imshow(dsidx.mason.data, extent=extent)
plt.savefig(os.path.join(OUT_PATH, 'mason-clim-SEQLD.png'))

plt.figure(figsize=(10, 10))
plt.title('Total totals')
plt.imshow(dsidx.totalx.data, extent=extent)
plt.savefig(os.path.join(OUT_PATH, 'totalx-clim-SEQLD.png'))

# load in lightning, crop to exten and plot

fp = os.path.join(DATA_DIR, "lightning-density-wztln-au-201510_202103.tif")
dataset = rasterio.open(fp)

lightning = dataset.read(1)
lat = np.linspace(dataset.bounds.top, dataset.bounds.bottom, dataset.height)
long = np.linspace(dataset.bounds.left, dataset.bounds.right, dataset.width)

mask1 = (dsidx.latitude.data.min() <= lat) & (lat <= dsidx.latitude.data.max())
mask2 = (dsidx.longitude.data.min() <= long) & (long <= dsidx.longitude.data.max())

mask = mask1[:, None] & mask2[None, :]


plt.figure(figsize=(10, 10))
plt.title('Lightning')
plt.imshow(lightning[mask].reshape((mask1.sum(), mask2.sum())), extent=extent)
plt.savefig(os.path.join(OUT_PATH, 'lightning-clim-SEQLD.png'))