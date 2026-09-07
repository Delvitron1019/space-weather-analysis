"""Tidy the DONKI catalogs into one Tableau-ready CSV.

Tableau reads column names literally, so fields are named for a person rather
than for code. Two derived columns do the work the raw catalog will not:

  Flare Class / Flare Magnitude
      `class_type` packs both into one string ("M2.0"). Split so class can be a
      colour and magnitude can be a size or an axis.

  Solar Latitude / Solar Longitude / Degrees From Centre
      `source_location` packs disk position into one string ("N25E90").
      Longitude is measured from the central meridian, so its absolute value is
      how far toward the limb an event occurred. That is the confounder in the
      study design: a flare near the limb is observed at a steep angle and reads
      weaker than the same flare at disk centre, and it is the field to plot
      against magnitude to see the effect.

Run:  python src/make_tableau_extract.py
Out:  data/tableau_space_weather.csv
"""

import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")

LOC = re.compile(r"^([NS])(\d{1,2})([EW])(\d{1,3})$")
CLS = re.compile(r"^([ABCMXG])([\d.]*)$")


def parse_location(v):
    """'N25E90' -> (+25, -90). West of centre is positive, east negative."""
    if not isinstance(v, str):
        return (None, None)
    m = LOC.match(v.strip().upper())
    if not m:
        return (None, None)
    ns, lat, ew, lon = m.groups()
    return (int(lat) * (1 if ns == "N" else -1),
            int(lon) * (1 if ew == "W" else -1))


def parse_class(v):
    """'M2.0' -> ('M', 2.0). Storm codes ('G0') return magnitude None."""
    if not isinstance(v, str):
        return (None, None)
    m = CLS.match(v.strip().upper())
    if not m:
        return (None, None)
    letter, mag = m.groups()
    try:
        return (letter, float(mag) if mag else None)
    except ValueError:
        return (letter, None)


def main():
    df = pd.read_csv(os.path.join(DATA, "space_weather_unified.csv"))
    n_in = len(df)

    begin = pd.to_datetime(df["begin_time"], errors="coerce", utc=True)
    peak = pd.to_datetime(df["peak_time"], errors="coerce", utc=True)
    end = pd.to_datetime(df["end_time"], errors="coerce", utc=True)

    cls = df["class_type"].apply(parse_class)
    loc = df["source_location"].apply(parse_location)

    out = pd.DataFrame({
        "Event ID": df["event_id"],
        "Event Type": df["event_type"],
        "Begin Time": begin.dt.tz_localize(None),
        "Peak Time": peak.dt.tz_localize(None),
        "End Time": end.dt.tz_localize(None),
        "Date": begin.dt.tz_localize(None).dt.date,
        "Year": begin.dt.year,
        "Month": begin.dt.month,
        "Month Name": begin.dt.strftime("%b"),
        "Hour": begin.dt.hour,
        "Class Code": df["class_type"],
        "Flare Class": [c for c, _ in cls],
        "Flare Magnitude": [m for _, m in cls],
        "Solar Latitude": [a for a, _ in loc],
        "Solar Longitude": [o for _, o in loc],
        "Active Region": df["active_region"],
        "Kp Index": df["kp_index"],
        "Instruments": df["instruments"],
    })

    out["Degrees From Centre"] = out["Solar Longitude"].abs()
    out["Hemisphere"] = out["Solar Latitude"].apply(
        lambda v: None if pd.isna(v) else ("Northern" if v >= 0 else "Southern"))
    out["Disk Position"] = out["Degrees From Centre"].apply(
        lambda v: None if pd.isna(v) else ("Near limb (>60°)" if v > 60
                                           else "Mid disk (30-60°)" if v > 30
                                           else "Near centre (<30°)"))
    dur = (end - begin).dt.total_seconds() / 60.0
    out["Duration Minutes"] = dur.where(dur.between(0, 60 * 24))

    assert len(out) == n_in, "row count changed during reshape"
    path = os.path.join(DATA, "tableau_space_weather.csv")
    out.to_csv(path, index=False)

    print("rows: %s (unchanged)" % f"{len(out):,}")
    print("\nparse coverage:")
    for col in ["Flare Class", "Flare Magnitude", "Solar Latitude", "Degrees From Centre",
                "Duration Minutes", "Kp Index"]:
        print("  %-22s %5d non-null  (%.1f%%)"
              % (col, out[col].notna().sum(), 100 * out[col].notna().mean()))
    print("\nunparsed source_location values: %d"
          % int(df["source_location"].notna().sum() - out["Solar Latitude"].notna().sum()))
    print("unparsed class_type values:      %d"
          % int(df["class_type"].notna().sum() - out["Flare Class"].notna().sum()))
    print("\nFlare Class:"); print(out["Flare Class"].value_counts().to_string())
    print("\nDisk Position:"); print(out["Disk Position"].value_counts().to_string())
    print("\nwrote data/tableau_space_weather.csv")


if __name__ == "__main__":
    main()
