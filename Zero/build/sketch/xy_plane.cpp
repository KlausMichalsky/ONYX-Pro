#line 1 "C:\\Users\\Klaus\\Documents\\ONYX-Pro\\Zero\\xy_plane.cpp"
// =======================================================================
//                      🔹 O N Y X   -   P R O 🔹
// =======================================================================
//  Archivo    : xy_plane.cpp
//  Autor      : Klaus Michalsky
//  Fecha      : Feb-2026
// -----------------------------------------------------------------------
//  ▫️ DESCRIPCIÓN
//      - Definición de funciones de movimientos
//      - Sincronización de movimientos
//      - Corrección de error (Feedback)
// =======================================================================

#include <Arduino.h>

#include "config.h"
#include "motors.h"
#include "sensors.h"
#include "utils.h"
#include "xy_plane.h"
#include "z_axis.h"

// VARIABLES LOCALES
// -----------------------------------------------------------------------
static float targetShoulderAngle = 0;
static float targetElbowAngle = 0;
static unsigned long settleStart = 0;

// DEFINICION DE MAQUINA DE ESTADOS PARA MOVIMIENTO XY-PLANE
// -----------------------------------------------------------------------
MovingStateXY movingStateXY = MovingStateXY::IDLE;
MoveSequenceState moveSeqState = MoveSequenceState::IDLE;
CaptureSequenceState captureSeqState = CaptureSequenceState::IDLE;

float startT1 = 0;
float startT2 = 0;
float endT1 = 0;
float endT2 = 0;
float captureT1 = 0;
float captureT2 = 0;
static float finalT1 = 0;
static float finalT2 = 0;

// Capture-Board: gestión de las 15 posiciones
static uint8_t nextCaptureSlot = 1;
static float captureBoardT1 = 0;
static float captureBoardT2 = 0;

// Datos para la segunda pieza del enroque (torre)
static bool castlingActive = false;
static float rookStartT1 = 0;
static float rookStartT2 = 0;
static float rookEndT1 = 0;
static float rookEndT2 = 0;

extern float currentShoulderAngle;
extern float currentElbowAngle;

// STATUS
// -----------------------------------------------------------------------
bool xyIsMoving() {
    return movingStateXY != MovingStateXY::IDLE;
}

// ASIGNACION DE DESTINO EN GRADOS (NO MUEVE TODAVIA)
// -----------------------------------------------------------------------
void moveToAngles(float shoulder, float elbow) {
    if (movingStateXY != MovingStateXY::IDLE)
        return;

    motorsEnableXY();

    // 🔥 1. CORRECCIÓN DE CONTINUIDAD (AQUÍ ES DONDE VA)
    float correctedShoulder = shortestAngle(shoulder, currentShoulderAngle);
    float correctedElbow = shortestAngle(elbow, currentElbowAngle);

    // 🔥 2. guardar targets corregidos
    targetShoulderAngle = correctedShoulder;
    targetElbowAngle = correctedElbow;

    // 🔥 3. convertir a pasos ya con valores suaves
    long sSteps = angleToStep(correctedShoulder, MotorID::J1);
    long eSteps = angleToStep(correctedElbow, MotorID::J2);

    motor1.moveTo(sSteps);
    motor2.moveTo(eSteps);

    movingStateXY = MovingStateXY::MOVING_TO_TARGET;
}

