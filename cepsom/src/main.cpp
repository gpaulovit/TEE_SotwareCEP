#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <WebServer.h>


const char* ssid     = "PEUGEOT 206"; 
const char* password = "password"; 

const unsigned long INTERVALO_LEITURA = 1500; 
WebServer server(80);

const float MOCK_DB_DATA[] = {
  // Estável 
  35.5, 36.0, 35.8, 38.2, 40.1, 42.5, 45.0, 41.2, 39.5, 38.0,
  // Desvio Moderado (Amarelo)
  55.0, 58.0, 59.5, 57.0, 
  // Erro Crítico (Vermelho)
  85.5, 90.2, 
  // Volta ao normal
  40.0, 38.5, 36.2, 35.0
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
<title>ESP32 - CEP Avançado</title>
<style>
  body{background:#0f172a;color:#e2e8f0;margin:0;font-family:'Segoe UI',Arial,sans-serif;display:flex;justify-content:center;padding:20px;}
  .container{width:100%;max-width:800px;display:grid;gap:15px;}
  .card{background:#1e293b;padding:20px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.4);border:1px solid #334155;}
  h1{margin:0 0 10px 0;font-size:1.5rem;color:#38bdf8;text-align:center;}
  h2{font-size:1rem;color:#94a3b8;margin-bottom:10px;border-bottom:1px solid #334155;padding-bottom:5px;}
  

  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
  
  .kpi-box { background:#0f172a; padding:10px; border-radius:8px; text-align:center; border:1px solid #334155; }
  .val-big { font-size:1.8rem; font-weight:bold; display:block; margin:5px 0; }
  .lbl { font-size:0.75rem; color:#94a3b8; text-transform:uppercase; letter-spacing:1px; }

  .tag { padding:4px 8px; border-radius:4px; font-weight:bold; font-size:0.8rem; display:inline-block; width:100%; box-sizing:border-box;}
  .bg-green { background:#064e3b; color:#6ee7b7; border:1px solid #059669; }
  .bg-yellow { background:#713f12; color:#fde047; border:1px solid #eab308; } /* SINAL AMARELO */
  .bg-red { background:#450a0a; color:#fca5a5; border:1px solid #ef4444; }   /* SINAL VERMELHO */


  input[type=number] { background:#020617; border:1px solid #475569; color:white; padding:8px; border-radius:4px; width:80px; text-align:center; }
  
  button{width:100%;padding:12px;border:none;border-radius:6px;font-weight:bold;cursor:pointer;margin-top:10px;}
  .btn-start{background:#38bdf8;color:#0f172a;} 
  .btn-stop{background:#334155;color:#e2e8f0;}

  table { width:100%; border-collapse:collapse; font-size:0.9rem; }
  td { padding:5px; border-bottom:1px solid #334155; }
  .num { text-align:right; font-family:monospace; color:#cbd5e1; }
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>

<div class="container">
  
  <div class="card">
    <h1>MONITORAMENTO DE PROCESSO</h1>
    <div class="grid-2">
      <div class="kpi-box">
        <span class="lbl">Leitura Atual</span>
        <span class="val-big" id="dispValor">--</span>
        <div id="tagSpec" class="tag bg-green">Aguardando...</div>
      </div>
      <div class="kpi-box">
        <span class="lbl">Controle Estatístico</span>
        <span class="val-big" style="font-size:1.2rem; margin-top:15px;" id="dispTipo">--</span>
        <div id="tagControl" class="tag bg-green">--</div>
      </div>
    </div>
  </div>

  <div class="card">
    <canvas id="chartX" height="200"></canvas>
  </div>

  <div class="card">
    <h2>PREVISÃO DE PRODUÇÃO (Arranjos)</h2>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
      <span>Tamanho do Lote de Produção:</span>
      <input type="number" id="inputLote" value="1000" onchange="calcProduction()">
    </div>
    
    <div class="grid-3">
      <div class="kpi-box">
        <span class="lbl">Probab. Defeito</span>
        <span class="val-big" id="probDefeito" style="color:#fca5a5">--%</span>
      </div>
      <div class="kpi-box">
        <span class="lbl">Peças Boas (Est.)</span>
        <span class="val-big" id="estBoas" style="color:#6ee7b7">--</span>
      </div>
      <div class="kpi-box">
        <span class="lbl">Sucata (Est.)</span>
        <span class="val-big" id="estRuins" style="color:#ef4444">--</span>
      </div>
    </div>
    
    <div style="margin-top:15px; font-size:0.85rem; color:#94a3b8;">
      <table>
        <tr><td>Média ($\bar{X}$):</td><td class="num" id="statMedia">--</td></tr>
        <tr><td>Desvio Padrão ($\hat{\sigma}$):</td><td class="num" id="statSigma">--</td></tr>
        <tr><td>Capabilidade (Cpk):</td><td class="num" id="statCpk">--</td></tr>
      </table>
    </div>
  </div>

  <button id="btnColeta" class="btn-start" onclick="toggleColeta()">INICIAR COLETA</button>
</div>

<script>
const MAX_BUFFER = 60;
const ESPEC_MIN = 30.0;
const ESPEC_MAX = 80.0;


let dados = { temps: [], mrs: [], labels: [], n: 0 };
let stats = { media: 0, sigma: 0, ucl: 0, lcl: 0, uwl: 0, lwl: 0 }; 
let ativo = false;
let timer = null;
let chart;


let probabilidadeExata = 0.0;


function normalCDF(x, mean, sigma) {
    if (sigma === 0) return x > mean ? 1 : 0;
    var z = (x - mean) / Math.sqrt(2 * sigma * sigma);
    var t = 1 / (1 + 0.3275911 * Math.abs(z));
    var erf = 1 - (((((1.061405429 * t + -1.453152027) * t) + 1.421413741) * t + -0.284496736) * t + 0.254829592) * t * Math.exp(-z * z);
    var sign = z < 0 ? -1 : 1;
    return 0.5 * (1 + sign * erf);
}

function calcStats(vals, mrs) {
  if (vals.length < 2) return;
  
  const media = vals.reduce((a,b)=>a+b,0) / vals.length;
  const mrMedia = mrs.reduce((a,b)=>a+b,0) / mrs.length;
  const sigma = mrMedia / 1.128;

  stats.media = media;
  stats.sigma = sigma;


  stats.ucl = media + (3 * sigma);
  stats.lcl = media - (3 * sigma);

  stats.uwl = media + (2 * sigma);
  stats.lwl = media - (2 * sigma);
}

function calcProbabilities() {
  if (stats.sigma === 0) return;

  const pAbaixo = normalCDF(ESPEC_MIN, stats.media, stats.sigma); 
  const pAcima  = 1.0 - normalCDF(ESPEC_MAX, stats.media, stats.sigma);
  
  probabilidadeExata = pAbaixo + pAcima;
  
  let texto = (probabilidadeExata * 100).toFixed(2);
  // Se houver probabilidade ínfima, mostra <0.01 em vez de 0.00
  if(probabilidadeExata > 0 && texto === "0.00") texto = "< 0.01"; 
  
  document.getElementById("probDefeito").textContent = texto + "%";
  
  calcProduction();
}

function calcProduction() {
  const pDefeito = probabilidadeExata;

  const lote = parseInt(document.getElementById("inputLote").value);
  
  const ruins = Math.round(lote * pDefeito); 
  const boas = lote - ruins;

  document.getElementById("estBoas").textContent = boas;
  document.getElementById("estRuins").textContent = ruins;
}

function processar(val) {
  dados.n++;
  dados.temps.push(val);
  dados.labels.push(dados.n);
  
  if (dados.temps.length > 1) {
    dados.mrs.push(Math.abs(val - dados.temps[dados.temps.length-2]));
  }
  
  if (dados.temps.length > MAX_BUFFER) {
    dados.temps.shift(); dados.labels.shift(); 
    if(dados.mrs.length) dados.mrs.shift();
  }

  calcStats(dados.temps, dados.mrs);
  calcProbabilities();
  atualizarUI(val);
}

function atualizarUI(val) {
  // Tags e Valores
  document.getElementById("dispValor").textContent = val.toFixed(1) + " dB";
  
  const tagSpec = document.getElementById("tagSpec");
  if (val < ESPEC_MIN || val > ESPEC_MAX) {
      tagSpec.textContent = "FORA DA ESPECIFICAÇÃO";
      tagSpec.className = "tag bg-red";
  } else {
      tagSpec.textContent = "DENTRO DA ESPECIFICAÇÃO";
      tagSpec.className = "tag bg-green";
  }

  const tagControl = document.getElementById("tagControl");
  const distMedia = Math.abs(val - stats.media);

  if (distMedia > (3 * stats.sigma)) {
      tagControl.textContent = "⚠ CAUSA ESPECIAL (CRÍTICO)";
      tagControl.className = "tag bg-red";
  } else if (distMedia > (2 * stats.sigma)) {
      tagControl.textContent = "⚠ ADVERTÊNCIA (2 SIGMA)";
      tagControl.className = "tag bg-yellow";
  } else {
      tagControl.textContent = "PROCESSO ESTÁVEL";
      tagControl.className = "tag bg-green";
  }

  document.getElementById("statMedia").textContent = stats.media.toFixed(2);
  document.getElementById("statSigma").textContent = stats.sigma.toFixed(3);
  
  if (stats.sigma > 0) {
      const cpk = Math.min((ESPEC_MAX - stats.media)/(3*stats.sigma), (stats.media - ESPEC_MIN)/(3*stats.sigma));
      document.getElementById("statCpk").textContent = cpk.toFixed(2);
  }

  updateChart();
}

function initChart() {
  const ctx = document.getElementById('chartX').getContext('2d');
  chart = new Chart(ctx, {
    type: 'line',
    data: { 
      labels: [], 
      datasets: [
        { label: 'Leitura', data: [], borderColor: '#38bdf8', borderWidth:2, pointRadius:2, order: 1 },
        { label: 'UCL (3s)', data: [], borderColor: '#ef4444', borderDash:[5,5], pointRadius:0, borderWidth:1, order: 2 },
        { label: 'LCL (3s)', data: [], borderColor: '#ef4444', borderDash:[5,5], pointRadius:0, borderWidth:1, order: 3 },
        // [CORREÇÃO 3] Adicionando linhas de advertência (amarelas)
        { label: 'UWL (2s)', data: [], borderColor: '#eab308', borderDash:[2,2], pointRadius:0, borderWidth:1, order: 4 },
        { label: 'LWL (2s)', data: [], borderColor: '#eab308', borderDash:[2,2], pointRadius:0, borderWidth:1, order: 5 },
        { label: 'Média', data: [], borderColor: '#94a3b8', pointRadius:0, borderWidth:1, order: 6 }
      ]
    },
    options: { 
      animation: false, 
      responsive: true, 
      plugins: { legend: { display: true, labels: { color: '#94a3b8', boxWidth: 10 } } }, // Habilitei a legenda para verem o que é linha amarela
      scales: { x: { display: false }, y: { grid: { color: '#334155' } } } 
    }
  });
}

function updateChart() {
  if (!chart) return;
  const len = dados.temps.length;
  chart.data.labels = dados.labels;
  
  // Atualiza dados
  chart.data.datasets[0].data = dados.temps; // Leitura
  chart.data.datasets[1].data = Array(len).fill(stats.ucl); // Vermelho Sup
  chart.data.datasets[2].data = Array(len).fill(stats.lcl); // Vermelho Inf
  
  chart.data.datasets[3].data = Array(len).fill(stats.uwl); // Amarelo Sup
  chart.data.datasets[4].data = Array(len).fill(stats.lwl); // Amarelo Inf
  
  chart.data.datasets[5].data = Array(len).fill(stats.media); // Média
  
  chart.update();
}

function toggleColeta() {
  const btn = document.getElementById("btnColeta");
  if (ativo) {
    clearInterval(timer);
    ativo = false;
    btn.textContent = "INICIAR COLETA";
    btn.className = "btn-start";
  } else {
    if(!chart) initChart();
    timer = setInterval(() => {
      fetch("/dados").then(r=>r.json()).then(d=>processar(d.valor));
    }, 1000);
    ativo = true;
    btn.textContent = "PARAR COLETA";
    btn.className = "btn-stop";
  }
}
</script>
</body>
</html>
)rawliteral";

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

void setup() {
  Serial.begin(115200);
  delay(1000);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nIP: " + WiFi.localIP().toString());
  
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