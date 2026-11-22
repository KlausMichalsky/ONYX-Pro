#line 1 "C:\\Users\\Klaus\\Documents\\ONYX-Pro\\Zero\\core.cpp"
// =======================================================================
//                      🔹 O N Y X   -   P R O 🔹
// =======================================================================
//  Archivo    : core.cpp
//  Autor      : Klaus Michalsky
//  Fecha      : Mar-2026
// -----------------------------------------------------------------------
//  ▫️ DESCRIPCIÓN
//      - Implementación de funciones centrales de sincronización
// =======================================================================

#include <Arduino.h>

#include "command.h"
#include "core.h"
#include "homing.h"
#include "motors.h"
#include "sensors.h"
#include "utils.h"
#include "xy_plane.h"
#include "z_axis.h"

// 🔥 DEFINICIÓN REAL (NO extern)
float currentShoulderAngle = 0.0f;
float currentElbowAngle = 0.0f;

static AutoRecoveryState autoRecoveryState = AutoRecoveryState::IDLE;

// INICIALIZACIÓN DEL CORE
// -----------------------------------------------------------------------
void coreInit() {
    homeAllState = HomeAllState::IDLE;
    homeSingleState = HomeSingleState::IDLE;
    autoRecoveryState = AutoRecoveryState::IDLE;
}

static void updateAutoRecovery() {
    switch (autoRecoveryState) {
        case AutoRecoveryState::START_J1:

            COMM.println("XY AUTO RECOVERY: HOMING J1");

            homingInitXY(motor1Homing);

            homingStartXY(
                motor1,
                motor1Config,
                motor1Homing,
                HALL_1);

            autoRecoveryState = AutoRecoveryState::WAIT_J1;
            break;

        case AutoRecoveryState::WAIT_J1:

            homingStepXY(
                motor1,
                motor1Config,
                motor1Homing,
                HALL_1);

            if (motor1Homing.state == HomingStateXY::OK) {
                COMM.println("J1 HOMING OK");

                homingInitXY(motor1Homing);

                autoRecoveryState = AutoRecoveryState::START_J2;

            } else if (motor1Homing.state == HomingStateXY::ERROR) {
                COMM.println("ERROR: AUTO RECOVERY J1 FAILED");

                motor1.stop();
                motor2.stop();
                motorsDisableXY();

                autoRecoveryState = AutoRecoveryState::ERROR;
            }

            break;

        case AutoRecoveryState::START_J2:

            COMM.println("XY AUTO RECOVERY: HOMING J2");

            homingInitXY(motor2Homing);

            homingStartXY(
                motor2,
                motor2Config,
                motor2Homing,
                HALL_2);

            autoRecoveryState = AutoRecoveryState::WAIT_J2;
            break;

        case AutoRecoveryState::WAIT_J2:

            homingStepXY(
                motor2,
                motor2Config,
                motor2Homing,
                HALL_2);

            if (motor2Homing.state == HomingStateXY::OK) {
                COMM.println("J2 HOMING OK");

                homingInitXY(motor2Homing);

                // Sincronizar únicamente las referencias articulares XY.
                currentShoulderAngle = 0.0f;
                currentElbowAngle = 0.0f;

                COMM.println("XY AUTO RECOVERY DONE");

                autoRecoveryState = AutoRecoveryState::DONE;

            } else if (motor2Homing.state == HomingStateXY::ERROR) {
                COMM.println("ERROR: AUTO RECOVERY J2 FAILED");

                motor1.stop();
                motor2.stop();
                motorsDisableXY();

                autoRecoveryState = AutoRecoveryState::ERROR;
            }

            break;

        case AutoRecoveryState::IDLE:
        case AutoRecoveryState::DONE:
        case AutoRecoveryState::ERROR:
            break;
    }
}

// CONTROL DE TAREAS EN EL FLUJO
// -----------------------------------------------------------------------
void coreUpdate() {
    if (homeAllState != HomeAllState::IDLE) {
        coreHomeAll();
        return;
    }

    if (homeSingleState != HomeSingleState::IDLE) {
        coreHomeSingleMotor();
        return;
    }
    // RECUPERACIÓN AUTOMÁTICA XY
    if (autoRecoveryState == AutoRecoveryState::START_J1 ||
        autoRecoveryState == AutoRecoveryState::WAIT_J1 ||
        autoRecoveryState == AutoRecoveryState::START_J2 ||
        autoRecoveryState == AutoRecoveryState::WAIT_J2) {
        updateAutoRecovery();
        return;
    }

    updateXY();
    updateZ();

    // 🔥 SOLO UNA STATE MACHINE ACTIVA
    if (captureSeqState != CaptureSequenceState::IDLE) {
        updateCaptureSequence();
    } else if (moveSeqState != MoveSequenceState::IDLE) {
        updateMoveSequence();
    }
    // ...otras tareas
}