// ASIGNACION DEL DESTINO DEL ERROR EN GRADOS
// (UNA SOLA EJECUCIÓN POR CICLO, NO MUEVE TODAVIA)
// -----------------------------------------------------------------------
void correctErrorOnce() {
    motorsEnableXY();

    float errorShoulder =
        calculateError(targetShoulderAngle,
                       Wire,
                       motor1Config,
                       sensor1Offset);

    float errorElbow =
        calculateError(targetElbowAngle,
                       Wire1,
                       motor2Config,
                       sensor2Offset);

    bool needsCorrection = false;

    if (fabs(errorShoulder) > 0.5f) {
        float correctedShoulder =
            targetShoulderAngle +
            (motor1Config.motorDirection *
             errorShoulder / motor1Config.reduction);

        motor1.moveTo(
            angleToStep(correctedShoulder, MotorID::J1));

        needsCorrection = true;
    }

    if (fabs(errorElbow) > 0.5f) {
        float correctedElbow =
            targetElbowAngle +
            (motor2Config.motorDirection *
             errorElbow / motor2Config.reduction);

        motor2.moveTo(
            angleToStep(correctedElbow, MotorID::J2));

        needsCorrection = true;
    }

    if (needsCorrection) {
        movingStateXY = MovingStateXY::CORRECTING;
    } else {
        movingStateXY = MovingStateXY::IDLE;
    }
}

// MAQUINA DE ESTADOS PARA MOVIMIENTO XY-PLANE (MOVIMIENTO DE MOTORES)
// -----------------------------------------------------------------------
void updateXY() {
    switch (movingStateXY) {
        case MovingStateXY::IDLE:
            break;

        case MovingStateXY::MOVING_TO_TARGET:
            motor1.run();
            motor2.run();
            if (motor1.distanceToGo() == 0 &&
                motor2.distanceToGo() == 0) {
                settleStart = millis();
                delay(100); // estabilizacion mecanica
                COMM.print("Moved to Target");
                // 🔥 AQUÍ VA LO IMPORTANTE
                currentShoulderAngle = targetShoulderAngle;
                currentElbowAngle = targetElbowAngle;
                // printDebugMove(targetShoulderAngle, targetElbowAngle);
                movingStateXY = MovingStateXY::SETTLING;
            }
            break;

        case MovingStateXY::SETTLING:
            if (millis() - settleStart > 100) {
                movingStateXY = MovingStateXY::CORRECTING;
                // COMM.println("Correcting Error");
                correctErrorOnce();
            }
            break;

        case MovingStateXY::CORRECTING:
            motor1.run();
            motor2.run();
            if (motor1.distanceToGo() == 0 &&
                motor2.distanceToGo() == 0) {
                settleStart = millis();
                COMM.println("Correction Done");
                COMM.println();
                movingStateXY = MovingStateXY::IDLE;
            }
            break;
    }
}

// INICIAR SECUENCIA DE MOVIMIENTO COMPLETA (START → XY → Z → XY → Z)
// -----------------------------------------------------------------------
// startT1, startT2: ángulos iniciales para el movimiento XY
// endT1, endT2: ángulos finales para el movimiento XY
void startMoveSequence(float s1, float s2, float e1, float e2) {
    startT1 = s1;
    startT2 = s2;
    endT1 = e1;
    endT2 = e2;

    moveSeqState = MoveSequenceState::MOVING_START;

    moveToAngles(startT1, startT2);
}

// INICIAR SECUENCIA DE ENROQUE (REY → TORRE)
// -----------------------------------------------------------------------
void startCastlingSequence(float kingS1, float kingS2,
                           float kingE1, float kingE2,
                           float rookS1, float rookS2,
                           float rookE1, float rookE2) {
    // Guardar las coordenadas del rey
    startT1 = kingS1;
    startT2 = kingS2;
    endT1 = kingE1;
    endT2 = kingE2;

    // Guardar las coordenadas de la torre
    rookStartT1 = rookS1;
    rookStartT2 = rookS2;
    rookEndT1 = rookE1;
    rookEndT2 = rookE2;

    // Activar la secuencia especial de enroque
    castlingActive = true;

    // Comenzar moviendo el rey
    moveSeqState = MoveSequenceState::MOVING_START;
    moveToAngles(startT1, startT2);
}

