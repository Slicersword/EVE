// Fake Arduino core so the real sketch can be compiled and tested on a PC (tests/test_firmware_sim.py).
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <deque>
#include <string>
#include <iostream>
#include <sstream>
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT 0
#ifndef min
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
#endif
extern unsigned long fake_us;
extern int pin_out[80], pwm_out[80], pin_in[80];
inline unsigned long millis() { return fake_us / 1000; }
inline unsigned long micros() { return fake_us; }
inline void pinMode(int, int) {}
inline void digitalWrite(int p, int v) { pin_out[p] = v; }
inline int digitalRead(int p) { return pin_in[p]; }
inline void analogWrite(int p, int v) { pwm_out[p] = v; }
struct SerialType {
  std::deque<char> input;
  std::string output;
  void begin(long) {}
  int available() { return (int)input.size(); }
  char read() { char c = input.front(); input.pop_front(); return c; }
  void print(const char* s) { output += s; }
};
extern SerialType Serial;
