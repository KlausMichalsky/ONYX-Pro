# =======================================================================
#                         🔹 O N Y X - P R O 🔹
# =======================================================================
#  Archivo   : game.py
#  Autor     : Klaus Michalsky
#  Fecha     : Oct-2026
# -----------------------------------------------------------------------
#  ▫️ DESCRIPCIÓN
#     - Reglas, jugadas, coordenadas y detección de jugadas humanas.
#     - Gestión del tablero de ajedrez
#     - Validación de jugadas humanas
#     - Gestión de movimientos
#     - Detección de capturas
#     - Detección del final de partida
# =======================================================================

import chess


# =========================
# GAME INIT
# =========================

def create_board():
    return chess.Board()  # devuelve un objeto Board de la librería chess


def create_move(move_uci):
    # recibe una jugada en formato texto UCI
    # y la convierte en un objeto Move de python-chess
    return chess.Move.from_uci(move_uci)


# =========================
# HUMAN MOVE
# =========================

def validate_human_move(board, move_uci):
    # recibe un objeto Board y un string move_uci
    # y devuelve un objeto Move de la librería chess
    # si la jugada es legal,
    move = chess.Move.from_uci(move_uci)

    if move not in board.legal_moves:
        return None

    return move


def push_move(board, move):
    # recibe un objeto Board y un objeto Move
    # actualiza el estado del tablero
    board.push(move)


# =========================
# CAPTURE
# =========================

def is_capture(board, move):
    # recibe un objeto Board y un objeto Move
    # y devuelve True si la jugada es una captura,
    # False en caso contrario
    return board.is_capture(move)


def get_capture_squares(board, move):
    """
    Obtiene la casilla de la pieza capturada y la casilla de origen.

    En una captura al paso, la pieza capturada no está
    en la casilla de destino, sino detrás de ella.
    """

    capture_square_index = move.to_square

    if board.is_en_passant(move):

        if board.turn == chess.WHITE:
            capture_square_index -= 8
        else:
            capture_square_index += 8

    capture_square = chess.square_name(capture_square_index)
    from_square = chess.square_name(move.from_square)

    return capture_square, from_square


# =========================
# GAME OVER
# =========================

def is_game_over(board):
    # recibe un objeto Board
    # y devuelve True si la partida ha terminado,
    # False en caso contrario
    return board.is_game_over()


def get_result(board):
    # recibe un objeto Board
    # y devuelve el resultado de la partida en formato string
    return board.result()


def mirror_square(square):
    # square[0] Obtiene el primer carácter de la casilla
    # ord(square[0]) Obtiene el valor ASCII del primer carácter
    # ord("a") → 97, ord("e") → 101, ord("h") → 104
    # ord(square[0]) - ord("a") calcula cuántas posiciones hay desde la columna A. Para E, esto sería 4.
    # ord("h") - (ord(square[0]) - ord("a")) calcula la columna espejo. Para E, esto sería 104 - 4 = 100, que es la letra D.
    # chr(...) convierte el valor ASCII de vuelta a un carácter. Para 100, esto sería "d".
    file = chr(ord("h") - (ord(square[0]) - ord("a")))
    # similar para el rango, pero en lugar de usar valores ASCII,
    # usamos la posición numérica de la fila.
    rank = str(9 - int(square[1]))
    # devuelve la casilla espejo en formato UCI
    return file + rank


def mirror_move(move_uci):  # recibe una jugada en formato UCI
    # Dame los caracteres desde el principio hasta la posición 2, sin incluir la posición 2
    from_square = move_uci[:2]
    # caracteres desde el índice 2 hasta el 4, sin incluir el 4
    to_square = move_uci[2:4]
    promotion = move_uci[4:]  # caracteres desde el índice 4 hasta el final

    # aqui en el return de abajo la función mirror_square() se ejecuta dos veces:
    # devuelve la jugada espejo en formato UCI
    return mirror_square(from_square) + mirror_square(to_square) + promotion


def sensor_occupancy_from_board(board, mirror_coordinates=False):
    """Convierte la posición de ajedrez en el estado esperado de los sensores."""
    occupancy = {}

    for square_index in chess.SQUARES:
        square = chess.square_name(square_index)

        if mirror_coordinates:
            square = mirror_square(square)

        occupancy[square.upper()] = (
            board.piece_at(square_index) is not None
        )

    return occupancy


def detect_human_move(
    board,
    initial_state,
    current_state,
    change_history,
    mirror_coordinates=False,
):
    """
    Identifica la jugada legal que corresponde al estado final del tablero.

    Devuelve la jugada en coordenadas lógicas UCI.
    Lanza ValueError si no hay una única jugada identificable.
    """

    # Normalizar las coordenadas recibidas de los sensores.
    initial = {
        square.upper(): bool(occupied)
        for square, occupied in initial_state.items()
    }

    current = {
        square.upper(): bool(occupied)
        for square, occupied in current_state.items()
    }

    # Comprobar que tenemos los 64 sensores.
    if len(initial) != 64 or len(current) != 64:
        raise ValueError("Faltan datos de uno o más sensores.")

    # El tablero inicial debe coincidir con la partida actual.
    expected_initial = sensor_occupancy_from_board(
        board, mirror_coordinates
    )

    if initial != expected_initial:
        raise ValueError(
            "Los sensores no coinciden con la posición actual del juego."
        )

    # Registrar las casillas que quedaron vacías temporalmente.
    emptied_squares = {
        square.upper()
        for square, occupied in change_history
        if not occupied
    }

    candidates = []

    # Probar todas las jugadas legales.
    for move in board.legal_moves:
        physical_move = (
            mirror_move(move.uci())
            if mirror_coordinates
            else move.uci()
        )

        destination = physical_move[2:4].upper()

        # Una captura necesita haber vaciado temporalmente el destino
        # si este estaba ocupado al principio y sigue ocupado al final.
        if (
            initial[destination]
            and current[destination]
            and destination not in emptied_squares
        ):
            continue

        # Calcular cómo quedaría el tablero con esa jugada.
        test_board = board.copy()
        test_board.push(move)

        expected_final = sensor_occupancy_from_board(
            test_board, mirror_coordinates
        )

        if expected_final == current:
            candidates.append(move.uci())

    if len(candidates) == 0:
        raise ValueError(
            "No se pudo identificar una jugada legal con el estado final."
        )

    if len(candidates) > 1:
        raise ValueError(
            "Jugada ambigua. Candidatas: " + ", ".join(candidates)
        )

    return candidates[0]


def process_human_move(
    board,
    confirmed_state,
    current_state,
    change_history,
    mirror_coordinates=False,
):
    """Identifica y valida una jugada humana sin modificar el tablero."""

    logical_move = detect_human_move(
        board,
        confirmed_state,
        current_state,
        change_history,
        mirror_coordinates,
    )

    human_move = validate_human_move(board, logical_move)

    if human_move is None:
        raise ValueError("Jugada ilegal. Corregí las piezas.")

    return logical_move, human_move


def prepare_robot_move(board, stockfish_move, mirror_coordinates=False):
    """Prepara la jugada física y los datos necesarios para una captura."""

    move = create_move(stockfish_move)

    robot_move = (
        mirror_move(stockfish_move)
        if mirror_coordinates
        else stockfish_move
    )

    capture_square = None
    from_square = None

    if is_capture(board, move):
        capture_square, from_square = get_capture_squares(board, move)

        if mirror_coordinates:
            capture_square = mirror_square(capture_square)
            from_square = mirror_square(from_square)

    return move, robot_move, capture_square, from_square
