#include <WiFi.h>
#include <WebServer.h>
#include <WiFiManager.h>

#define LED_AZUL 2

#define MOTOR_LEFT  26
#define MOTOR_RIGHT 27

WebServer server(80);

unsigned long leftMotorUntil = 0;
unsigned long rightMotorUntil = 0;

void ligarMotorEsquerdo(unsigned long tempoMs) {
  digitalWrite(MOTOR_LEFT, HIGH);
  leftMotorUntil = millis() + tempoMs;
}

void ligarMotorDireito(unsigned long tempoMs) {
  digitalWrite(MOTOR_RIGHT, HIGH);
  rightMotorUntil = millis() + tempoMs;
}

void controlarMotores() {
  unsigned long agora = millis();

  if (leftMotorUntil > 0 && agora >= leftMotorUntil) {
    digitalWrite(MOTOR_LEFT, LOW);
    leftMotorUntil = 0;
  }

  if (rightMotorUntil > 0 && agora >= rightMotorUntil) {
    digitalWrite(MOTOR_RIGHT, LOW);
    rightMotorUntil = 0;
  }
}

void atualizarLedWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(LED_AZUL, HIGH);
  } else {
    digitalWrite(LED_AZUL, LOW);
  }
}

unsigned long pegarTempoDaUrl(String uri, String prefixo) {
  String tempoStr = uri.substring(prefixo.length());
  return tempoStr.toInt();
}

void setup() {
  Serial.begin(115200);

  pinMode(LED_AZUL, OUTPUT);
  pinMode(MOTOR_LEFT, OUTPUT);
  pinMode(MOTOR_RIGHT, OUTPUT);

  digitalWrite(LED_AZUL, LOW);
  digitalWrite(MOTOR_LEFT, LOW);
  digitalWrite(MOTOR_RIGHT, LOW);

  WiFiManager wm;

  bool conectado = wm.autoConnect("ESP32-Motores");

  if (!conectado) {
    Serial.println("Falha ao conectar no WiFi");
    digitalWrite(LED_AZUL, LOW);
  } else {
    Serial.println("WiFi conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    digitalWrite(LED_AZUL, HIGH);
  }

  server.on("/health", HTTP_GET, []() {
    server.send(200, "text/plain", "status ok");
  });

  server.onNotFound([]() {
    String uri = server.uri();

    if (uri.startsWith("/left/")) {
      unsigned long tempo = pegarTempoDaUrl(uri, "/left/");
      ligarMotorEsquerdo(tempo);
      server.send(200, "text/plain", "motor esquerdo ligado por " + String(tempo) + " ms");
      return;
    }

    if (uri.startsWith("/right/")) {
      unsigned long tempo = pegarTempoDaUrl(uri, "/right/");
      ligarMotorDireito(tempo);
      server.send(200, "text/plain", "motor direito ligado por " + String(tempo) + " ms");
      return;
    }

    if (uri.startsWith("/front/")) {
      unsigned long tempo = pegarTempoDaUrl(uri, "/front/");
      ligarMotorEsquerdo(tempo);
      ligarMotorDireito(tempo);
      server.send(200, "text/plain", "motores ligados por " + String(tempo) + " ms");
      return;
    }

    server.send(404, "text/plain", "rota nao encontrada");
  });

  server.begin();
  Serial.println("Servidor HTTP iniciado");
}

void loop() {
  server.handleClient();

  atualizarLedWiFi();
  controlarMotores();
}