// INICIAR SECUENCIA DE CAPTURA COMPLETA (XY → Z → HOME)
// -----------------------------------------------------------------------
bool startCaptureSequence(
    float captureT1_,
    float captureT2_,
    float finalT1_,
    float finalT2_) {
    // No iniciar otra captura si hay una secuencia activa.
    if (captureSeqState != CaptureSequenceState::IDLE ||
        moveSeqState != MoveSequenceState::IDLE ||
        movingStateZ != MovingStateZ::IDLE ||
        xyIsMoving()) {
        COMM.println("ERROR: ROBOT BUSY");
        return false;
    }

    // Comprobar si quedan posiciones disponibles.
    if (nextCaptureSlot > CAPTURE_BOARD_SLOTS) {
        COMM.println("ERROR: CAPTURE BOARD FULL");
        return false;
    }

    // Calcular los ángulos de la siguiente posición libre.
    if (!captureBoardToAngles(
            nextCaptureSlot,
            captureBoardT1,
            captureBoardT2)) {
        COMM.println("ERROR: CAPTURE BOARD SLOT");
        return false;
    }

    // Guardar destino y origen de la pieza atacante.
    captureT1 = captureT1_;
    captureT2 = captureT2_;
    finalT1 = finalT1_;
    finalT2 = finalT2_;

    // Iniciar la captura.
    captureSeqState = CaptureSequenceState::CAPTURE_START;
    moveToAngles(captureT1, captureT2);

    COMM.print("CAPTURE SLOT: ");
    COMM.println(nextCaptureSlot);

    return true;
}

// MAQUINA DE ESTADOS PARA SECUENCIA DE MOVIMIENTO COMPLETA (START → XY → Z → XY → Z)
// -----------------------------------------------------------------------
void updateMoveSequence() {
    switch (moveSeqState) {
        // 1. Ir a la pieza inicial (rey o torre)
        case MoveSequenceState::MOVING_START:
            if (!xyIsMoving()) {
                startZPick();
                moveSeqState = MoveSequenceState::PICKING;
            }
            break;

        // 2. Esperar a que termine la recogida
        case MoveSequenceState::PICKING:
            if (movingStateZ == MovingStateZ::IDLE) {
                moveToAngles(endT1, endT2);
                moveSeqState = MoveSequenceState::MOVING_END;
            }
            break;

        // 3. Llevar la pieza a su destino
        case MoveSequenceState::MOVING_END:
            if (!xyIsMoving()) {
                startZPlace();
                moveSeqState = MoveSequenceState::PLACING;
            }
            break;

        // 4. Esperar a que termine la colocación
        case MoveSequenceState::PLACING:
            if (movingStateZ == MovingStateZ::IDLE) {
                if (castlingActive) {
                    // El rey ya está colocado.
                    // Preparar el movimiento de la torre.
                    startT1 = rookStartT1;
                    startT2 = rookStartT2;
                    endT1 = rookEndT1;
                    endT2 = rookEndT2;

                    moveToAngles(startT1, startT2);
                    moveSeqState =
                        MoveSequenceState::CASTLING_ROOK_START;

                } else {
                    // Iniciar regreso a HOME.
                    moveToHomeXY();
                    moveSeqState = MoveSequenceState::GO_HOME;
                }
            }
            break;

        // 5. Esperar a llegar a la torre
        case MoveSequenceState::CASTLING_ROOK_START:
            if (!xyIsMoving()) {
                startZPick();
                moveSeqState =
                    MoveSequenceState::CASTLING_ROOK_PICKING;
            }
            break;

        // 6. Esperar a recoger la torre
        case MoveSequenceState::CASTLING_ROOK_PICKING:
            if (movingStateZ == MovingStateZ::IDLE) {
                moveToAngles(endT1, endT2);
                moveSeqState =
                    MoveSequenceState::CASTLING_ROOK_END;
            }
            break;

        // 7. Transportar la torre a su destino
        case MoveSequenceState::CASTLING_ROOK_END:
            if (!xyIsMoving()) {
                startZPlace();
                moveSeqState =
                    MoveSequenceState::CASTLING_ROOK_PLACING;
            }
            break;

        // 8. Esperar a colocar la torre
        case MoveSequenceState::CASTLING_ROOK_PLACING:
            if (movingStateZ == MovingStateZ::IDLE) {
                // Ambas piezas están colocadas.
                castlingActive = false;

                // Iniciar regreso a HOME.
                moveToHomeXY();
                moveSeqState =
                    MoveSequenceState::CASTLING_WAIT_HOME;
            }
            break;

        // 9. Esperar a terminar el regreso a HOME
        case MoveSequenceState::CASTLING_WAIT_HOME:
            if (!xyIsMoving()) {
                COMM.println("MOVE DONE");
                moveSeqState = MoveSequenceState::IDLE;
            }
            break;

            // 10. Regreso a HOME de un movimiento normal
        case MoveSequenceState::GO_HOME:
            if (!xyIsMoving()) {
                COMM.println("MOVE DONE");
                moveSeqState = MoveSequenceState::IDLE;
            }
            break;

        case MoveSequenceState::IDLE:
        default:
            break;
    }
}

