import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { marked } from "marked";
import {
  Activity,
  AlertTriangle,
  Building2,
  FileText,
  HeartPulse,
  Loader2,
  MapPin,
  Navigation,
  Search,
  Star,
  Stethoscope,
  Upload,
  CheckCircle2,
  AlertCircle,
  WalletCards,
  CalendarCheck
} from "lucide-react";
import "./styles.css";

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (import.meta.env.DEV ? "http://127.0.0.1:5050" : "");

const tabs = [
  { id: "guidance", label: "Health Guidance", icon: HeartPulse },
  { id: "reports", label: "Report Analysis", icon: FileText },
  { id: "hospitals", label: "Hospitals Near Me", icon: Building2 },
  { id: "doctors", label: "Doctors Near Me", icon: Stethoscope }
];

const defaultSpecialties = [
  "General Physician",
  "Dentist",
  "Cardiologist",
  "Pediatrician",
  "Dermatologist",
  "Gynecologist",
  "Orthopedist"
];

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}

function App() {
  const [activeTab, setActiveTab] = useState("guidance");
  const [autoCity, setAutoCity] = useState("");
  const [specialties, setSpecialties] = useState(defaultSpecialties);

  useEffect(() => {
    api("/api/meta").then((data) => setSpecialties(data.specialties || defaultSpecialties)).catch(() => {});
    api("/api/location").then((data) => setAutoCity(data.city || "")).catch(() => {});
  }, []);

  const ActiveIcon = tabs.find((tab) => tab.id === activeTab)?.icon || HeartPulse;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Activity size={28} />
          </div>
          <div>
            <h1>AI Health</h1>
            <p>Clinical guidance workspace</p>
          </div>
        </div>

        <nav className="nav-list" aria-label="Primary">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                className={activeTab === tab.id ? "nav-button active" : "nav-button"}
                onClick={() => setActiveTab(tab.id)}
                type="button"
              >
                <Icon size={18} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="emergency-box">
          <span>Emergency services</span>
          <strong>108 / 112 / 102</strong>
        </div>
      </aside>

      <main className="main-panel">
        <div className="topbar">
          <div>
            <span className="eyebrow">Full-stack web app</span>
            <h2>
              <ActiveIcon size={26} />
              {tabs.find((tab) => tab.id === activeTab)?.label}
            </h2>
          </div>
          <div className="location-pill">
            <MapPin size={16} />
            {autoCity || "Location not detected"}
          </div>
        </div>

        {activeTab === "guidance" && <Guidance autoCity={autoCity} />}
        {activeTab === "reports" && <Reports />}
        {activeTab === "hospitals" && <Hospitals autoCity={autoCity} />}
        {activeTab === "doctors" && <Doctors autoCity={autoCity} specialties={specialties} />}
      </main>
    </div>
  );
}

function Guidance({ autoCity }) {
  const [symptoms, setSymptoms] = useState("");
  const [city, setCity] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const effectiveCity = city.trim() || autoCity;

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(
        await api("/api/advice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symptoms, city: effectiveCity })
        })
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="work-grid">
      <div>
        <form className="panel" onSubmit={submit}>
          <div className="panel-heading">
            <h3>Describe Symptoms</h3>
            <p>Receive safe first-pass guidance and a matching specialty.</p>
          </div>
          <label>
            City
            <input value={city} onChange={(event) => setCity(event.target.value)} placeholder={autoCity || "Delhi"} />
          </label>
          <label>
            Symptoms
            <textarea
              value={symptoms}
              onChange={(event) => setSymptoms(event.target.value)}
              placeholder="Example: fever, sore throat, body pain for two days..."
              rows={8}
            />
          </label>
          <button className="primary-button" disabled={loading} type="submit">
            {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
            Get Advice & Find Doctors
          </button>
          {error && <div className="error">{error}</div>}
        </form>

        {result?.doctors?.length > 0 && <DoctorList doctors={result.doctors} compact />}
      </div>

      <div className="stack">
        {result?.isEmergency && (
          <div className="alert-card">
            <AlertTriangle size={22} />
            <div>
              <strong>Emergency warning</strong>
              <p>{result.advice}</p>
            </div>
          </div>
        )}
        {result && !result.isEmergency && (
          <ResultCard title="Health Suggestions" content={result.advice} variant="advice" />
        )}
      </div>
    </section>
  );
}

