from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>PFAS DC RiskScope</title>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  />
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; padding: 1rem; }
    #map { height: 460px; margin-bottom: 0.75rem; }
    label { font-weight: 600; display: block; margin-top: 0.5rem; }
    input, textarea { width: 100%; padding: 0.25rem; font-family: monospace; }
    button { margin-top: 0.5rem; margin-right: 0.5rem; padding: 0.4rem 0.8rem; }
    pre { background: #111; color: #eee; padding: 0.5rem; overflow-x: auto; }
  </style>
</head>
<body>
  <h2>PFAS DC RiskScope – Click to Select a Site</h2>
  <div id="map"></div>
  <p id="clicked-location">Clicked location: (none)</p>

  <label>State (auto-filled):</label>
  <input id="state" value="VA" />

  <label>Receiving flow (MGD):</label>
  <input id="receiving_flow" value="42.0" />

  <label>Discharge flow (MGD):</label>
  <input id="discharge_flow" value="3.5" />

  <label>PFAS discharge (ppt, JSON dict):</label>
  <textarea id="pfas_json" rows="5">
{
  "PFOA": 7.5,
  "PFOS": 6.2,
  "HFPO-DA": 5.0
}
  </textarea>

  <button id="run-btn">Run Simulation</button>
  <button id="pdf-btn">Download PDF</button>

  <h3>Simulation result (JSON)</h3>
  <pre id="result"></pre>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map('map').setView([38.9, -77.2], 8);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let marker = null;
    let lastLat = null;
    let lastLon = null;

    async function updateContextFromClick(lat, lon) {
      try {
        const url = `/location-context?lat=${lat}&lon=${lon}`;
        const resp = await fetch(url);
        if (!resp.ok) {
          console.error('Context fetch failed', resp.status);
          return;
        }
        const data = await resp.json();

        document.getElementById('state').value = data.state || 'VA';
        document.getElementById('receiving_flow').value = data.receiving_flow_mgd;
        document.getElementById('discharge_flow').value = data.discharge_flow_mgd;
        document.getElementById('pfas_json').value = JSON.stringify(
          data.discharge_pfas_ppt,
          null,
          2
        );
      } catch (err) {
        console.error('Error fetching context', err);
      }
    }

    map.on('click', async function(e) {
      const lat = e.latlng.lat.toFixed(4);
      const lon = e.latlng.lng.toFixed(4);
      lastLat = parseFloat(lat);
      lastLon = parseFloat(lon);

      if (marker) {
        marker.setLatLng(e.latlng);
      } else {
        marker = L.marker(e.latlng).addTo(map);
      }

      document.getElementById('clicked-location').textContent =
        `Clicked location: ${lat}, ${lon}`;

      // Ask backend for context based on lat/lon
      await updateContextFromClick(lat, lon);
    });

    function buildPayload() {
      const state = document.getElementById('state').value.trim() || 'VA';
      const receiving_flow = parseFloat(document.getElementById('receiving_flow').value);
      const discharge_flow = parseFloat(document.getElementById('discharge_flow').value);
      const rawPfas = document.getElementById('pfas_json').value;

      let pfasDict;
      try {
        pfasDict = JSON.parse(rawPfas);
      } catch (e) {
        alert('PFAS JSON is invalid. Please fix it.');
        throw e;
      }

      return {
        lat: lastLat,
        lon: lastLon,
        state: state,
        receiving_flow_mgd: receiving_flow,
        discharge_flow_mgd: discharge_flow,
        discharge_pfas_ppt: pfasDict
      };
    }

    async function runSimulation() {
      try {
        const payload = buildPayload();
        const resp = await fetch('/simulate-simple', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await resp.json();
        document.getElementById('result').textContent =
          JSON.stringify(data, null, 2);
      } catch (err) {
        console.error(err);
        alert('Simulation failed – see console for details');
      }
    }

    async function downloadPdf() {
      try {
        const payload = buildPayload();
        const resp = await fetch('/export-pdf-simple', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!resp.ok) {
          const txt = await resp.text();
          console.error('PDF error', resp.status, txt);
          alert('PDF generation failed – see console');
          return;
        }

        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'pfas_risk_report.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error(err);
        alert('PDF download failed – see console');
      }
    }

    document.getElementById('run-btn').addEventListener('click', runSimulation);
    document.getElementById('pdf-btn').addEventListener('click', downloadPdf);
  </script>
</body>
</html>
"""

@router.get("/ui", response_class=HTMLResponse)
async def ui_root():
    return HTMLResponse(DASHBOARD_HTML)
