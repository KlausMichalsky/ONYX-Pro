#line 1 "/Users/klausmichalsky/Proyectos Mac/ONYX-Pro_Workspace/ONYX-Pro/Zero/Zero.ino"
// =======================================================================
//                          🔹 O N Y X   -   P R O 🔹
// =======================================================================
//  Archivo    : Zero.ino
//  Autor      : Klaus Michalsky
//  Fecha      : Feb-2026
// -----------------------------------------------------------------------
//  ▫️ DESCRIPCIÓN
//      - Setup de inicialización
//      - Loop principal
// =======================================================================

#include <Arduino.h>
#include <Wire.h>

#include <AccelStepper.h>

#include "command.h"
#include "communication.h"
#include "config.h"
#include "core.h"
#include "homing.h"
#include "motors.h"
#include "sensors.h"
#include "utils.h"
#include "z_axis.h"

// SETUP
// -----------------------------------------------------------------------
#line 30 "/Users/klausmichalsky/Proyectos Mac/ONYX-Pro_Workspace/ONYX-Pro/Zero/Zero.ino"
void setup();
#line 45 "/Users/klausmichalsky/Proyectos Mac/ONYX-Pro_Workspace/ONYX-Pro/Zero/Zero.ino"
void loop();
#line 30 "/Users/klausmichalsky/Proyectos Mac/ONYX-Pro_Workspace/ONYX-Pro/Zero/Zero.ino"
void setup() {
    delay(1000);
    communicationInit();
    coreInit();
    homingInitXY(motor1Homing);
    homingInitXY(motor2Homing);
    homingInitZ(motor3Homing);
    motorsInit();
    sensorsInit();
    magnetInit();
    pinMode(LED, OUTPUT);
}

// LOOP
// -----------------------------------------------------------------------
void loop() {
    if (commandAvailable()) {
        String cmd = readCommand();
        if (cmd.length() > 0) // 🔥 SOLO procesar si hay comando completo.
        {
            processCommand(cmd);
        }
    }
    coreUpdate();
}

