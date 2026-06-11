# 📡 Aruba Wireless AI Analyzer

> AI-powered wireless troubleshooting tool — integrated with **Aruba Wireless Controller** and backed by **Hermes Agent** for automated diagnosis, visual analytics, and one-click remediation.

---

## 🧭 Overview

**Aruba Wireless AI Analyzer** adalah aplikasi web yang menghubungkan langsung ke Aruba Wireless Controller untuk memantau kondisi wireless secara real-time, menganalisa masalah client/AP, menyajikan hasil analisis dalam bentuk visual yang informatif, dan mengeksekusi konfigurasi remediation secara otomatis melalui AI Agent berbasis **Hermes**.

### Cara Kerja

```
┌────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                       │
│   (Charts, Client Table, Alert Panel, Resolve Button)      │
└───────────────────┬──────────────────┬─────────────────────┘
                    │                  │
          REST API  │          AI Chat │ Resolve Action
                    ▼                  ▼
┌───────────────────────┐   ┌──────────────────────────────┐
│  Aruba Controller API  │   │     Hermes AI Agent Backend  │
│  - Client Stats        │   │  - Diagnose Issue            │
│  - AP Health           │   │  - Recommend Fix             │
│  - RF Data             │   │  - Execute SSH/REST Command  │
│  - Event Logs          │   │  - Confirm Remediation       │
└───────────────────────┘   └──────────────────────────────┘
```

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🔌 **Live Controller Connection** | Konek ke Aruba WLC via REST API (AOS-CX / ArubaOS) |
| 📊 **Visual Analytics** | Chart RSSI trend, channel utilization, client distribution per AP |
| 🧠 **AI Diagnosis** | Hermes Agent menganalisa root cause berdasarkan data controller |
| 💡 **Smart Recommendation** | Saran fix spesifik per client/AP/SSID |
| ⚡ **One-Click Resolve** | Eksekusi konfigurasi otomatis via Hermes Agent ke controller |
| 📋 **Audit Log** | Riwayat semua aksi remediation yang dilakukan AI Agent |
| 🔔 **Alert Engine** | Deteksi otomatis anomali: roaming loop, deauth storm, RSSI drop |

---

## 🗂️ Struktur Project

