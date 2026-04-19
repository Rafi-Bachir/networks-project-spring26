"""
rtt vs speed of light
networks assignment

run with: python rtt_speedoflight.py
requires: pip install requests matplotlib numpy
"""

import math, time, os, requests, numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import urllib.request

# -----------------------------------------------
# config
# -----------------------------------------------

TARGETS = {
    "Tokyo":        {"url": "http://www.google.co.jp",   "coords": (35.6762,  139.6503), "continent": "Asia"},
    "São Paulo":    {"url": "http://www.google.com.br",  "coords": (-23.5505, -46.6333), "continent": "S. America"},
    "Lagos":        {"url": "http://www.google.com.ng",  "coords": (6.5244,     3.3792), "continent": "Africa"},
    "Frankfurt":    {"url": "http://www.google.de",      "coords": (50.1109,    8.6821), "continent": "Europe"},
    "Sydney":       {"url": "http://www.google.com.au",  "coords": (-33.8688, 151.2093), "continent": "Oceania"},
    "Mumbai":       {"url": "http://www.google.co.in",   "coords": (19.0760,   72.8777), "continent": "Asia"},
    "London":       {"url": "http://www.google.co.uk",   "coords": (51.5074,   -0.1278), "continent": "Europe"},
    "Singapore":    {"url": "http://www.google.com.sg",  "coords": (1.3521,   103.8198), "continent": "Asia"},
}

PROBES           = 15       # number of requests per city
FIBER_SPEED_KM_S = 200_000  # speed of light in fiber in km/s
FIGURES_DIR      = "figures"

CONTINENT_COLORS = {
    "Asia":       "#e63946",
    "S. America": "#2a9d8f",
    "Africa":     "#e9c46a",
    "Europe":     "#457b9d",
    "Oceania":    "#a8dadc",
}

# -----------------------------------------------
# task 1 - measure rtts
# -----------------------------------------------

def measure_rtt(url, probes=PROBES):
    # send http requests to the url and record how long each one takes
    samples = []
    lost    = 0

    for _ in range(probes):
        try:
            # record time before and after the request
            # read(1) and close() force a fresh connection each probe
            start = time.perf_counter()
            response = urllib.request.urlopen(url, timeout=3)
            response.read(1)
            elapsed_ms = (time.perf_counter() - start) * 1000
            response.close()
            samples.append(elapsed_ms)
        except Exception:
            # request failed or timed out - count it as lost
            lost += 1
        time.sleep(0.2)  # wait between probes

    # if every probe failed return none for all stats
    if not samples:
        return {"min_ms": None, "mean_ms": None, "median_ms": None,
                "loss_pct": 100.0, "samples": []}

    arr = np.array(samples)
    return {
        "min_ms":    float(np.min(arr)),
        "mean_ms":   float(np.mean(arr)),
        "median_ms": float(np.median(arr)),
        "loss_pct":  (lost / probes) * 100,
        "samples":   samples,
    }


# -----------------------------------------------
# task 2 - haversine distance and inefficiency
# -----------------------------------------------

def great_circle_km(lat1, lon1, lat2, lon2):
    # calculate the straight line distance between two points on earth in km
    # uses the haversine formula: a = sin^2(dlat/2) + cos(lat1)*cos(lat2)*sin^2(dlon/2)
    # then d = 2 * R * atan2(sqrt(a), sqrt(1-a)), where R = 6371 km
    R    = 6371
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_my_location():
    # look up this machine's location from its public ip address
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat, lon = map(float, r["loc"].split(","))
        return lat, lon, r.get("city", "Your Location")
    except Exception:
        print("could not auto-detect location, defaulting to boston")
        return 42.3601, -71.0589, "Boston"


def compute_inefficiency(results, src_lat, src_lon):
    # for each city: calculate distance, theoretical minimum rtt, and how far off we are
    for city, data in results.items():
        city_lat, city_lon = data["coords"]

        # straight line distance from our machine to the city
        distance_km = great_circle_km(src_lat, src_lon, city_lat, city_lon)

        # theoretical minimum rtt = round trip distance / fiber speed, converted to ms
        theoretical_min_ms = (distance_km / FIBER_SPEED_KM_S) * 2 * 1000

        # ratio of real rtt to theoretical minimum - higher means worse routing
        median_ms = data.get("median_ms")
        ratio = median_ms / theoretical_min_ms if median_ms is not None else None

        data["distance_km"]        = distance_km
        data["theoretical_min_ms"] = theoretical_min_ms
        data["inefficiency_ratio"] = ratio
        data["high_inefficiency"]  = (ratio is not None and ratio > 3.0)

    return results