void updateCaptureSequence() {
    switch (captureSeqState) {
        // 1. Ir a pieza enemiga
        case CaptureSequenceState::CAPTURE_START:

            if (!xyIsMoving()) {
                startZPick();
                captureSeqState = CaptureSequenceState::PICKING_OPPONENT;
            }
            break;

            // 2. Esperar pick enemigo
        case CaptureSequenceState::PICKING_OPPONENT:

            if (movingStateZ == MovingStateZ::IDLE) {
                moveToAngles(captureBoardT1, captureBoardT2);
                captureSeqState = CaptureSequenceState::TAKE_PIECE_OUT;
            }
            break;

        // 3. Sacar pieza
        case CaptureSequenceState::TAKE_PIECE_OUT:

            if (!xyIsMoving()) {
                startZPlace();
                captureSeqState = CaptureSequenceState::PLACING_OPPONENT;
            }
            break;

        // 4. Esperar a que termine de depositar la pieza capturada
        case CaptureSequenceState::PLACING_OPPONENT:

            if (movingStateZ == MovingStateZ::IDLE) {
                nextCaptureSlot++;

                // Ir directamente a la pieza atacante, sin pasar por HOME.
                captureSeqState =
                    CaptureSequenceState::MOVING_OWN_PIECE_START;
            }
            break;

        // 5. Ir a pieza propia (XY)
        case CaptureSequenceState::MOVING_OWN_PIECE_START:

            if (!xyIsMoving()) {
                moveToAngles(finalT1, finalT2);
                captureSeqState = CaptureSequenceState::PICKING_OWN_PIECE;
            }
            break;

        // 6. Esperar llegada a pieza propia
        case CaptureSequenceState::PICKING_OWN_PIECE:

            if (!xyIsMoving()) {
                startZPick();
                captureSeqState = CaptureSequenceState::MOVING_OWN_PIECE_END;
            }
            break;

        // 7. Mover pieza propia a destino
        case CaptureSequenceState::MOVING_OWN_PIECE_END:

            if (movingStateZ == MovingStateZ::IDLE) {
                moveToAngles(captureT1, captureT2);
                captureSeqState = CaptureSequenceState::PLACING_OWN_PIECE;
            }
            break;

        // 8. Esperar llegada a destino
        case CaptureSequenceState::PLACING_OWN_PIECE:

            if (!xyIsMoving()) {
                startZPlace();
                captureSeqState = CaptureSequenceState::GO_HOME;
            }
            break;

        // 9. Iniciar regreso a HOME después de colocar la pieza propia
        case CaptureSequenceState::GO_HOME:

            if (movingStateZ == MovingStateZ::IDLE) {
                moveToHomeXY();
                captureSeqState = CaptureSequenceState::WAIT_HOME;
            }
            break;

        // 10. Esperar a que XY termine de regresar a HOME
        case CaptureSequenceState::WAIT_HOME:

            if (!xyIsMoving()) {
                COMM.println("CAPTURE DONE");
                captureSeqState = CaptureSequenceState::IDLE;
            }
            break;

        case CaptureSequenceState::IDLE:
        default:
            break;
    }
}