```
aruba-wireless-ai-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI entrypoint
│   │   ├── config.py                 # Env & settings loader
│   │   ├── routers/
│   │   │   ├── clients.py            # Endpoint: client stats
│   │   │   ├── access_points.py      # Endpoint: AP health
│   │   │   ├── events.py             # Endpoint: controller event log
│   │   │   └── remediation.py        # Endpoint: trigger AI resolve
│   │   ├── services/
│   │   │   ├── aruba_client.py       # Aruba REST API wrapper
│   │   │   ├── hermes_agent.py       # Hermes AI Agent interface
│   │   │   └── analyzer.py           # Rule-based pre-analysis layer
│   │   └── models/
│   │       ├── client.py
│   │       ├── ap.py
│   │       └── issue.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx         # Main dashboard
│   │   │   ├── ClientDetail.jsx      # Per-client drill-down
│   │   │   └── AuditLog.jsx          # Remediation history
│   │   ├── components/
│   │   │   ├── RSSIChart.jsx         # RSSI trend line chart
│   │   │   ├── ChannelHeatmap.jsx    # Channel utilization heatmap
│   │   │   ├── ClientTable.jsx       # Live client list + status badge
│   │   │   ├── APHealthCard.jsx      # Per-AP health summary card
│   │   │   ├── AlertPanel.jsx        # Active issue alerts
│   │   │   ├── AIInsightPanel.jsx    # Hermes diagnosis + recommendation
│   │   │   └── ResolveButton.jsx     # One-click remediation trigger
│   │   ├── hooks/
│   │   │   ├── useAruba.js           # Polling hook untuk controller data
│   │   │   └── useHermes.js          # Hook untuk AI Agent interaction
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
│
├── hermes/
│   ├── agent_config.yaml             # Hermes Agent tools & skill config
│   ├── tools/
│   │   ├── aruba_ssh.py              # SSH executor ke controller
│   │   ├── aruba_rest_action.py      # REST-based config push
│   │   └── log_analyzer.py           # Log parsing tool untuk Hermes
│   └── prompts/
│       ├── system_prompt.txt         # System persona Hermes untuk wireless
│       └── remediation_template.txt  # Template prompt aksi remediation
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔧 Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **Docker** & **Docker Compose**
- **Aruba Wireless Controller** dengan REST API aktif (ArubaOS 8.x / AOS 10.x)
- **Hermes Agent** (self-hosted, dengan OpenRouter atau Ollama sebagai LLM backend)
- Network access dari server ini ke Management IP Aruba Controller

---

## ⚙️ Konfigurasi

### 1. Clone Repository

```bash
git clone https://github.com/your-org/aruba-wireless-ai-analyzer.git
cd aruba-wireless-ai-analyzer
```

### 2. Setup Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# === Aruba Controller ===
ARUBA_CONTROLLER_HOST=192.168.1.1
ARUBA_CONTROLLER_PORT=4343
ARUBA_USERNAME=admin
ARUBA_PASSWORD=your_password
ARUBA_API_VERSION=v1          # v1 (ArubaOS 8.x) atau v8 (AOS 10.x)
ARUBA_VERIFY_SSL=false        # Set true jika pakai cert resmi

# === Hermes AI Agent ===
HERMES_AGENT_URL=http://localhost:8080
HERMES_API_KEY=your_hermes_key

# === LLM Backend (via Hermes) ===
# Pilih salah satu: openrouter / ollama
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-xxxxx
OPENROUTER_MODEL=mistralai/mistral-7b-instruct

# Atau untuk lokal:
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=qwen2.5:7b

# === App Config ===
POLL_INTERVAL_SECONDS=30
ALERT_RSSI_THRESHOLD=-75
ALERT_CHANNEL_UTIL_THRESHOLD=80
LOG_LEVEL=INFO
```

### 3. Aktifkan REST API di Aruba Controller

Masuk ke controller via CLI atau Web UI, pastikan REST API aktif:

```
(Aruba-Controller) # configure terminal
(Aruba-Controller)(config) # web-server profile default
(Aruba-Controller)(Web Server Profile "default") # cipher-suite TLS_RSA_WITH_AES_256_CBC_SHA256
(Aruba-Controller)(Web Server Profile "default") # end
(Aruba-Controller) # write memory
```

Test koneksi:

```bash
curl -k -X POST https://<CONTROLLER_IP>:4343/v1/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

Response yang valid:
```json
{ "status": "OK", "status_str": "Login successful", "sid": "abc123..." }
```

---

## 🚀 Instalasi & Menjalankan

### Menggunakan Docker Compose (Recommended)

```bash
docker-compose up -d
```

Akses aplikasi:
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs

### Manual (Development Mode)

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

---

## 🖥️ Alur Penggunaan Aplikasi

### 1. Dashboard Utama

Saat pertama dibuka, dashboard langsung polling data dari controller:

- **AP Health Grid** — status setiap AP (online/offline, client count, channel util)
- **Client Table** — semua wireless client dengan kolom: MAC, SSID, AP, RSSI, SNR, Tx Rate, status
- **Active Alerts** — issue yang terdeteksi otomatis (merah = critical, kuning = warning)

### 2. Analisis Visual

Klik client atau AP untuk membuka panel drill-down dengan:

```
┌─────────────────────────────────────────────────────┐
│  📈 RSSI Trend (last 1 hour)                        │
│  ─────────────────────────────────────────────────  │
│   -40 ┤                                             │
│   -55 ┤   ████                                      │
│   -70 ┤         ████████████████                    │
│   -85 ┤                         ████ ← threshold    │
│       └─────────────────────────────────────────────│
│          10:00   10:15   10:30   10:45   11:00      │
├─────────────────────────────────────────────────────┤
│  📊 Channel Utilization Heatmap (per AP per Band)   │
│  📡 Roaming History Timeline                        │
│  🔢 Retry Rate & Error Statistics                   │
└─────────────────────────────────────────────────────┘
```

### 3. AI Diagnosis (Hermes)

Panel **"AI Insight"** muncul otomatis ketika issue terdeteksi. Hermes melakukan:

1. **Data Collection** — Ambil semua metric relevan dari controller
2. **Root Cause Analysis** — Identifikasi penyebab: interference, coverage hole, auth issue, dll
3. **Impact Assessment** — Berapa banyak client yang affected
4. **Recommendation** — Langkah spesifik untuk fix

Contoh output Hermes:

```
🔍 Diagnosis:
Client 00:11:22:33:44:55 mengalami roaming loop antara AP-3F-01 dan AP-3F-02.
RSSI di kedua AP berada di rentang -72 sampai -78 dBm, menyebabkan client
terus-menerus reassociate karena threshold steering terlalu sensitif.

