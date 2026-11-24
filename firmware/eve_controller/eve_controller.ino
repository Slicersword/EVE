// EVE V3 - Arduino Mega 2560 actuator controller.
// Safety rules (see docs/adr/ADR-002-firmware-safety.md):
//  * Starts latched. Nothing moves until the Pi sends heartbeats and an accepted CLEAR.
//  * Lost heartbeat or any cliff channel at its edge level -> everything stops and latches.
//  * Drive and head each need their own fresh command (lease); a heartbeat alone never keeps them moving.
//  * DRIVE_ENABLED / HEAD_ENABLED false -> the outputs are never driven, whatever the Pi sends.
#include <Arduino.h>
#include <errno.h>
#include "eve_config.h"
#ifdef __AVR__
#include <avr/wdt.h>
#endif

static const unsigned long STEP_US = 1800, TELEM_MS = 100, COIL_HOLD_MS = 200;
static const uint8_t HALFSTEP[8][4] = {{1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},{0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}};

static char lineBuf[196];
static uint16_t lineLen = 0, lastSeq = 0;
static bool discarding = false, haveSeq = false, hbValid = false, latched = true;
static unsigned long lastHb = 0, lastDrive = 0, lastHead = 0, lastTelem = 0, lastStepUs = 0, lastRamp = 0;
static unsigned long reverseStart = 0, headIdleSince = 0;
static bool reversing = false, headHomed = false, coilsOn = false;
static long panPos = 0, tiltPos = 0, panTarget = 0, tiltTarget = 0;
static uint8_t panPhase = 0, tiltPhase = 0;
static int outL = 0, outR = 0, targetL = 0, targetR = 0;

static uint16_t crc16(const uint8_t* p, size_t n) {
  uint16_t c = 0xffff;
  while (n--) { c ^= (uint16_t)*p++ << 8; for (uint8_t i = 0; i < 8; i++) c = (c & 0x8000) ? (c << 1) ^ 0x1021 : c << 1; }
  return c;
}
static void tx(uint16_t seq, const char* payload) {
  char body[160], out[172];
  int n = snprintf(body, sizeof(body), "E1:%u:%s", (unsigned)seq, payload);
  if (n < 0 || n >= (int)sizeof(body)) return;
  snprintf(out, sizeof(out), "%s*%04X\n", body, crc16((const uint8_t*)body, (size_t)n));
  Serial.print(out);
}

// ---------------------------------------------------------------- drive
static void motorPins(uint8_t in1, uint8_t in2, uint8_t pwm, int v) {
  analogWrite(pwm, 0);                       // remove PWM before changing polarity
  digitalWrite(in1, v > 0 ? HIGH : LOW);
  digitalWrite(in2, v < 0 ? HIGH : LOW);
  analogWrite(pwm, abs(v));
}
static void writeDrive() {
  digitalWrite(L_STBY, outL ? HIGH : LOW);
  digitalWrite(R_STBY, outR ? HIGH : LOW);
  motorPins(L_A1, L_A2, L_PWMA, outL); motorPins(L_B1, L_B2, L_PWMB, outL);
  motorPins(R_A1, R_A2, R_PWMA, outR); motorPins(R_B1, R_B2, R_PWMB, outR);
}
static void stopDrive() { outL = outR = targetL = targetR = 0; reversing = false; writeDrive(); }
static bool driveMoving() { return outL || outR || targetL || targetR; }
static int toward(int v, int t, int step) { return v < t ? min(t, v + step) : max(t, v - step); }

// ---------------------------------------------------------------- head
static void releaseCoils() {
  for (uint8_t i = 0; i < 4; i++) { digitalWrite(PAN[i], LOW); digitalWrite(TILT[i], LOW); }
  coilsOn = false;
}
static void holdHead() { panTarget = panPos; tiltTarget = tiltPos; releaseCoils(); }
static bool headMoving() { return headHomed && (panPos != panTarget || tiltPos != tiltTarget); }
static void coils(const uint8_t p[4], uint8_t phase) {
  for (uint8_t i = 0; i < 4; i++) digitalWrite(p[i], HALFSTEP[phase & 7][i]);
  coilsOn = true;
}

// ---------------------------------------------------------------- safety
static void emergencyStop() { stopDrive(); holdHead(); headHomed = false; latched = true; }
static bool heartbeatOK() { return hbValid && (millis() - lastHb) <= HB_TIMEOUT_MS; }
static bool cliffSafe() {
  if (!CLIFF_CALIBRATED) return false;
  for (uint8_t i = 0; i < 3; i++) if (digitalRead(CLIFF[i]) == CLIFF_EDGE_LEVEL[i]) return false;
  return true;
}

