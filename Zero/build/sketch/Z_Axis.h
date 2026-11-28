#line 1 "/Users/klausmichalsky/Proyectos Mac/ONYX-Pro_Workspace/ONYX-Pro/Zero/z_Axis.h"
// =======================================================================
//                      🔹 O N Y X   -   P R O 🔹
// =======================================================================
//  Archivo    : z_axis.h
//  Autor      : Klaus Michalsky
//  Fecha      : Feb-2026
// -----------------------------------------------------------------------
//  ▫️ DESCRIPCIÓN
//      - Declaración de funciones para movimiento del eje Z
//      - Sincronización de movimiento del eje Z
//      - Controll del electroimán
// =======================================================================

#include <Arduino.h>

#include "config.h"

#pragma once

// estado global del Z
extern MovingStateZ movingStateZ;

void zMoveHome();
void zMoveDown();
void zMoveTravel();
void magnetInit();
void magnetON();
void magnetOFF();
void startZPick();
void startZPlace();
void updateZ();