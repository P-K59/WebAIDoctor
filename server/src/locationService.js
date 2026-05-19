export const cityCoords = {
  delhi: [28.6139, 77.209],
  "new delhi": [28.6139, 77.209],
  mumbai: [19.076, 72.8777],
  bombay: [19.076, 72.8777],
  bangalore: [12.9716, 77.5946],
  bengaluru: [12.9716, 77.5946],
  hyderabad: [17.385, 78.4867],
  chennai: [13.0827, 80.2707],
  kolkata: [22.5726, 88.3639],
  pune: [18.5204, 73.8567],
  ahmedabad: [23.0225, 72.5714],
  jaipur: [26.9124, 75.7873],
  lucknow: [26.8467, 80.9462],
  chandigarh: [30.7333, 76.7794],
  gurgaon: [28.4595, 77.0266],
  gurugram: [28.4595, 77.0266],
  noida: [28.5355, 77.391]
};

export async function detectCityFromIp() {
  const apis = [
    ["https://ipapi.co/json/", "city", "latitude", "longitude"],
    ["https://ip-api.com/json/", "city", "lat", "lon"],
    ["https://ipwho.is/", "city", "latitude", "longitude"]
  ];

  for (const [url, cityKey, latKey, lonKey] of apis) {
    try {
      const response = await fetch(url, { headers: { "User-Agent": "AIHealthApp/2.0" } });
      const data = await response.json();
      if (data?.[cityKey] && data?.[latKey] && data?.[lonKey]) {
        return { city: String(data[cityKey]), lat: Number(data[latKey]), lon: Number(data[lonKey]) };
      }
    } catch {
      // Try the next provider.
    }
  }

  return { city: "", lat: null, lon: null };
}

export async function geocodeCity(city = "") {
  const key = city.toLowerCase().trim();
  if (cityCoords[key]) {
    const [lat, lon] = cityCoords[key];
    return { lat, lon };
  }

  const fuzzy = Object.entries(cityCoords).find(([name]) => key.includes(name) || name.includes(key));
  if (fuzzy) {
    const [lat, lon] = fuzzy[1];
    return { lat, lon };
  }

  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.search = new URLSearchParams({ q: `${city}, India`, format: "json", limit: "1" });
  const response = await fetch(url, { headers: { "User-Agent": "AIHealthApp/2.0" } });
  const data = await response.json();
  if (!data?.length) return { lat: null, lon: null };

  return { lat: Number(data[0].lat), lon: Number(data[0].lon) };
}

export async function getHospitals(lat, lon) {
  const query = `
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:12000,${lat},${lon});
      way["amenity"="hospital"](around:12000,${lat},${lon});
      node["amenity"="clinic"](around:12000,${lat},${lon});
      node["healthcare"="hospital"](around:12000,${lat},${lon});
    );
    out center tags;
  `;

  const response = await fetch("https://overpass-api.de/api/interpreter", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "AIHealthApp/2.0" },
    body: new URLSearchParams({ data: query })
  });
  const data = await response.json();
  const seen = new Set();

  return (data.elements || [])
    .map((element) => {
      const tags = element.tags || {};
      const name = (tags.name || "").trim();
      if (!name || seen.has(name)) return null;
      seen.add(name);
      const center = element.center || element;
      const address =
        [tags["addr:housenumber"], tags["addr:street"], tags["addr:suburb"]].filter(Boolean).join(", ") ||
        "Address not listed";

      return {
        name,
        address,
        phone: tags.phone || tags["contact:phone"] || "",
        opening: tags.opening_hours || "",
        amenity: tags.amenity || tags.healthcare || "hospital",
        lat: Number(center.lat || lat),
        lon: Number(center.lon || lon)
      };
    })
    .filter(Boolean)
    .sort((a, b) => (a.amenity === "hospital" ? 0 : 1) - (b.amenity === "hospital" ? 0 : 1))
    .slice(0, 20);
}