static void driveTick() {
  if (!driveMoving()) return;
  if (!DRIVE_ENABLED || millis() - lastDrive > DRIVE_LEASE_MS) { stopDrive(); return; }
  unsigned long now = millis(), dt = now - lastRamp;
  if (dt < 10) return;
  lastRamp = now;
  if (reversing) { if (now - reverseStart < REVERSE_MS) return; reversing = false; }
  if ((outL && targetL && ((outL > 0) != (targetL > 0))) || (outR && targetR && ((outR > 0) != (targetR > 0)))) {
    outL = outR = 0; writeDrive(); reversing = true; reverseStart = now; return;
  }
  if (dt > 50) dt = 50;
  int step = (int)(((unsigned long)RAMP_PER_SECOND * dt) / 1000UL);
  if (step < 1) step = 1;
  outL = toward(outL, targetL, step); outR = toward(outR, targetR, step);
  writeDrive();
}
static void headTick() {
  if (!HEAD_ENABLED || !headHomed) { if (coilsOn) releaseCoils(); return; }
  if (!headMoving()) { if (coilsOn && millis() - headIdleSince > COIL_HOLD_MS) releaseCoils(); return; }
  if (millis() - lastHead > HEAD_LEASE_MS || driveMoving()) { holdHead(); return; }
  unsigned long u = micros();
  if (u - lastStepUs < STEP_US) return;
  lastStepUs = u;
  if (panPos != panTarget) { int d = panTarget > panPos ? 1 : -1; panPhase = (panPhase + d + 8) & 7; coils(PAN, panPhase); panPos += d; }
  else { int d = tiltTarget > tiltPos ? 1 : -1; tiltPhase = (tiltPhase + d + 8) & 7; coils(TILT, tiltPhase); tiltPos += d; }
  headIdleSince = millis();
}

// ---------------------------------------------------------------- commands
static bool parseLong(const char* s, long lo, long hi, long& value) {
  if (!s || !*s) return false;
  const char* q = s; if (*q == '-') q++;
  if (!*q || strlen(q) > 6) return false;
  while (*q) { if (*q < '0' || *q > '9') return false; q++; }
  long v = strtol(s, nullptr, 10);
  if (v < lo || v > hi) return false;
  value = v; return true;
}
static bool pairArgs(char* payload, const char* name, long loA, long hiA, long loB, long hiB, long& a, long& b) {
  size_t n = strlen(name);
  if (strncmp(payload, name, n) || payload[n] != ',') return false;
  char* comma = strchr(payload + n + 1, ',');
  if (!comma || strchr(comma + 1, ',')) return false;
  *comma = 0;
  bool ok = parseLong(payload + n + 1, loA, hiA, a) && parseLong(comma + 1, loB, hiB, b);
  *comma = ',';
  return ok;
}
static void command(char* payload, uint16_t seq) {
  if (!strcmp(payload, "HB")) { lastHb = millis(); hbValid = true; tx(seq, "ACK"); return; }
  if (!strcmp(payload, "STOP")) { emergencyStop(); tx(seq, "ACK"); return; }
  if (!strcmp(payload, "HEADSTOP")) { holdHead(); headHomed = false; tx(seq, "ACK"); return; }
  if (!strcmp(payload, "CLEAR")) {
    if (!heartbeatOK() || !cliffSafe()) { tx(seq, "ERR,UNSAFE"); return; }
    stopDrive(); holdHead(); latched = false; tx(seq, "ACK"); return;
  }
  if (!strcmp(payload, "HOMESET")) {
    if (!HEAD_ENABLED || latched || !heartbeatOK() || driveMoving() || coilsOn) { tx(seq, "ERR,UNSAFE"); return; }
    panPos = tiltPos = panTarget = tiltTarget = 0; headHomed = true; lastHead = millis(); tx(seq, "ACK"); return;
  }
  long a = 0, b = 0;
  if (pairArgs(payload, "DRIVE", -DRIVE_MAX, DRIVE_MAX, -DRIVE_MAX, DRIVE_MAX, a, b)) {
    if (a == 0 && b == 0) { stopDrive(); tx(seq, "ACK"); return; }
    if (!DRIVE_ENABLED || latched || !heartbeatOK() || !cliffSafe() || headMoving() || coilsOn) { tx(seq, "ERR,UNSAFE"); return; }
    if ((!REVERSE_ALLOWED && (a < 0 || b < 0)) || (!PIVOT_ALLOWED && ((a > 0) != (b > 0)))) { tx(seq, "ERR,RANGE"); return; }
    targetL = (int)a; targetR = (int)b; lastDrive = millis(); tx(seq, "ACK"); return;
  }
  if (pairArgs(payload, "HEAD", PAN_MIN, PAN_MAX, TILT_MIN, TILT_MAX, a, b)) {
    if (!HEAD_ENABLED || !headHomed || latched || !heartbeatOK() || !cliffSafe() || driveMoving()) { tx(seq, "ERR,UNSAFE"); return; }
    panTarget = a; tiltTarget = b; lastHead = millis(); tx(seq, "ACK"); return;
  }
  tx(seq, "ERR,CMD");
}
static void parseLine(char* s) {
  char* star = strrchr(s, '*');
  if (!star || strlen(star + 1) != 4) return;
  for (char* q = star + 1; *q; q++) if (!isxdigit(*q)) return;
  unsigned long want = strtoul(star + 1, nullptr, 16);
  *star = 0;
  if (crc16((const uint8_t*)s, strlen(s)) != want || strncmp(s, "E1:", 3)) return;
  char* colon = strchr(s + 3, ':');
  if (!colon) return;
  *colon = 0;
  long seqLong = 0;
  if (!parseLong(s + 3, 1, 65535, seqLong)) return;
  uint16_t seq = (uint16_t)seqLong;
  char* payload = colon + 1;
  if (!strcmp(payload, "SYNC")) {            // new session: stop everything, forget the old heartbeat
    emergencyStop(); hbValid = false; haveSeq = true; lastSeq = seq;
    char ack[40]; snprintf(ack, sizeof(ack), "ACK,%s", FIRMWARE_ID); tx(seq, ack); return;
  }
  if (!haveSeq || (int16_t)(seq - lastSeq) <= 0) return;   // replayed or out-of-order frame
  lastSeq = seq;
  command(payload, seq);
}