bool resetCaptureCounter() {
    // No reiniciar mientras el robot esté ocupado.
    if (captureSeqState != CaptureSequenceState::IDLE ||
        moveSeqState != MoveSequenceState::IDLE ||
        movingStateZ != MovingStateZ::IDLE ||
        xyIsMoving()) {
        COMM.println("ERROR: ROBOT BUSY");
        return false;
    }

    // Reiniciar el contador al primer espacio.
    nextCaptureSlot = 1;

    COMM.println("CAPTURE COUNTER RESET");
    return true;
}

// MOVIMIENTO A HOME DEL PLANO XY
// (NO ES HOMING SOLO REGRESAR A POSICION CERO DESPUES DEL MOVIMIENTO)
// -----------------------------------------------------------------------
void moveToHomeXY() {
    moveToAngles(0.0f, 0.0f);
}

// DEBUG
// -----------------------------------------------------------------------
void printDebugMove(float motor1Angle, float motor2Angle) {
    COMM.println();
    COMM.println("-------- MOTOR 1 --------");

    float sensor1 = estimateSensorAngle(
        targetShoulderAngle,
        motor1Config.reduction,
        sensor1Offset,
        motor1Config.motorDirection);

    COMM.print("HomingOffset: ");
    COMM.println(sensor1Offset, 1);

    COMM.print("Estimated Sensor Angle: ");
    COMM.println(sensor1, 1);

    COMM.print("Real Sensor Angle: ");
    COMM.println(rawToDegrees(sensorReadRawAngle(Wire)), 1);

    COMM.println("-------- MOTOR 2 --------");

    float sensor2 = estimateSensorAngle(
        targetElbowAngle,
        motor2Config.reduction,
        sensor2Offset,
        motor2Config.motorDirection);

    COMM.print("HomingOffset: ");
    COMM.println(sensor2Offset, 1);

    COMM.print("Estimated Sensor Angle: ");
    COMM.println(round1Decimal(sensor2), 1);

    COMM.print("Real Sensor Angle: ");
    COMM.println(rawToDegrees(sensorReadRawAngle(Wire1)), 1);

    COMM.println();

    float errorShoulder =
        calculateError(targetShoulderAngle, Wire, motor1Config, sensor1Offset);

    float errorElbow =
        calculateError(targetElbowAngle, Wire1, motor2Config, sensor2Offset);

    COMM.print("Error1: ");
    COMM.println(errorShoulder, 1);

    COMM.print("Error2: ");
    COMM.println(errorElbow, 1);

    COMM.println();
}

void resetXYState() {
    // =========================
    // RESET DE MÁQUINA XY
    // =========================

    movingStateXY = MovingStateXY::IDLE;
    moveSeqState = MoveSequenceState::IDLE;
    captureSeqState = CaptureSequenceState::IDLE;

    // =========================
    // RESET DE TARGETS
    // =========================

    targetShoulderAngle = 0;
    targetElbowAngle = 0;

    startT1 = 0;
    startT2 = 0;
    endT1 = 0;
    endT2 = 0;
    captureT1 = 0;
    captureT2 = 0;

    // =========================
    // RESET DE TIEMPOS
    // =========================

    settleStart = 0;

    // =========================
    // OPCIONAL SEGURIDAD
    // =========================

    motor1.stop();
    motor2.stop();

    COMM.println("XY STATE RESET");
}

void cancelMoveSequence() {
    // parar máquina de estados
    moveSeqState = MoveSequenceState::IDLE;
    captureSeqState = CaptureSequenceState::IDLE;

    // parar XY inmediatamente
    motor1.stop();
    motor2.stop();

    // opcional: reset targets
    startT1 = 0;
    startT2 = 0;
    endT1 = 0;
    endT2 = 0;
    captureT1 = 0;
    captureT2 = 0;

    // opcional: reset estado XY también
    movingStateXY = MovingStateXY::IDLE;

    COMM.println("MOVE SEQUENCE CANCELED");
}