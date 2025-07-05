import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Prakiraan Cuaca DKI Jakarta", layout="wide")
st.title("📡 Prakiraan Cuaca - DKI Jakarta (GFS)")
st.markdown("### Yanti Mala_M8TB_14.24.0014")

@st.cache_data
def load_dataset(run_date, run_hour):
    base_url = f"https://nomads.ncep.noaa.gov/dods/gfs_0p25_1hr/gfs{run_date}/gfs_0p25_1hr_{run_hour}z"
    ds = xr.open_dataset(base_url)
    return ds

# Sidebar
st.sidebar.title("⚙️ Pengaturan")
today = datetime.utcnow()
run_date = st.sidebar.date_input("Tanggal Run GFS (UTC)", today.date())
run_hour = st.sidebar.selectbox("Jam Run GFS (UTC)", ["00", "06", "12", "18"])
forecast_hour = st.sidebar.slider("Jam ke depan", 0, 240, 0, step=1)
parameter = st.sidebar.selectbox("Parameter", [
    "Curah Hujan per jam (pratesfc)",
    "Suhu Permukaan (tmp2m)",
    "Angin Permukaan (ugrd10m & vgrd10m)",
    "Tekanan Permukaan Laut (prmslmsl)"
])
show_contour = st.sidebar.checkbox("Tampilkan Kontur", value=False)

if st.sidebar.button("🔎 Tampilkan Visualisasi"):
    try:
        ds = load_dataset(run_date.strftime("%Y%m%d"), run_hour)
        if forecast_hour >= len(ds.time):
            st.error("Forecast hour melebihi jangkauan data.")
            st.stop()
        st.success("Dataset berhasil dimuat.")
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()

    is_vector = False

    if "pratesfc" in parameter:
        var = ds["pratesfc"][forecast_hour, :, :] * 3600
        label = "Curah Hujan (mm/jam)"
        cmap = "Blues"
        vmin, vmax = 0, 50
    elif "tmp2m" in parameter:
        var = ds["tmp2m"][forecast_hour, :, :] - 273.15
        label = "Suhu (°C)"
        cmap = "coolwarm"
        vmin, vmax = 24, 36
    elif "ugrd10m" in parameter:
        u = ds["ugrd10m"][forecast_hour, :, :]
        v = ds["vgrd10m"][forecast_hour, :, :]
        speed = (u**2 + v**2)**0.5 * 1.94384
        var = speed
        label = "Kecepatan Angin (knot)"
        cmap = "YlGnBu"
        vmin, vmax = 0, 25
        is_vector = True
    elif "prmsl" in parameter:
        var = ds["prmslmsl"][forecast_hour, :, :] / 100
        label = "Tekanan Permukaan Laut (hPa)"
        cmap = "cool"
        vmin, vmax = 1000, 1020
    else:
        st.warning("Parameter tidak dikenali.")
        st.stop()

    # Wilayah DKI Jakarta lebih sempit & detail
    lat_min, lat_max = -6.4, -5.9
    lon_min, lon_max = 106.6, 107.05

    var = var.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
    if is_vector:
        u = u.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
        v = v.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))

    fig = plt.figure(figsize=(12, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

    valid_time = pd.to_datetime(str(ds.time[forecast_hour].values))
    valid_str = valid_time.strftime("%HUTC %a %d %b %Y")
    tstr = f"t+{forecast_hour:03d}"

    ax.set_title(f"{label} - Valid {valid_str} (GFS {tstr})", fontsize=14, fontweight="bold", pad=10)

    im = ax.pcolormesh(var.lon, var.lat, var.values, cmap=cmap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
    cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02)
    cbar.set_label(label)

    if is_vector:
        ax.quiver(var.lon[::2], var.lat[::2], u.values[::2, ::2], v.values[::2, ::2],
                  transform=ccrs.PlateCarree(), scale=700, width=0.0025, color='black')

    if show_contour:
        cs = ax.contour(var.lon, var.lat, var.values, levels=10, colors='black', linewidths=0.6, transform=ccrs.PlateCarree())
        ax.clabel(cs, fmt="%.0f", colors='black', fontsize=8)

    # Tambahan fitur agar peta terlihat "hidup"
    ax.coastlines(resolution='10m', linewidth=0.7)
    ax.add_feature(cfeature.BORDERS.with_scale('10m'), linestyle=':')
    ax.add_feature(cfeature.LAND, facecolor='whitesmoke')
    ax.add_feature(cfeature.RIVERS, edgecolor='blue', linewidth=0.5)
    ax.add_feature(cfeature.LAKES, facecolor='lightblue', alpha=0.5)

    # Titik pusat Kemayoran, Jakarta
    ax.plot(106.8462, -6.1745, marker='o', color='red', markersize=6, transform=ccrs.PlateCarree())
    ax.text(106.86, -6.18, 'Kemayoran', transform=ccrs.PlateCarree(), fontsize=9, color='red')

    fig.tight_layout()
    st.pyplot(fig)
