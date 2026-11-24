// Drives the real sketch with scripted time, pins and serial input. Commands on stdin:
//   ms N | rx PAYLOAD | raw LINE | seq N | in PIN VALUE | dump | tel
#include "Arduino.h"
#include <iostream>
#include <sstream>
unsigned long fake_us = 0;
int pin_out[80], pwm_out[80], pin_in[80];
SerialType Serial;
#include "../eve_controller/eve_controller.ino"

static std::string lastTel;
static uint16_t nextSeq = 0;
static void run(unsigned long ms) { for (unsigned long i = 0; i < ms * 4; i++) { fake_us += 250; loop(); } }
static void flush() {
  std::istringstream in(Serial.output); Serial.output.clear();
  std::string line;
  while (std::getline(in, line)) {
    size_t a = line.find(':', 3), b = line.rfind('*');
    if (a == std::string::npos || b == std::string::npos) continue;
    std::string payload = line.substr(a + 1, b - a - 1);
    if (payload.rfind("T,", 0) == 0) lastTel = payload; else printf("TX %s\n", payload.c_str());
  }
}
static void feed(const std::string& s) { for (char c : s) Serial.input.push_back(c); Serial.input.push_back('\n'); }
int main() {
  setup();
  std::string line;
  while (std::getline(std::cin, line)) {
    std::istringstream in(line); std::string cmd; in >> cmd;
    std::string rest; std::getline(in, rest); if (!rest.empty() && rest[0] == ' ') rest.erase(0, 1);
    if (cmd == "ms") run(strtoul(rest.c_str(), nullptr, 10));
    else if (cmd == "seq") nextSeq = (uint16_t)atoi(rest.c_str());
    else if (cmd == "rx") {
      nextSeq++;
      std::string body = "E1:" + std::to_string(nextSeq) + ":" + rest;
      char crc[8]; snprintf(crc, sizeof(crc), "*%04X", crc16((const uint8_t*)body.c_str(), body.size()));
      feed(body + crc); run(1);
    }
    else if (cmd == "raw") { feed(rest); run(1); }
    else if (cmd == "in") { int p, v; if (sscanf(rest.c_str(), "%d %d", &p, &v) == 2 && p >= 0 && p < 80) pin_in[p] = v; }
    else if (cmd == "dump") {
      printf("D pwm=%d,%d,%d,%d stby=%d,%d fwd=%d,%d,%d,%d rev=%d,%d,%d,%d coils=", pwm_out[L_PWMA], pwm_out[L_PWMB],
             pwm_out[R_PWMA], pwm_out[R_PWMB], pin_out[L_STBY], pin_out[R_STBY], pin_out[L_A1], pin_out[L_B1],
             pin_out[R_A1], pin_out[R_B1], pin_out[L_A2], pin_out[L_B2], pin_out[R_A2], pin_out[R_B2]);
      for (int i = 0; i < 4; i++) printf("%d", pin_out[PAN[i]]);
      for (int i = 0; i < 4; i++) printf("%d", pin_out[TILT[i]]);
      printf("\n");
    }
    else if (cmd == "tel") { flush(); printf("TEL %s\n", lastTel.c_str()); }
    flush();
  }
  return 0;
}