function Reports() {
  const [mode, setMode] = useState("lab");
  const [reportType, setReportType] = useState("Blood Report");
  const [patientContext, setPatientContext] = useState("");
  const [reportText, setReportText] = useState("");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    const formData = new FormData();
    formData.append("mode", mode);
    formData.append("reportType", reportType);
    formData.append("patientContext", patientContext);
    formData.append("reportText", reportText);
    if (file) formData.append("report", file);

    try {
      setResult(await api("/api/reports/analyze", { method: "POST", body: formData }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="panel wide-panel" onSubmit={submit}>
      <div className="segmented" role="tablist" aria-label="Report mode">
        <button className={mode === "lab" ? "selected" : ""} type="button" onClick={() => setMode("lab")}>
          Lab & Health Reports
        </button>
        <button className={mode === "imaging" ? "selected" : ""} type="button" onClick={() => setMode("imaging")}>
          X-rays & Imaging Notes
        </button>
      </div>

      <div className="form-grid">
        <label>
          Report type
          <input value={reportType} onChange={(event) => setReportType(event.target.value)} />
        </label>
        <label>
          Upload file
          <span className="file-input">
            <Upload size={18} />
            <input
              type="file"
              accept=".pdf,.txt,.csv,.jpg,.jpeg,.png"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
            {file?.name || "Choose PDF, image, TXT, or CSV"}
          </span>
        </label>
      </div>

      <label>
        Patient context
        <textarea
          value={patientContext}
          onChange={(event) => setPatientContext(event.target.value)}
          rows={4}
          placeholder="Age, symptoms, medicines, known conditions, or radiologist findings..."
        />
      </label>

      <label>
        Paste report text
        <textarea
          value={reportText}
          onChange={(event) => setReportText(event.target.value)}
          rows={7}
          placeholder="Optional. Paste report text here when the PDF is scanned or image OCR is unavailable."
        />
      </label>

      <button className="primary-button" disabled={loading} type="submit">
        {loading ? <Loader2 className="spin" size={18} /> : <FileText size={18} />}
        Analyze Report
      </button>
      {error && <div className="error">{error}</div>}
      {result && (
        <div className="report-results">
          {result.preview && (
            <details>
              <summary>Extracted preview</summary>
              <pre>{result.preview}</pre>
            </details>
          )}
          <ResultCard title="Analysis Results" content={result.analysis} />
        </div>
      )}
    </form>
  );
}

function Hospitals({ autoCity }) {
  const [city, setCity] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const effectiveCity = city.trim() || autoCity;

  async function search(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setData(null);
    try {
      setData(await api(`/api/hospitals?city=${encodeURIComponent(effectiveCity)}`));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel wide-panel">
      <form className="search-row" onSubmit={search}>
        <label>
          City
          <input value={city} onChange={(event) => setCity(event.target.value)} placeholder={autoCity || "Mumbai"} />
        </label>
        <button className="primary-button" disabled={loading} type="submit">
          {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
          Find Hospitals
        </button>
      </form>
      {error && <div className="error">{error}</div>}
      {data && (
        <>
          <MapEmbed lat={data.lat} lon={data.lon} city={effectiveCity} />
          <HospitalList hospitals={data.hospitals} />
        </>
      )}
    </section>
  );
}

function Doctors({ autoCity, specialties }) {
  const [city, setCity] = useState("");
  const [specialty, setSpecialty] = useState(specialties[0] || "General Physician");
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const effectiveCity = city.trim() || autoCity;

  useEffect(() => {
    if (!specialties.includes(specialty)) setSpecialty(specialties[0] || "General Physician");
  }, [specialties, specialty]);

  async function search(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setDoctors([]);
    try {
      const data = await api(`/api/doctors?city=${encodeURIComponent(effectiveCity)}&specialty=${encodeURIComponent(specialty)}`);
      setDoctors(data.doctors || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel wide-panel">
      <form className="search-row" onSubmit={search}>
        <label>
          City
          <input value={city} onChange={(event) => setCity(event.target.value)} placeholder={autoCity || "Delhi"} />
        </label>
        <label>
          Specialty
          <select value={specialty} onChange={(event) => setSpecialty(event.target.value)}>
            {specialties.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <button className="primary-button" disabled={loading} type="submit">
          {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
          Search Doctors
        </button>
      </form>
      {error && <div className="error">{error}</div>}
      <DoctorList doctors={doctors} />
    </section>
  );
}

function MarkdownRenderer({ content }) {
  const html = useMemo(() => {
    try {
      return marked(content, { 
        breaks: true,
        gfm: true,
        headerIds: false
      });
    } catch {
      return `<p>${content}</p>`;
    }
  }, [content]);

  return <div className="markdown-content" dangerouslySetInnerHTML={{ __html: html }} />;
}

function AdviceRenderer({ content }) {
  const { intro, sections } = useMemo(() => {
    const parts = content.split(/^##\s+/m);
    const opening = parts.shift()?.trim() || "";
    const parsedSections = parts
      .map((part) => {
        const [titleLine, ...bodyLines] = part.trim().split("\n");
        return {
          title: titleLine?.trim(),
          body: bodyLines.join("\n").trim()
        };
      })
      .filter((section) => section.title && section.body);

    return { intro: opening, sections: parsedSections };
  }, [content]);

  if (!sections.length) return <MarkdownRenderer content={content} />;

  return (
    <div className="advice-content">
      {intro && <MarkdownRenderer content={intro} />}
      <div className="advice-section-list">
        {sections.map((section) => (
          <section className={`advice-section ${getAdviceSectionClass(section.title)}`} key={section.title}>
            <h4>{section.title}</h4>
            <MarkdownRenderer content={section.body} />
          </section>
        ))}
      </div>
    </div>
  );
}

function getAdviceSectionClass(title) {
  const lower = title.toLowerCase();
  if (lower.includes("summary")) return "advice-summary";
  if (lower.includes("doctor")) return "advice-warning";
  if (lower.includes("don't") || lower.includes("dont")) return "advice-dont";
  if (lower.includes("medicine") || lower.includes("otc")) return "advice-medicine";
  if (lower === "do") return "advice-do";
  return "";
}

function ResultCard({ title, content, variant = "default" }) {
  return (
    <article className={variant === "advice" ? "result-card advice-card" : "result-card"}>
      <h3>{title}</h3>
      {variant === "advice" ? <AdviceRenderer content={content} /> : <MarkdownRenderer content={content} />}
      <div className="disclaimer">
        <AlertCircle size={16} />
        <span>Educational support only. Confirm decisions with a qualified medical professional.</span>
      </div>
    </article>
  );
}

function DoctorList({ doctors, compact = false }) {
  if (!doctors?.length) return null;
  
  const specialty = doctors[0]?.specialty || "Doctors";
  const city = doctors[0]?.address?.split(",")[0] || "Your Area";
  
  return (
    <>
      <div className="doctor-header-card">
        <div className="doctor-header-icon">
          <Stethoscope size={26} />
        </div>
        <div className="header-content">
          <span className="doctor-kicker">{doctors.length} recommended matches</span>
          <h2>Recommended {specialty} Near You</h2>
          <p>{city} - Specialty matched from your search</p>
        </div>
      </div>
      
      <div className={compact ? "doctor-cards-container" : "card-grid"}>
        {doctors.map((doctor, index) => (
          <article className="doctor-card" key={`${doctor.name}-${index}`}>
            <div className="doctor-header">
              <div className="doctor-info">
                <h3>{doctor.name}</h3>
                <div className="doctor-meta">
                  <span className="specialty-badge">{doctor.specialty}</span>
                  {doctor.reviews && (
                    <span className="verified">
                      <CheckCircle2 size={13} />
                      Verified
                    </span>
                  )}
                </div>
            </div>
              <div className="doctor-rating">
                <Star size={16} fill="currentColor" />
                <span className="rating-number">{doctor.rating}</span>
                <span className="rating-reviews">{doctor.reviews} Reviews</span>
              </div>
            </div>
            
            <div className="doctor-details">
              <p className="hospital-name">
                <MapPin size={17} />
                {doctor.hospital}
              </p>
              <p className="location">{doctor.address || doctor.specialty}</p>
              <div className="doctor-facts">
                <span>
                  <CalendarCheck size={15} />
                  {doctor.experience}
                </span>
                <span>
                  <WalletCards size={15} />
                  {doctor.fees}
                </span>
              </div>
            </div>

            <div className="doctor-actions">
              <a href={doctor.link} target="_blank" rel="noreferrer" className="btn-book">
                Book Appointment
              </a>
              <a href={doctor.mapLink} target="_blank" rel="noreferrer" className="btn-map">
                <Navigation size={16} />
                View on Map
              </a>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}

function HospitalList({ hospitals }) {
  if (!hospitals?.length) return <div className="empty">No hospitals found in this area.</div>;
  return (
    <div className="card-grid">
      {hospitals.map((hospital) => {
        const destination = encodeURIComponent(`${hospital.name} ${hospital.address}`);
        return (
          <article className="info-card" key={`${hospital.name}-${hospital.lat}`}>
            <span className="source">{hospital.amenity}</span>
            <h3>{hospital.name}</h3>
            <p>{hospital.address}</p>
            <div className="facts">
              {hospital.phone && <span>{hospital.phone}</span>}
              {hospital.opening && <span>{hospital.opening}</span>}
            </div>
            <div className="actions">
              <a href={`https://www.google.com/maps/dir/?api=1&destination=${destination}`} target="_blank" rel="noreferrer">
                Directions
              </a>
            </div>
          </article>
        );
      })}
    </div>
  );
}

function MapEmbed({ lat, lon, city }) {
  const src = useMemo(
    () =>
      `https://www.openstreetmap.org/export/embed.html?bbox=${lon - 0.06}%2C${lat - 0.04}%2C${lon + 0.06}%2C${
        lat + 0.04
      }&layer=mapnik&marker=${lat}%2C${lon}`,
    [lat, lon]
  );

  return <iframe className="map-frame" title={`Hospitals near ${city}`} src={src} loading="lazy" />;
}

createRoot(document.getElementById("root")).render(<App />);