void setup() {
#ifdef __AVR__
  MCUSR = 0; wdt_disable();
#endif
  pinMode(L_STBY, OUTPUT); pinMode(R_STBY, OUTPUT);
  const uint8_t outs[] = {L_A1, L_A2, L_PWMA, L_B1, L_B2, L_PWMB, R_A1, R_A2, R_PWMA, R_B1, R_B2, R_PWMB};
  for (uint8_t i = 0; i < sizeof(outs); i++) pinMode(outs[i], OUTPUT);
  for (uint8_t i = 0; i < 4; i++) { pinMode(PAN[i], OUTPUT); pinMode(TILT[i], OUTPUT); }
  pinMode(PIR_PIN, INPUT);
  for (uint8_t i = 0; i < 3; i++) pinMode(CLIFF[i], INPUT);
  emergencyStop();
  Serial.begin(115200);
#ifdef __AVR__
  if (WATCHDOG_ENABLED) wdt_enable(WDTO_1S);
#endif
}

void loop() {
#ifdef __AVR__
  wdt_reset();
#endif
  uint8_t budget = 64;                       // bounded so a serial flood cannot starve the safety checks
  while (Serial.available() && budget--) {
    char c = Serial.read();
    if (c == '\n') {
      if (!discarding) { lineBuf[lineLen] = 0; parseLine(lineBuf); }
      lineLen = 0; discarding = false;
    } else if (c != '\r' && !discarding) {
      if (c < 32 || c > 126 || lineLen >= sizeof(lineBuf) - 1) { discarding = true; lineLen = 0; }
      else lineBuf[lineLen++] = c;
    }
  }
  if (!latched && (!heartbeatOK() || !cliffSafe())) emergencyStop();
  if (!latched) { driveTick(); headTick(); }
  if (millis() - lastTelem >= TELEM_MS) {
    lastTelem = millis();
    char t[100];
    snprintf(t, sizeof(t), "T,%d,%d,%d,%d,%d,%ld,%ld,%d,%d,%d", digitalRead(CLIFF[0]), digitalRead(CLIFF[1]),
             digitalRead(CLIFF[2]), digitalRead(PIR_PIN), headHomed ? 1 : 0, panPos, tiltPos,
             headMoving() ? 1 : 0, (outL || outR) ? 1 : 0, latched ? 1 : 0);
    if (haveSeq) tx(lastSeq, t);
  }
}