📋 Root Cause:
- Band steering aggressiveness terlalu tinggi (nilai: 5)
- Client sticky di 5GHz padahal RSSI tidak adequate
- Tidak ada 802.11r Fast Transition aktif di SSID "CorpWiFi"

💡 Rekomendasi:
1. Turunkan band steering aggressiveness ke 3 di AP cluster ini
2. Aktifkan 802.11r pada SSID CorpWiFi untuk seamless roaming
3. Pertimbangkan tambah coverage di koridor lantai 3
```

### 4. One-Click Resolve

Tombol **"Resolve"** akan menampilkan preview aksi sebelum dieksekusi:

```
┌─────────────────────────────────────────────────────────┐
│  ⚡ AI Remediation Plan                                 │
│                                                         │
│  Target: AP-3F-01, AP-3F-02 | SSID: CorpWiFi           │
│                                                         │
│  Actions yang akan dieksekusi:                          │
│  [ ] rf dot11a-radio band-steering aggressiveness 3     │
│  [ ] wlan ssid-profile CorpWiFi                         │
│      opmode wpa3-aes-ccm-128                            │
│      dot11r                                             │
│                                                         │
│  [ Confirm & Execute ]     [ Cancel ]                   │
└─────────────────────────────────────────────────────────┘
```

Setelah konfirmasi, Hermes Agent:

1. Login ke controller via REST API / SSH
2. Eksekusi perintah konfigurasi
3. Verifikasi hasil (`show ap bss-table`, `show station`, dll)
4. Catat semua aksi ke **Audit Log**

---

## 🧠 Konfigurasi Hermes Agent

File `hermes/agent_config.yaml`:

```yaml
agent:
  name: "Aruba Wireless Engineer"
  system_prompt_file: prompts/system_prompt.txt

tools:
  - name: aruba_rest_action
    description: "Execute configuration commands to Aruba controller via REST API"
    module: tools.aruba_rest_action

  - name: aruba_ssh_command
    description: "Run show/debug commands on Aruba controller via SSH"
    module: tools.aruba_ssh

  - name: analyze_event_log
    description: "Parse and analyze Aruba controller event log for anomalies"
    module: tools.log_analyzer

  - name: get_client_details
    description: "Fetch detailed client stats from controller for diagnosis"
    module: tools.aruba_rest_action

llm:
  provider: openrouter       # atau ollama
  model: mistralai/mistral-7b-instruct
  temperature: 0.2           # Rendah untuk output teknis yang konsisten
  max_tokens: 2048