// HOMING PARA MOTORES INDEPENDIENTES
// -----------------------------------------------------------------------
void coreHomeSingleMotor() {
    // Motor 1
    if (homingXYisActive(motor1Homing)) {
        homingStepXY(motor1, motor1Config, motor1Homing, HALL_1);
    }
    if (motor1Homing.state == HomingStateXY::OK) {
        COMM.print(motorStatus(MotorID::J1));
        homeSingleState = HomeSingleState::DONE;
        homingInitXY(motor1Homing);
        return;
    }

    // Motor 2
    if (homingXYisActive(motor2Homing)) {
        homingStepXY(motor2, motor2Config, motor2Homing, HALL_2);
    }
    if (motor2Homing.state == HomingStateXY::OK) {
        COMM.print(motorStatus(MotorID::J2));
        homeSingleState = HomeSingleState::DONE;
        homingInitXY(motor2Homing);
        return;
    }

    // Motor 3
    if (homingZisActive(motor3Homing)) {
        homingStepZ(motor3, motor3Config, motor3Homing, HALL_3);
    }
    if (motor3Homing.state == HomingStateZ::OK) {
        COMM.print(motorStatus(MotorID::Z));
        homeSingleState = HomeSingleState::DONE;
        homingInitZ(motor3Homing);
        return;
    }
}

// HOMING PARA TODOS LOS MOTORES
// -----------------------------------------------------------------------
void coreHomeAll() {
    // Ejecutar homings normalmente
    switch (homeAllState) {
        case HomeAllState::MOTOR1:
            if (motor1Homing.state == HomingStateXY::INACTIVE)
                homingStartXY(motor1, motor1Config, motor1Homing, HALL_1);

            homingStepXY(motor1, motor1Config, motor1Homing, HALL_1);

            if (motor1Homing.state == HomingStateXY::OK)
                homeAllState = HomeAllState::MOTOR2;
            break;

        case HomeAllState::MOTOR2:
            if (motor2Homing.state == HomingStateXY::INACTIVE)
                homingStartXY(motor2, motor2Config, motor2Homing, HALL_2);

            homingStepXY(motor2, motor2Config, motor2Homing, HALL_2);

            if (motor2Homing.state == HomingStateXY::OK)
                homeAllState = HomeAllState::MOTOR3;
            break;

        case HomeAllState::MOTOR3:
            if (motor3Homing.state == HomingStateZ::INACTIVE)
                homingStartZ(motor3, motor3Config, motor3Homing, HALL_3);

            homingStepZ(motor3, motor3Config, motor3Homing, HALL_3);

            if (motor3Homing.state == HomingStateZ::OK) {
                homeAllState = HomeAllState::DONE;
                commandSendStatusReport();

                COMM.println("DONE"); // 👈 ESTO ES LO IMPORTANTE
                                      // Manda un mensaje de "DONE" al finalizar el homing de todos los motores,
                                      // para que el Raspi sepa que puede continuar con el primer movimiento.
                delay(100);
                homingInitXY(motor1Homing);
                homingInitXY(motor2Homing);
                homingInitZ(motor3Homing);

                digitalWrite(LED, HIGH);

                // 🔥 GUARDAR OFFSET SOLO UNA VEZ
                delay(200);
                sensor1Offset = sensorHomingOffset(Wire);
                delay(200);
                sensor2Offset = sensorHomingOffset(Wire1);
            }
            break;

        case HomeAllState::DONE:
            homeAllState = HomeAllState::IDLE;

            break;

        default:
            break;
    }
}

bool coreStartAutoRecovery() {
    if (autoRecoveryState != AutoRecoveryState::IDLE) {
        return false;
    }

    autoRecoveryState = AutoRecoveryState::START_J1;
    return true;
}

AutoRecoveryState coreGetAutoRecoveryState() {
    return autoRecoveryState;
}

void coreResetAutoRecovery() {
    autoRecoveryState = AutoRecoveryState::IDLE;
}