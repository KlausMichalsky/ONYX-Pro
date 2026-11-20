// =======================================================================
//                      🔹 O N Y X   -   P R O 🔹
// =======================================================================
//  Archivo    : command.cpp
//  Autor      : Klaus Michalsky
//  Fecha      : Feb-2026
// -----------------------------------------------------------------------
//  ▫️ DESCRIPCIÓN
//      - Definición de funciones para la gestión de comandos
//        recibidos por UART
// =======================================================================

#include <Arduino.h>

#include <AccelStepper.h>

#include "Z_Axis.h"
#include "command.h"
#include "config.h"
#include "core.h"
#include "homing.h"
#include "motors.h"
#include "sensors.h"
#include "utils.h"
#include "xy_plane.h"

// VARIABLES EXTERNAS
// -----------------------------------------------------------------------
extern HomingXY motor1Homing;
extern HomingXY motor2Homing;
extern HomingZ motor3Homing;
extern bool homeAllActive;

// COMPROBACIÓN DE COMANDOS DISPONIBLES
// -----------------------------------------------------------------------
// Si usas Serial1 para comunicacion TX/RX, descomenta esta función y comenta la siguiente
// bool commandAvailable() {
//     return Serial1.available();
// }

// Si usas Serial comunicacion por USB, descomenta esta función y comenta la anterior
bool commandAvailable() {
    return COMM.available();
}

// ENVIO DE RESPUESTA DE STATUS DE TODOS LOS MOTORES Y SENSORES
// -----------------------------------------------------------------------
// Si usas Serial1 para comunicacion TX/RX, descomenta esta función y comenta la siguiente
// void commandSendStatusReport() {
//     String report = "";
//     report += motorStatus(MotorID::J1) + "\n";
//     report += motorStatus(MotorID::J2) + "\n";
//     report += motorStatus(MotorID::Z) + "\n";

//     Serial1.print(report);
// }

// Si usas Serial comunicacion por USB, descomenta esta función y comenta la anterior
void commandSendStatusReport() {
    String report = "";
    report += motorStatus(MotorID::J1) + "\n";
    report += motorStatus(MotorID::J2) + "\n";
    report += motorStatus(MotorID::Z) + "\n";

    COMM.print(report);
}

// LECTURA DE COMANDOS
// -----------------------------------------------------------------------
String readCommand() {
    static String buffer = "";
    while (COMM.available()) {
        char c = COMM.read();
        if (c == '\n') {
            String cmd = buffer;
            buffer = "";
            cmd.trim();
            return cmd;
        } else {
            buffer += c;
        }
    }
    return ""; // return si no hay comando completo todavía
}

// MAPEO DE STRING A ENUM CLASS COMMAND
// -----------------------------------------------------------------------
Command parseCommand(const String &cmd) {
    if (cmd == "STATUS")
        return Command::STATUS;
    else if (cmd == "RESET")
        return Command::RESET;
    else if (cmd == "ANGLES")
        return Command::ANGLES;
    else if (cmd == "BOARD")
        return Command::BOARD;
    else if (cmd == "COMMANDS")
        return Command::COMMANDS;
    else if (cmd == "HOME")
        return Command::HOME;
    else if (cmd == "HOMING")
        return Command::HOMING;
    else if (cmd.startsWith("MOVE"))
        return Command::MOVE;
    else if (cmd == "PICK")
        return Command::PICK;
    else if (cmd == "PLACE")
        return Command::PLACE;
    else if (cmd.startsWith("REMOVE"))
        return Command::REMOVE;
    else if (cmd.startsWith("SQUARE"))
        return Command::SQUARE;
    else if (cmd == "CAPTURETEST")
        return Command::CAPTURETEST;
    else if (cmd == "CAPTURERESET")
        return Command::CAPTURERESET;
    else if (cmd == "MOTOROFF")
        return Command::MOTOROFF;
    else
        return Command::UNKNOWN;
}

