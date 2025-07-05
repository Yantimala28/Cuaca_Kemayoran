import matplotlib.pyplot as plt
import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Prakiraan Cuaca Kemayoran", layout="wide")

st.title("📡 GFS Viewer Area Kemayoran (Realtime via NOMADS)")
st.header("Web Hasil Pembelajaran Pengelolaan Informasi Meteorologi")

# Identitas
st.markdown("**YANTI MALA**  \n*M8TB_14.24.0014_2025*")

@st.cache_data
def load_dataset(run_date, run_hour):
    base_url = f"https://nomads.ncep.noaa.gov/dods/gfs_0p25_1hr/gfs{run_date}/gfs_0p25_1hr_{run_hour}z"
    ds = xr.open_dataset(base_url)
    return ds

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

if st.sidebar.button("🔎 Tampilkan Visualisasi"):
    try:
        ds = load_dataset(run_date.strftime("%Y%m%d"), run_hour)
        if forecast_hour >= len(ds.time):
            st.error(f"Data untuk jam ke-{forecast_hour} belum tersedia.")
            st.stop()
        st.success("Dataset berhasil dimuat.")
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()

    is_contour = False
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
        vmin, vmax = None, None
    elif "ugrd10m" in parameter:
        u = ds["ugrd10m"][forecast_hour, :, :]
        v = ds["vgrd10m"][forecast_hour, :, :]
        speed = (u**2 + v**2)**0.5 * 1.94384
        var = speed
        label = "Kecepatan Angin (knot)"
        cmap = plt.cm.get_cmap("RdYlGn_r", 10)
        is_vector = True
        vmin, vmax = 0, 50
    elif "prmsl" in parameter:
        var = ds["prmslmsl"][forecast_hour, :, :] / 100
        label = "Tekanan Permukaan Laut (hPa)"
        cmap = "cool"
        is_contour = True
    else:
        st.warning("Parameter tidak dikenali.")
        st.stop()

    # Fokus wilayah sekitar Kemayoran
    var = var.sel(lat=slice(-7.5, -5.5), lon=slice(106, 108))

    if is_vector:
        u = u.sel(lat=slice(-7.5, -5.5), lon=slice(106, 108))
        v = v.sel(lat=slice(-7.5, -5.5), lon=slice(106, 108))

    fig = plt.figure(figsize=(8, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([106, 108, -7.5, -5.5], crs=ccrs.PlateCarree())

    valid_time = ds.time[forecast_hour].values
    valid_dt = pd.to_datetime(str(valid_time))
    valid_str = valid_dt.strftime("%HUTC %a %d %b %Y")
    tstr = f"t+{forecast_hour:03d}"

    plt.subplots_adjust(top=0.90)
    ax.set_title(f"{label} - Valid {valid_str}", fontsize=12, fontweight="bold", loc='center')

    if is_contour:
        cs = ax.contour(var.lon, var.lat, var.values, levels=15, colors='black', linewidths=0.8, transform=ccrs.PlateCarree())
        ax.clabel(cs, fmt="%d", colors='black', fontsize=8)
    else:
        im = ax.pcolormesh(var.lon, var.lat, var.values, cmap=cmap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
        cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02)
        cbar.set_label(label)
        if is_vector:
            ax.quiver(var.lon[::2], var.lat[::2], u.values[::2, ::2], v.values[::2, ::2], transform=ccrs.PlateCarree(), scale=700, width=0.002, color='black')

    ax.coastlines(resolution='10m', linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, facecolor='lightgray')

    # Titik Kemayoran (DKI Jakarta)
    lon_kemayoran, lat_kemayoran = 106.865, -6.165
    ax.plot(lon_kemayoran, lat_kemayoran, marker='o', color='red', markersize=6, transform=ccrs.PlateCarree())
    ax.text(lon_kemayoran + 0.05, lat_kemayoran + 0.05, "Kemayoran", fontsize=9, fontweight='bold', color='red',
            transform=ccrs.PlateCarree(), bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2'))

    st.pyplot(fig)
