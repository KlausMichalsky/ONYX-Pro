#line 1 "C:\\Users\\Klaus\\Documents\\ONYX-Pro\\Zero\\config.h"
// =======================================================================
//                      🔹 O N Y X   -   P R O 🔹
// =======================================================================
//  Archivo    : config.h
//  Autor      : Klaus Michalsky
//  Fecha      : Feb-2026
// -----------------------------------------------------------------------
//  ▫️ DESCRIPCIÓN
//      - Pines de configuración
//      - Parametros de configuración plano xy
//      - Parametros de configuración eje z
//      - Niveles lógicos de enable del tmc2209
//      - Configuracion de steps y microstepping
//      - Configuracion del tablero en mm
//      - Configuracion de los brazos en mm
//      - Tipos de datos y definición de maquina de estados
//      - Estructuras de configuración de motores
// =======================================================================

#pragma once

#include <Arduino.h>

#define COMM Serial // Cambia a Serial1 si usas UART hardware en pines 0 y 1

// PINES DE CONFIGURACIÓN
// -----------------------------------------------------------------------
// Sensor1, Encoder1, Motor1
#define HALL_1 3
#define AS5600_1_SDA 4
#define AS5600_1_SCL 5
#define MOTOR1_ENABLE 6
#define MOTOR1_DIR 7
#define MOTOR1_STEP 8
// Sensor2, Encoder2, Motor2
#define HALL_2 15
#define AS5600_2_SDA 26
#define AS5600_2_SCL 27
#define MOTOR2_ENABLE 12
#define MOTOR2_DIR 13
#define MOTOR2_STEP 14
// Sensor3, Encoder3, Motor3
#define HALL_3 29
#define MOTOR3_ENABLE 9
#define MOTOR3_DIR 10
#define MOTOR3_STEP 11
// Pines de indicador LED y electroimán
#define LED 2
#define MAGNET_IN1 0
#define MAGNET_IN2 1
#define MAGNET_RELEASE_TIME 50 // ms

// PARAMETROS DE CONFIGURACIÓN PLANO XY
// -----------------------------------------------------------------------
#define AS5600_ADDR 0x36
#define BASE_SPEED 2 * 1500 // usada para igualar tiempo de llegada de motor1 y 2
// BASE_SPEED: velocidad máxima que tendrá el motor que recorre la mayor distancia
// ✔ suficientemente alta para que el movimiento no sea lento
// ✔ suficientemente baja para que ningún motor pierda pasos

// PARAMETROS DE CONFIGURACIÓN EJE Z
// -----------------------------------------------------------------------
<<<<<<< HEAD
constexpr float Z_GAME_SPEED = 55000.0f;        // velocidad durante el juego min.6000 max.55000
constexpr float Z_GAME_ACCELERATION = 30000.0f; // aceleracion durante el juego min.2000 max.30000
=======
constexpr float Z_GAME_SPEED = 40000.0f;        // velocidad durante el juego min.6000 max.55000 std.40000
constexpr float Z_GAME_ACCELERATION = 30000.0f; // aceleracion durante el juego min.2000 max.30000 std.30000
>>>>>>> 45b46657441ae6cbd08db367a57bb691757a59a4
#define Z_STEPS_DOWN 3300                       // cantidad de pasos desde el Sensor
                                                // hasta el punto mas bajo -> posicion de agarre
// #define Z_HOME_OFFSET 8000 / 4        // cantidad de pasos desde Sensor hast HOME -> posicion de referencia
// #define Z_TRAVEL_POS (-Z_HOME_OFFSET) // cantidad de pasos desde HOME hasta la posición de viaje
// para levantar la pieza (Z arriba)
#define Z_DELAY 100 // delay entre movimientos para darle tiempo al iman

// NIVELES LÓGICOS DE ENABLE DEL TMC2209
// -----------------------------------------------------------------------
constexpr bool ENABLE_ACTIVE = LOW; // Nivel lógico (LOW=ON, HIGH=OFF)
constexpr bool ENABLE_INACTIVE = HIGH;

// CONFIURACION DE STEPS Y MICROSTEPING
// -----------------------------------------------------------------------
constexpr int MOTOR_STEPS = 200;
constexpr int MOTOR1_MICROSTEPPING = 16;
constexpr int MOTOR2_MICROSTEPPING = 16;
constexpr int MOTOR3_MICROSTEPPING = 8;

