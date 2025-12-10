#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <WebServer.h>

const char* ssid     = "NOME_DO_SEU_CELULAR"; 
const char* password = "SENHA_DO_SEU_CELULAR"; 

const unsigned long INTERVALO_LEITURA = 2000; // 2 segundos
WebServer server(80);

// ================= SIMULAÇÃO (MOCK) =================
const float MOCK_DB_DATA[] = {
  35.5, 36.0, 35.8, 38.2, 40.1, 42.5, 45.0, 65.2, 68.5, 66.0, 
  45.0, 42.1, 38.5, 36.2, 35.0, 85.5, 88.2, 90.1, 36.0, 35.5
};
const int DATASET_SIZE = sizeof(MOCK_DB_DATA) / sizeof(MOCK_DB_DATA[0]);
int mockIndex = 0;
float ultimoValorLido = 0.0;
unsigned long lastTime = 0;

const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ESP32 - Monitor CEP</title>
<style>
  body{background:#0f172a;color:#e2e8f0;margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:Arial,sans-serif;}
  .card{background:#1e293b;padding:20px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.5);width:100%;max-width:600px;}
  h1{margin:0 0 5px 0;font-size:1.4rem;color:#38bdf8;}
  .grid-kpi { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }
  .box { background:#0f172a; border:1px solid #334155; padding:10px; border-radius:8px; font-size:0.85rem; }
  .metric-value{font-size:2rem;font-weight:bold;color:#f8fafc;}
  .tag{font-size:0.7rem;padding:3px 8px;border-radius:12px;font-weight:bold;text-transform:uppercase;}
  .ok{background:#064e3b;color:#6ee7b7;} .warn{background:#450a0a;color:#fca5a5;}
  button{margin-top:10px;width:100%;padding:12px;border:none;border-radius:6px;font-weight:bold;cursor:pointer;transition:0.2s;}
  .btn-primary{background:#38bdf8;color:#0f172a;} .btn-sec{background:#334155;color:#e2e8f0;}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
<div class="card">
  <h1>ESP32 - Monitor CEP</h1>
  <div class="grid-kpi">
    <div class="box"><div>Nível Atual</div><div class="metric-value" id="tempDisplay">-- dB</div><span id="statusTag" class="tag ok">Aguardando</span></div>
    <div class="box"><div>Status CEP</div><div style="font-weight:bold; margin-top:5px;" id="kpiStatus">--</div><div>Cpk: <span id="kpiCpk">--</span></div></div>
  </div>
  <div class="box">
    <b>Controle Estatístico:</b><br>
    Média: <b id="valMedia">--</b> | UCL: <b id="valUCL" style="color:#ef4444">--</b> | LCL: <b id="valLCL" style="color:#ef4444">--</b>
  </div>
  <div style="margin-top:15px"><canvas id="chartX" height="180"></canvas></div>
  <button id="btnToggleColeta" class="btn-primary" onclick="toggleColeta()">Iniciar Coleta</button>
</div>

<script>
// === CONFIGURAÇÕES DO CEP (Front-end) ===
const MAX_AMOSTRAS = 60; 
const ESPEC_MIN = 30.0; 
const ESPEC_MAX = 80.0; 

let dados = { temps: [], mrs: [], labels: [], contador: 0 };
let limites = { media: 0, ucl: 0, lcl: 0, sigma: 0 };
let coletaAtiva = false; 
let timer = null; 
let chartX;

function initChart(){
  const ctx = document.getElementById('chartX').getContext('2d');
  chartX = new Chart(ctx, { type:'line', data:{labels:[], datasets:[
    {label:'dB', data:[], borderColor:'#38bdf8', tension:0.1},
    {label:'Média', data:[], borderColor:'#94a3b8', borderDash:[5,5], pointRadius:0},
    {label:'UCL', data:[], borderColor:'#ef4444', borderDash:[2,2], pointRadius:0},
    {label:'LCL', data:[], borderColor:'#ef4444', borderDash:[2,2], pointRadius:0}
  ]}, options:{animation:false, responsive:true, plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{grid:{color:'#334155'}}}}});
}

function calcStats(arrT, arrM) {
  if (arrT.length < 2) return null;
  const med = arrT.reduce((a,b)=>a+b,0)/arrT.length;
  const mrMed = arrM.reduce((a,b)=>a+b,0)/arrM.length;
  const sig = mrMed / 1.128; 
  return { media: med, sigma: sig };
}

function processar(val) {
  // Adiciona ao buffer
  dados.contador++; 
  dados.temps.push(val); 
  dados.labels.push(dados.contador);
  
  // Calcula Amplitude Móvel (MR)
  if (dados.temps.length > 1) {
    const mr = Math.abs(val - dados.temps[dados.temps.length-2]);
    dados.mrs.push(mr);
  }
  
  // Mantém tamanho fixo (Janela Deslizante)
  if (dados.temps.length > MAX_AMOSTRAS) { 
    dados.temps.shift(); 
    dados.labels.shift(); 
    if(dados.mrs.length > 0) dados.mrs.shift(); 
  }
  
  // Calcula CEP
  const st = calcStats(dados.temps, dados.mrs);
  if (st) {
     limites.media = st.media; 
     limites.sigma = st.sigma; 
     limites.ucl = st.media + 3*st.sigma; 
     limites.lcl = st.media - 3*st.sigma; 
  }
  ui(val);
}

function ui(val) {
  document.getElementById("tempDisplay").textContent = val.toFixed(1) + " dB";
  const tag = document.getElementById("statusTag");
  
  // Verifica Especificação do Cliente
  if(val < ESPEC_MIN || val > ESPEC_MAX){ 
      tag.textContent="FORA ESPECIFICAÇÃO"; tag.className="tag warn"; 
  } else { 
      tag.textContent="DENTRO ESPECIFICAÇÃO"; tag.className="tag ok"; 
  }

  if(dados.temps.length > 1){
    document.getElementById("valMedia").textContent = limites.media.toFixed(1);
    document.getElementById("valUCL").textContent = limites.ucl.toFixed(1);
    document.getElementById("valLCL").textContent = limites.lcl.toFixed(1);
    
    // Verifica Causa Especial (Regra 1: Ponto fora dos limites de controle)
    const fora = val > limites.ucl || val < limites.lcl;
    const kpi = document.getElementById("kpiStatus");
    if(fora){ kpi.textContent="⚠ CAUSA ESPECIAL"; kpi.style.color="#ef4444"; }
    else{ kpi.textContent="Processo Estável"; kpi.style.color="#6ee7b7"; }
    
    // Calcula Cpk
    if(limites.sigma > 0){
      const cpk = Math.min((ESPEC_MAX-limites.media)/(3*limites.sigma), (limites.media-ESPEC_MIN)/(3*limites.sigma));
      document.getElementById("kpiCpk").textContent = cpk.toFixed(2);
    }
  }
  updChart();
}

function updChart(){
  if(!chartX) return;
  const len = dados.temps.length;
  chartX.data.labels = dados.labels;
  chartX.data.datasets[0].data = dados.temps;
  // Desenha as linhas de controle dinâmicas
  chartX.data.datasets[1].data = Array(len).fill(limites.media);
  chartX.data.datasets[2].data = Array(len).fill(limites.ucl);
  chartX.data.datasets[3].data = Array(len).fill(limites.lcl);
  chartX.update();
}

function toggleColeta() {
  const btn = document.getElementById("btnToggleColeta");
  if(coletaAtiva){ 
    clearInterval(timer); 
    coletaAtiva=false; 
    btn.textContent="Iniciar Coleta"; 
    btn.className="btn-primary"; 
  } else { 
    if(!chartX) initChart();
    timer=setInterval(fetchData, 1000); // Pede dados a cada 1s
    coletaAtiva=true; 
    btn.textContent="Parar Coleta"; 
    btn.className="btn-sec"; 
  }
}

async function fetchData(){
  try {
    const r = await fetch("/dados");
    const d = await r.json();
    processar(d.valor);
  } catch(e) { console.log(e); }
}

// Inicializa o gráfico vazio ao carregar
window.onload = initChart;
</script>
</body></html>
)rawliteral";

float lerSensorMock();
void handleRoot();
void handleData();

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.print("Conectando ao Hotspot: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi Conectado!");
  Serial.print("IP para ngrok: http://");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/dados", handleData);
  server.begin();
}

void loop() {
  server.handleClient();
  if (millis() - lastTime >= INTERVALO_LEITURA) {
    lastTime = millis();
    ultimoValorLido = lerSensorMock();
  }
}

float lerSensorMock() {
  float valor = MOCK_DB_DATA[mockIndex];
  mockIndex++;
  if (mockIndex >= DATASET_SIZE) mockIndex = 0;
  return valor;
}

void handleRoot() { server.send(200, "text/html", index_html); }
void handleData() {
  JsonDocument doc;
  doc["valor"] = ultimoValorLido;
  String json;
  serializeJson(doc, json);
  server.send(200, "application/json", json);
}