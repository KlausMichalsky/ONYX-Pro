#line 1 "C:\\Users\\Klaus\\Documents\\ONYX-Pro\\Zero\\xy_plane.h"
// =======================================================================
//                      🔹 O N Y X   -   P R O 🔹
// =======================================================================
//  Archivo    : xy_plane.h
//  Autor      : Klaus Michalsky
//  Fecha      : Feb-2026
// -----------------------------------------------------------------------
//  ▫️ DESCRIPCIÓN
//      - Declaracion de funciones de movimientos
//      - Sincronización de movimientos
//      - Corrección de error (Feedback)
// =======================================================================

#pragma once

#include <Arduino.h>

extern float sensor1Offset;
extern float sensor2Offset;
extern MoveSequenceState moveSeqState;
extern CaptureSequenceState captureSeqState;

void moveToAngles(float targetShoulder, float targetElbow);
void moveToHomeXY();
void updateXY();
void updateMoveSequence();
bool xyIsMoving();
void printDebugMove(float motor1Angle, float motor2Angle);
void correctErrorOnce();
void startMoveSequence(float s1, float s2, float e1, float e2);
// kingS: origen del rey.
// kingE: destino del rey.
// rookS: origen de la torre.
// rookE: destino de la torre.
void startCastlingSequence(float kingS1, float kingS2,
                           float kingE1, float kingE2,
                           float rookS1, float rookS2,
                           float rookE1, float rookE2);
bool startCaptureSequence(float captureT1_,
                          float captureT2_,
                          float finalT1_,
                          float finalT2_);
bool resetCaptureCounter();
void updateCaptureSequence();
void resetXYState();
void cancelMoveSequence();