// CONFIGURACION DEL TABLERO en MM
// -----------------------------------------------------------------------
constexpr float SQUARE_SIZE = 40.0f;                                  // Tamaño de casilla en mm
constexpr float OFFSET_X = -((3 * SQUARE_SIZE) + SQUARE_SIZE / 2.0f); // Distancia desde DOF1 a centro Fila A
constexpr float OFFSET_Y = 121.0f;                                    // Distancia desde DOF1 a centro Rango 1

// CONFIGURACION DE LOS BRAZOS EN MM
// -----------------------------------------------------------------------
constexpr float LINK1 = 285;
constexpr float LINK2 = 170;

// COORDENADAS FÍSICAS DE LA ZONA DE CAPTURA EN MM
// -----------------------------------------------------------------------
#define CAPTURE_BOARD_COLUMNS 5
#define CAPTURE_BOARD_ROWS 3
#define CAPTURE_BOARD_SLOTS 15

// Coordenadas X de las cinco columnas
constexpr float CAPTURE_X[CAPTURE_BOARD_COLUMNS] = {
    284.0f, 244.0f, 204.0f, 164.0f, 124.0f};

// Coordenadas Y de las tres filas
constexpr float CAPTURE_Y[CAPTURE_BOARD_ROWS] = {
    -40.0f, 0.0f, 40.0f};

// TIPOS DE DATOS Y DEFINICIÓN DE MAQUINA DE ESTADOS
// -----------------------------------------------------------------------
// Comandos recibidos por UART
enum class Command {
    STATUS,
    RESET,
    ANGLES,
    BOARD,
    COMMANDS,
    HOME,
    HOMING,
    MOVE,
    PICK,
    PLACE,
    REMOVE,
    SQUARE,
    CAPTURETEST,
    CAPTURERESET,
    MOTOROFF,
    UNKNOWN
};

// Asignacion de ID para motores
enum class MotorID {
    NONE,
    J1,
    J2,
    Z
};

// Maquina de estados de homing, motor1-2 (CW = ClockWise, CCW = CounterClockWise)
enum class HomingStateXY {
    INACTIVE,
    FIND_FIRST_EDGE_CW,
    FIND_SECOND_EDGE_CW,
    FIND_FIRST_EDGE_CCW,
    FIND_SECOND_EDGE_CCW,
    SEARCH_FAST_CW,
    SEARCH_FAST_CCW,
    REVERSE_EDGE_CW,
    REVERSE_EDGE_CCW,
    CALC_CENTER,
    MOVE_TO_CENTER,
    OK,
    ERROR
};

// Maquina de estados para el homing del motor3
enum class HomingStateZ {
    INACTIVE,
    CHECK_SENSOR,
    FIND_EDGE_DOWNWARD,
    FIND_EDGE_UPWARD,
    MOVE_TO_REFERENCE,
    OK,
    ERROR
};

// Máquina de estado para Homing de todos los motores
enum class HomeAllState {
    IDLE,
    MOTOR1,
    MOTOR2,
    MOTOR3,
    DONE
};

// Maquina de estado para Homing de motores individuales
enum class HomeSingleState {
    IDLE,
    RUNNING,
    DONE
};

// Maquina de estados para movimiento del plano XY
enum class MovingStateXY {
    IDLE,
    MOVING_TO_TARGET,
    SETTLING,
    CORRECTING,
    CORRECTION_DONE
};

// Maquina de estados para movimiento del eje Z
enum class MovingStateZ {
    IDLE,
    PICK_DOWN,
    PICK_GRIP,
    PICK_UP,
    PLACE_DOWN,
    PLACE_RELEASE,
    PLACE_UP
};

// Maquina de estados para secuencia de movimiento, captura, enrroque...
enum class MoveSequenceState {
    IDLE,
    MOVING_START,
    PICKING,
    MOVING_END,
    PLACING,
    CASTLING_ROOK_START,
    CASTLING_ROOK_PICKING,
    CASTLING_ROOK_END,
    CASTLING_ROOK_PLACING,
    CASTLING_WAIT_HOME, // esperar a que XY termine el regreso a HOME antes de confirmar el movimiento completo
    GO_HOME
};