# -----------------------------------------------
# task 3 - plots
# -----------------------------------------------

def make_plots(results):
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # only include cities we got data for, sorted by distance
    valid  = {c: d for c, d in results.items() if d.get("median_ms") is not None}
    cities = sorted(valid, key=lambda c: valid[c]["distance_km"])

    # figure 1 - grouped bar chart: measured rtt vs theoretical minimum per city
    fig, ax = plt.subplots(figsize=(11, 6))

    x            = np.arange(len(cities))
    bar_width    = 0.35
    medians      = [valid[c]["median_ms"]         for c in cities]
    theoreticals = [valid[c]["theoretical_min_ms"] for c in cities]

    ax.bar(x - bar_width / 2, medians,      bar_width, label="measured median rtt", color="#457b9d")
    ax.bar(x + bar_width / 2, theoreticals, bar_width, label="theoretical min rtt", color="#a8dadc")

    ax.set_xlabel("city (sorted by distance from source)")
    ax.set_ylabel("rtt (ms)")
    ax.set_title("measured vs theoretical minimum rtt by city")
    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=25, ha="right")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(f"{FIGURES_DIR}/fig1_rtt_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()

    # figure 2 - scatter plot: distance vs measured rtt, colored by continent
    fig, ax = plt.subplots(figsize=(10, 7))

    # draw the theoretical minimum as a dashed line
    max_dist   = max(valid[c]["distance_km"] for c in cities)
    dist_range = np.linspace(0, max_dist * 1.05, 300)
    theor_line = (dist_range / FIBER_SPEED_KM_S) * 2 * 1000
    ax.plot(dist_range, theor_line, linestyle="--", color="gray", linewidth=1.5,
            label="theoretical minimum (fiber speed)")

    # plot each city as a dot colored by continent
    for city in cities:
        d     = valid[city]
        color = CONTINENT_COLORS.get(d["continent"], "#999999")
        ax.scatter(d["distance_km"], d["median_ms"], color=color, s=80, zorder=3)
        ax.annotate(city, (d["distance_km"], d["median_ms"]),
                    textcoords="offset points", xytext=(6, 4), fontsize=9)

    # build continent legend
    legend_patches = [
        mpatches.Patch(color=color, label=continent)
        for continent, color in CONTINENT_COLORS.items()
        if any(valid[c]["continent"] == continent for c in cities)
    ]
    legend_patches.append(
        plt.Line2D([0], [0], linestyle="--", color="gray", label="theoretical minimum")
    )
    ax.legend(handles=legend_patches, loc="upper left", fontsize=9)

    ax.set_xlabel("great-circle distance from source (km)")
    ax.set_ylabel("measured median rtt (ms)")
    ax.set_title("rtt vs great-circle distance (colored by continent)")
    ax.grid(linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(f"{FIGURES_DIR}/fig2_distance_scatter.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"figures saved to {FIGURES_DIR}/")


# -----------------------------------------------
# main
# -----------------------------------------------

def main():
    src_lat, src_lon, src_city = get_my_location()
    print(f"Your location: {src_city} ({src_lat:.4f}, {src_lon:.4f})\n")

    results = {}
    for city, info in TARGETS.items():
        print(f"Probing {city} ({info['url']}) ...", end=" ", flush=True)
        stats = measure_rtt(info["url"])
        results[city] = {**stats, "coords": info["coords"], "continent": info["continent"]}
        med = stats.get("median_ms")
        print(f"median={med:.1f} ms  loss={stats['loss_pct']:.0f}%" if med else "unreachable")

    results = compute_inefficiency(results, src_lat, src_lon)

    print(f"\n{'City':<14} {'Dist km':>8} {'Median ms':>10} {'Theor. ms':>10} {'Ratio':>7}")
    print("-" * 55)
    for city, d in sorted(results.items(), key=lambda x: x[1].get("distance_km", 0)):
        dist  = d.get("distance_km", 0)
        med   = d.get("median_ms")
        theor = d.get("theoretical_min_ms")
        ratio = d.get("inefficiency_ratio")
        flag  = " !!" if d.get("high_inefficiency") else ""
        print(f"{city:<14} {dist:>8.0f} "
              f"{(f'{med:.1f}' if med else 'N/A'):>10} "
              f"{(f'{theor:.1f}' if theor else 'N/A'):>10} "
              f"{(f'{ratio:.2f}' if ratio else 'N/A'):>7}{flag}")

    make_plots(results)

if __name__ == "__main__":
    main()
