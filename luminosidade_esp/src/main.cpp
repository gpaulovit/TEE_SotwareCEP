#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <SPIFFS.h>

// ---------- CONFIG Wi-Fi ----------
const char* SSID = "ESP32-LUZ";
const char* PASS = "12345678";

// ---------- PINO DO SENSOR ----------
const int LDR_PIN = 34; 

WebServer server(80);

// HIGH = ESCURO, LOW = CLARO no seu módulo
String gerarJsonEstado() {
  int v = digitalRead(LDR_PIN);

  String nivel   = (v == HIGH) ? "baixa" : "alta";   
  String estado  = (v == HIGH) ? "Ambiente escuro" : "Ambiente bem iluminado";

  String json = "{";
  json += "\"nivel\":\"" + nivel + "\",";
  json += "\"descricao\":\"" + estado + "\",";
  json += "\"raw\":" + String(v);
  json += "}";

  return json;
}

void handleIndex() {
  File file = SPIFFS.open("/index.html", "r");
  if (!file) {
    server.send(500, "text/plain", "Erro ao abrir index.html");
    return;
  }
  server.streamFile(file, "text/html");
  file.close();
}

void handleEstado() {
  String json = gerarJsonEstado();
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  pinMode(LDR_PIN, INPUT);

  // Inicia SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("Falha ao montar SPIFFS");
    return;
  }

  // Inicia AP
  WiFi.mode(WIFI_AP);
  WiFi.softAP(SSID, PASS);

  Serial.println("Wi-Fi iniciado!");
  Serial.print("SSID: ");
  Serial.println(SSID);
  Serial.print("Acesse: http://");
  Serial.println(WiFi.softAPIP());

  // Rotas
  server.on("/", handleIndex);
  server.on("/estado", handleEstado);

  server.begin();
  Serial.println("Servidor HTTP iniciado.");
}

void loop() {
  server.handleClient();
}