// Maquina de estados para secuencia de captura completa
enum class CaptureSequenceState {
    IDLE,
    CAPTURE_START,
    PICKING_OPPONENT,
    TAKE_PIECE_OUT,
    PLACING_OPPONENT,
    MOVING_OWN_PIECE_START,
    PICKING_OWN_PIECE,
    MOVING_OWN_PIECE_END,
    PLACING_OWN_PIECE,
    GO_HOME,
    WAIT_HOME
};

// =======================================================================
// MÁQUINA DE ESTADOS PARA RECUPERACIÓN AUTOMÁTICA XY
// =======================================================================
enum class AutoRecoveryState {
    IDLE,
    START_J1,
    WAIT_J1,
    START_J2,
    WAIT_J2,
    DONE,
    ERROR
};

// ESTRUCTURAS DE CONFIGURACIÓN DE MOTORES
// -----------------------------------------------------------------------
struct MotorConfig {
    // Mecanica
    int microstepping;      // Microstepping del driver
    int reduction;          // Relación de reducción mecánica
    int stepsPerRevolution; // Pasos por revolución del motor
    int8_t motorDirection;  // Dirección fisica del motor/sensor / alineación del montaje

    // Homing
    float slowSpeed;       // Velocidad lenta durante homing
    float fastSpeed;       // Velocidad rápida durante homing
    long steps90Deg;       // Pasos equivalentes a 90°
    long stepsLimit;       // Límite máximo de pasos
    unsigned long timeout; // Tiempo máximo permitido en homing

    // Movimiento a coordenadas
    float baseSpeed;    // Velocidad máxima de referencia
    float acceleration; // Aceleración máxima

    // Pines
    int enablePin;
};

// Configuracion de Homing para cada motor, con parámetros mecánicos específicos
inline const MotorConfig motor1Config = {
    .microstepping = MOTOR1_MICROSTEPPING,
    .reduction = 9,
    .stepsPerRevolution = MOTOR_STEPS,
    .motorDirection = -1, // ‼️ -1 porque el motor/sensor esta fisicamente montado al revez
    .slowSpeed = 2000.0,
    .fastSpeed = 20000.0, // min.25000 max.55000
    .steps90Deg = MOTOR1_MICROSTEPPING * MOTOR_STEPS / 4,
    .stepsLimit = 0, // no existe para motor1
    .timeout = 15000,
    .baseSpeed = BASE_SPEED,
<<<<<<< HEAD
    .acceleration = 20000.0, // min.6000 max.20000
=======
    .acceleration = 10000.0, // min.6000 max.20000
>>>>>>> 45b46657441ae6cbd08db367a57bb691757a59a4
    .enablePin = MOTOR1_ENABLE};

inline const MotorConfig motor2Config = {
    .microstepping = MOTOR2_MICROSTEPPING,
    .reduction = 6,
    .stepsPerRevolution = MOTOR_STEPS,
    .motorDirection = 1,
    .slowSpeed = 1000.0,
    .fastSpeed = 20000.0, // min.20000 max.55000
    .steps90Deg = MOTOR2_MICROSTEPPING * MOTOR_STEPS / 4,
    .stepsLimit = 0, // no existe para motor2
    .timeout = 15000,
    .baseSpeed = BASE_SPEED,
<<<<<<< HEAD
    .acceleration = 20000.0, // min.6000 max.20000
=======
    .acceleration = 10000.0, // min.6000 max.25000
>>>>>>> 45b46657441ae6cbd08db367a57bb691757a59a4
    .enablePin = MOTOR2_ENABLE};

inline const MotorConfig motor3Config = {
    .microstepping = MOTOR3_MICROSTEPPING,
    .reduction = 2, // Reducción mecánica 2:1. Referencial: no aplicada al cálculo de pasos del eje Z.
    .stepsPerRevolution = 200,
    .motorDirection = 1,
    .slowSpeed = 1000.0,
    .fastSpeed = Z_GAME_SPEED,
    .steps90Deg = 0,     // no existe para motor3
    .stepsLimit = -9000, // pasos máximos si arranca fuera del imán (solo motor3)
    .timeout = 12000,
    .baseSpeed = BASE_SPEED,
    .acceleration = Z_GAME_ACCELERATION,
    .enablePin = MOTOR3_ENABLE};