```

---

## 📊 Tipe Masalah yang Dapat Dideteksi & Di-resolve

| Issue Type | Deteksi | Visual | AI Resolve |
|------------|---------|--------|------------|
| Low RSSI / Coverage Hole | ✅ | RSSI Chart | Tx Power adjustment |
| Roaming Loop | ✅ | Roaming Timeline | Band steering tuning |
| High Channel Utilization | ✅ | Heatmap | Channel reassignment |
| Authentication Failure | ✅ | Event Log Panel | RADIUS / PSK check |
| IP Conflict / DHCP Issue | ✅ | Alert Panel | DHCP pool investigation |
| Deauth Storm | ✅ | Event Spike Chart | Client blacklist / rate limit |
| AP Down / Offline | ✅ | AP Grid (merah) | Reboot via controller |
| Sticky Client | ✅ | RSSI + Roaming | 802.11v BSS Transition push |

---

## 🔐 Keamanan

- Semua credential Aruba Controller disimpan di `.env` dan **tidak pernah** di-commit ke repo
- Hermes Agent berkomunikasi dengan controller di jaringan internal/management VLAN
- HTTPS mandatory untuk koneksi ke controller (skip verify SSL hanya untuk lab)
- Audit log menyimpan username, timestamp, dan exact command yang dieksekusi
- Tambahkan dedicated read-write API user di controller khusus untuk aplikasi ini:

```
(Aruba-Controller)(config) # mgmt-user api-user password <password> role network-admin
```

---

## 🐳 Docker Compose Reference

```yaml
# docker-compose.yml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  hermes:
    image: hermes-agent:latest   # Sesuaikan dengan image Hermes lo
    ports:
      - "8080:8080"
    env_file: .env
    volumes:
      - ./hermes:/config
    restart: unless-stopped
```

---

## 📡 Aruba API Endpoints yang Digunakan

| Data | Method | Endpoint |
|------|--------|----------|
| Login / Get Token | POST | `/v1/api/login` |
| Client Stats | GET | `/v1/monitoring/clients` |
| AP Summary | GET | `/v1/monitoring/aps` |
| RF Stats | GET | `/v1/monitoring/ap_rf_summary` |
| Event Log | GET | `/v1/monitoring/events` |
| Push Config | POST | `/v1/configuration/object/wlan_ssid_profile` |
| AP Reboot | POST | `/v1/tools/ap_reboot` |

> Dokumentasi lengkap: [Aruba Developer Hub](https://developer.arubanetworks.com/)

---

## 🛠️ Troubleshooting

**Gagal konek ke controller:**
```
ConnectionError: Cannot reach 192.168.1.1:4343
```
→ Pastikan management IP reachable dari host ini. Cek firewall dan port 4343/TCP.

**Hermes tidak generate response:**
```
HermesAgentError: LLM timeout after 30s
```
→ Cek `OPENROUTER_API_KEY` valid atau Ollama berjalan dengan model yang benar.
→ Untuk Ollama: `ollama run qwen2.5:7b` dan pastikan model sudah didownload.

**Data tidak update / stale:**
→ Cek nilai `POLL_INTERVAL_SECONDS` di `.env`.
→ Lihat log backend: `docker-compose logs -f backend`

**Resolve button tidak eksekusi:**
→ Pastikan user Aruba API punya role `network-admin`.
→ Cek koneksi Hermes Agent: `curl http://localhost:8080/health`

---

## 🗺️ Roadmap

- [ ] Support multi-controller (cluster / mobility master)
- [ ] Integrasi Syslog/SNMP Trap untuk alert real-time
- [ ] Export laporan PDF per-AP atau per-SSID
- [ ] Notifikasi Telegram/Slack saat AI mendeteksi issue kritis
- [ ] History comparison: before vs after remediation metrics
- [ ] Support ArubaOS Instant (IAP) di samping controller-based

---

## 🤝 Kontribusi

Pull request dan issue sangat welcome. Untuk perubahan besar, buka issue dulu untuk diskusi sebelum mulai coding.

---

## 📄 Lisensi

MIT License — bebas dipakai dan dimodifikasi untuk kebutuhan internal maupun komersial.