// PROCESAMIENTO DE COMANDOS
// -----------------------------------------------------------------------
void processCommand(const String &cmdStr) {
    String trimmedCmd = cmdStr;
    trimmedCmd.trim(); // eliminar espacios al iniciofinal,
    // justo después de crear trimmedCmd

    COMM.print("RX=[");
    COMM.print(trimmedCmd);
    COMM.println("]");

    Command cmd = parseCommand(trimmedCmd);

    switch (cmd) {
        case Command::STATUS:
            commandSendStatusReport();
            break;

        case Command::RESET:

            // 1. parar cualquier movimiento activo
            stopAllMotors();      // ⬅️ IMPORTANTE (si no existe, hay que crearla)
            cancelMoveSequence(); // ⬅️ clave si tenés planner
            resetXYState();       // 🔥 ESTO ES CLAVE

            // 2. reset flags de homing
            motor1Homing.fault = false;
            motor2Homing.fault = false;
            motor3Homing.fault = false;

            // 3. reset estados de homing
            homingInitXY(motor1Homing);
            homingInitXY(motor2Homing);
            homingInitZ(motor3Homing);

            // 4. reset máquina de estados global
            homeAllState = HomeAllState::IDLE;

            // 5. reset posición lógica (MUY IMPORTANTE)
            setCurrentPositionHome(); // ⬅️ o algo equivalente en tu sistema

            COMM.println("SYSTEM RESET OK");
            break;

        case Command::ANGLES:
            COMM.print("ANGLE1: ");
            COMM.println(rawToDegrees(sensorReadRawAngle(Wire)), 1);
            COMM.print("ANGLE2: ");
            COMM.println(rawToDegrees(sensorReadRawAngle(Wire1)), 1);
            COMM.println();
            break;

        case Command::BOARD:
            printBoardXY();
            break;

        case Command::COMMANDS:
            break;

        case Command::HOME:
            moveToHomeXY();
            // COMM.println("HOME DONE"); // NO HOME DONE AQUI (esperar a que el movimiento termine para mandar el mensaje)
            break;

        case Command::HOMING:
            COMM.println("HOMING SEQUENCE STARTED");
            homeAllState = HomeAllState::MOTOR1;
            break;

        case Command::MOVE: {
            char startSquare[4] = {0};
            char endSquare[4] = {0};

            int parsed = sscanf(trimmedCmd.c_str(),
                                "MOVE %3s %3s",
                                startSquare,
                                endSquare);

            if (parsed != 2) {
                COMM.println("ERROR MOVE FORMAT");
                break;
            }

            if (strcmp(startSquare, endSquare) == 0) {
                COMM.println("ERROR SAME SQUARE");
                break;
            }

            float s1, s2;
            float e1, e2;

            if (!chessSquareToAngles(String(startSquare), s1, s2)) {
                COMM.println("ERROR START");
                break;
            }

            if (!chessSquareToAngles(String(endSquare), e1, e2)) {
                COMM.println("ERROR END");
                break;
            }

            // SOLO UNA LLAMADA
            String start = String(startSquare);
            String end = String(endSquare);

            String rookStart = "";
            String rookEnd = "";

            if (start == "e1" && end == "g1") {
                rookStart = "h1";
                rookEnd = "f1";
            } else if (start == "e1" && end == "c1") {
                rookStart = "a1";
                rookEnd = "d1";
            } else if (start == "e8" && end == "g8") {
                rookStart = "h8";
                rookEnd = "f8";
            } else if (start == "e8" && end == "c8") {
                rookStart = "a8";
                rookEnd = "d8";
            }

            if (rookStart != "") {
                float rookS1, rookS2;
                float rookE1, rookE2;

                if (!chessSquareToAngles(rookStart, rookS1, rookS2) ||
                    !chessSquareToAngles(rookEnd, rookE1, rookE2)) {
                    COMM.println("ERROR CASTLING ROOK");
                    break;
                }

                startCastlingSequence(
                    s1, s2, e1, e2,
                    rookS1, rookS2, rookE1, rookE2);
            } else {
                startMoveSequence(s1, s2, e1, e2);
            }
            break;
        }

        case Command::PICK:
            Serial1.println("PICKING PIECE!");
            startZPick(); // bloqueante: sube/baja Z y activa imán
            // después de esto, XY puede moverse sin problemas
            break;

        case Command::PLACE:
            Serial1.println("PLACING PIECE!");
            startZPlace(); // bloqueante: sube/baja Z y desactiva imán
            break;

        case Command::REMOVE: {
            char capturedSquare[4] = {0};
            char attackerStartSquare[4] = {0};
            char attackerEndSquare[4] = {0};

            int parsed = sscanf(trimmedCmd.c_str(),
                                "REMOVE %3s %3s %3s",
                                capturedSquare,
                                attackerStartSquare,
                                attackerEndSquare);

            if (parsed != 3) {
                COMM.println("ERROR REMOVE FORMAT");
                break;
            }

            float capturedT1, capturedT2;
            float attackerStartT1, attackerStartT2;
            float attackerEndT1, attackerEndT2;

            if (!chessSquareToAngles(
                    String(capturedSquare),
                    capturedT1,
                    capturedT2)) {
                COMM.println("ERROR CAPTURED");
                break;
            }

            if (!chessSquareToAngles(
                    String(attackerStartSquare),
                    attackerStartT1,
                    attackerStartT2)) {
                COMM.println("ERROR ATTACKER START");
                break;
            }

            if (!chessSquareToAngles(
                    String(attackerEndSquare),
                    attackerEndT1,
                    attackerEndT2)) {
                COMM.println("ERROR ATTACKER END");
                break;
            }

            // Iniciar la secuencia completa de captura.
            if (startCaptureSequence(
                    capturedT1, capturedT2,
                    attackerStartT1, attackerStartT2,
                    attackerEndT1, attackerEndT2)) {
                COMM.println("REMOVE STARTED");
            }

            break;
        }

        case Command::SQUARE: {
            char square[3];

            int parsed = sscanf(trimmedCmd.c_str(), "SQUARE %2s", square);
            // "SQUARE %2s" leer máximo 2 caracteres.

            if (parsed != 1) {
                Serial1.println("ERROR: SQUARE format invalid");
                break;
            }

            float shoulderDeg;
            float elbowDeg;

            // CASILLA -> ANGULOS
            if (!chessSquareToAngles(
                    String(square),
                    shoulderDeg,
                    elbowDeg)) {
                Serial1.println("ERROR: Invalid square or unreachable");
                break;
            }

            // MOVER BRAZO
            moveToAngles(shoulderDeg, elbowDeg);
            break;
        }

        case Command::CAPTURETEST: {
            COMM.println("CAPTURE-BOARD ANGLE TEST");

            for (uint8_t position = 1;
                 position <= CAPTURE_BOARD_SLOTS;
                 position++) {
                float theta1Deg;
                float theta2Deg;

                COMM.print("Position ");
                COMM.print(position);
                COMM.print(": ");

                if (captureBoardToAngles(
                        position, theta1Deg, theta2Deg)) {
                    COMM.print("T1 = ");
                    COMM.print(theta1Deg, 2);
                    COMM.print(" deg, T2 = ");
                    COMM.print(theta2Deg, 2);
                    COMM.println(" deg");

                } else {
                    COMM.println("ERROR: unreachable or invalid");
                }
            }

            COMM.println("CAPTURETEST DONE");
            break;
        }

        case Command::CAPTURERESET:
            resetCaptureCounter();
            break;

        case Command::MOTOROFF:
            cancelMoveSequence();
            movingStateZ = MovingStateZ::IDLE;
            magnetOFF();
            stopAllMotors();
            motorsDisableXY();
            motorDisableZ();
            COMM.println("MOTORS OFF");
            break;

        default: {
            // ==========================================================
            // 🧠 NUEVO: soporte para Stockfish (UCI: e2e4)
            // ==========================================================

            if (trimmedCmd.length() == 4 &&
                isalpha(trimmedCmd[0]) &&
                isdigit(trimmedCmd[1]) &&
                isalpha(trimmedCmd[2]) &&
                isdigit(trimmedCmd[3])) {
                float s1, s2;
                float e1, e2;

                String startSquare = trimmedCmd.substring(0, 2);
                String endSquare = trimmedCmd.substring(2, 4);

                if (!chessSquareToAngles(startSquare, s1, s2)) {
                    COMM.println("ERROR START");
                    break;
                }

                if (!chessSquareToAngles(endSquare, e1, e2)) {
                    COMM.println("ERROR END");
                    break;
                }

                COMM.print("OK:");
                COMM.println(trimmedCmd);

                COMM.print("START=");
                COMM.println(startSquare);

                COMM.print("END=");
                COMM.println(endSquare);

                String rookStartSquare = "";
                String rookEndSquare = "";

                if (startSquare == "e1" && endSquare == "g1") {
                    rookStartSquare = "h1";
                    rookEndSquare = "f1";
                } else if (startSquare == "e1" && endSquare == "c1") {
                    rookStartSquare = "a1";
                    rookEndSquare = "d1";
                } else if (startSquare == "e8" && endSquare == "g8") {
                    rookStartSquare = "h8";
                    rookEndSquare = "f8";
                } else if (startSquare == "e8" && endSquare == "c8") {
                    rookStartSquare = "a8";
                    rookEndSquare = "d8";
                } else if (startSquare == "d1" && endSquare == "b1") {
                    rookStartSquare = "a1";
                    rookEndSquare = "c1";
                } else if (startSquare == "d1" && endSquare == "f1") {
                    rookStartSquare = "h1";
                    rookEndSquare = "e1";
                }

                if (rookStartSquare != "") {
                    float rookS1, rookS2;
                    float rookE1, rookE2;

                    if (!chessSquareToAngles(
                            rookStartSquare, rookS1, rookS2) ||
                        !chessSquareToAngles(
                            rookEndSquare, rookE1, rookE2)) {
                        COMM.println("ERROR CASTLING ROOK");
                        break;
                    }

                    startCastlingSequence(
                        s1, s2, e1, e2,
                        rookS1, rookS2, rookE1, rookE2);
                } else {
                    startMoveSequence(s1, s2, e1, e2);
                }
                break;
            }

            COMM.println("UNKNOWN COMMAND");
            break;
        }
    }
}