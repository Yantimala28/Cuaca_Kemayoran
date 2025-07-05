# Perbaiki bagian plotting

fig = plt.figure(figsize=(10, 8))  # Ukuran lebih besar
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([106.6, 107.05, -6.4, -5.9], crs=ccrs.PlateCarree())

# Judul gabungan 1 baris
valid_time = ds.time[forecast_hour].values
valid_dt = pd.to_datetime(str(valid_time))
valid_str = valid_dt.strftime("%HUTC %a, %d %b %Y")
tstr = f"t+{forecast_hour:03d}"
ax.set_title(f"{label} • Valid: {valid_str} • GFS {tstr}",
             fontsize=12, fontweight="bold", loc="center")

# Plot data
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
