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
    elif "tmp2m" in parameter:
        var = ds["tmp2m"][forecast_hour, :, :] - 273.15
        label = "Suhu (°C)"
        cmap = "coolwarm"
    elif "ugrd10m" in parameter:
        u = ds["ugrd10m"][forecast_hour, :, :]
        v = ds["vgrd10m"][forecast_hour, :, :]
        speed = (u**2 + v**2)**0.5 * 1.94384  # konversi ke knot
        var = speed
        label = "Kecepatan Angin (knot)"
        cmap = plt.cm.get_cmap("RdYlGn_r", 10)
        is_vector = True
    elif "prmsl" in parameter:
        var = ds["prmslmsl"][forecast_hour, :, :] / 100
        label = "Tekanan Permukaan Laut (hPa)"
        cmap = "cool"
        is_contour = True
    else:
        st.warning("Parameter tidak dikenali.")
        st.stop()

    # Fokus area DKI Jakarta dan sekitarnya
    var = var.sel(lat=slice(-6.5, -5.9), lon=slice(106.6, 107.1))
    if is_vector:
        u = u.sel(lat=slice(-6.5, -5.9), lon=slice(106.6, 107.1))
        v = v.sel(lat=slice(-6.5, -5.9), lon=slice(106.6, 107.1))

    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([106.6, 107.1, -6.5, -5.9], crs=ccrs.PlateCarree())

    # Judul peta
    valid_time = ds.time[forecast_hour].values
    valid_dt = pd.to_datetime(str(valid_time))
    valid_str = valid_dt.strftime("%HUTC %a, %d %b %Y")
    tstr = f"t+{forecast_hour:03d}"
    ax.set_title(f"{label} • Valid: {valid_str} • GFS {tstr}", fontsize=12, fontweight="bold", loc="center")

    # Plot parameter
    if is_contour:
        cs = ax.contour(var.lon, var.lat, var.values, levels=15, colors='black', linewidths=0.8, transform=ccrs.PlateCarree())
        ax.clabel(cs, fmt="%d", colors='black', fontsize=8)
    else:
        im = ax.pcolormesh(var.lon, var.lat, var.values,
                           cmap=cmap, vmin=0, vmax=50,
                           transform=ccrs.PlateCarree())
        cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.03, shrink=0.8)
        cbar.set_label(label)
        if is_vector:
            ax.quiver(var.lon[::1], var.lat[::1],
                      u.values[::1, ::1], v.values[::1, ::1],
                      transform=ccrs.PlateCarree(), scale=500, width=0.002, color='black')

    # Tambahkan fitur peta
    ax.coastlines(resolution='10m', linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, facecolor='lightgray')

    # Titik Kemayoran
    lon_kemayoran, lat_kemayoran = 106.8650, -6.1744
    ax.plot(lon_kemayoran, lat_kemayoran, marker='o', color='red', markersize=6, transform=ccrs.PlateCarree())
    ax.text(lon_kemayoran + 0.015, lat_kemayoran + 0.015, "Kemayoran", fontsize=10,
            fontweight='bold', color='red', transform=ccrs.PlateCarree(),
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2'))

    st.pyplot(fig)
