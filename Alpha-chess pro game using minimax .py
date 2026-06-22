import pygame
import chess
import random

WIDTH, HEIGHT = 640, 640
SQUARE = WIDTH // 8

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)

GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

# AI settings
AI_COLOR = chess.BLACK  # AI plays black, you play white
SEARCH_DEPTH = 2  # 2-3 is good. 3 = slower but smarter

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Alpha Chess Master PRO vs AI")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 40)

# Load sounds
pygame.mixer.init()
try:
    move_sound = pygame.mixer.Sound("move.wav")  # put move.wav in same folder
    check_sound = pygame.mixer.Sound("check.wav")  # put check.wav in same folder
except:
    move_sound = check_sound = None  # no sound if files missing

board = chess.Board()

# state of moves
dragging = False
drag_square = None
legal_moves = []

selected_square = None
last_move = None

mouse_x, mouse_y = 0, 0
ai_thinking = False

def to_square(pos):
    x, y = pos
    col = x // SQUARE
    row = y // SQUARE
    return chess.square(col, 7 - row)

def get_legal_targets(square):
    return [m.to_square for m in board.legal_moves if m.from_square == square]

def play_sound(move):
    if move_sound and check_sound:
        if board.is_check():
            check_sound.play()
        else:
            move_sound.play()

# ========== MINIMAX AI ==========
piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

def evaluate_board(b):
    if b.is_checkmate():
        return -99999 if b.turn == AI_COLOR else 99999
    if b.is_stalemate() or b.is_insufficient_material():
        return 0
    
    score = 0
    for square in chess.SQUARES:
        piece = b.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            score += value if piece.color == AI_COLOR else -value
    return score

def minimax(b, depth, alpha, beta, maximizing):
    if depth == 0 or b.is_game_over():
        return evaluate_board(b), None
    
    best_move = None
    if maximizing:
        max_eval = -float('inf')
        for move in b.legal_moves:
            b.push(move)
            eval_score, _ = minimax(b, depth - 1, alpha, beta, False)
            b.pop()
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in b.legal_moves:
            b.push(move)
            eval_score, _ = minimax(b, depth - 1, alpha, beta, True)
            b.pop()
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def ai_move():
    global last_move, ai_thinking
    ai_thinking = True
    pygame.display.set_caption("Alpha Chess Master PRO - AI Thinking...")
    
    _, best = minimax(board, SEARCH_DEPTH, -float('inf'), float('inf'), True)
    
    if best:
        board.push(best)
        last_move = best
        play_sound(best)
    
    ai_thinking = False
    pygame.display.set_caption("Alpha Chess Master PRO vs AI")

# for draw board
def draw_board():
    for r in range(8):
        for c in range(8):
            color = LIGHT if (r + c) % 2 == 0 else DARK
            pygame.draw.rect(screen, color, (c * SQUARE, r * SQUARE, SQUARE, SQUARE))

def draw_last_move():
    if last_move:
        for sq in [last_move.from_square, last_move.to_square]:
            r = 7 - chess.square_rank(sq)
            c = chess.square_file(sq)
            pygame.draw.rect(screen, YELLOW, (c * SQUARE, r * SQUARE, SQUARE, SQUARE), 4)

def draw_check():
    if board.is_check():
        king_square = board.king(board.turn)
        r = 7 - chess.square_rank(king_square)
        c = chess.square_file(king_square)
        pygame.draw.rect(screen, RED, (c * SQUARE, r * SQUARE, SQUARE, SQUARE), 5)

def draw_pieces():
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            if dragging and square == drag_square:
                continue
            r = 7 - chess.square_rank(square)
            c = chess.square_file(square)
            color = (255, 255, 255) if piece.color == chess.WHITE else (0, 0, 0)
            text = font.render(piece.symbol(), True, color)
            screen.blit(text, (c * SQUARE + 15, r * SQUARE + 5))

def draw_legal_moves():
    for sq in legal_moves:
        r = 7 - chess.square_rank(sq)
        c = chess.square_file(sq)
        pygame.draw.circle(screen, GREEN, (c * SQUARE + SQUARE // 2, r * SQUARE + SQUARE // 2), 10)

def draw_drag():
    if dragging and drag_square is not None:
        piece = board.piece_at(drag_square)
        if piece:
            color = (255, 255, 255) if piece.color == chess.WHITE else (0, 0, 0)
            text = font.render(piece.symbol(), True, color)
            screen.blit(text, (mouse_x - 20, mouse_y - 20))

def make_move(start, end):
    global last_move
    move = chess.Move(start, end)

    piece = board.piece_at(start)
    if piece and piece.piece_type == chess.PAWN:
        if chess.square_rank(end) in [0, 7]:
            move = chess.Move(start, end, promotion=chess.QUEEN)

    if move in board.legal_moves:
        board.push(move)
        last_move = move
        play_sound(move)
        return True
    return False

# main game loop
running = True

while running:
    screen.fill((0, 0, 0))

    draw_board()
    draw_last_move()
    draw_legal_moves()
    draw_check()
    draw_pieces()
    draw_drag()

    # Show "AI Thinking" text
    if ai_thinking:
        text = pygame.font.SysFont("Arial", 30).render("AI Thinking...", True, RED)
        screen.blit(text, (WIDTH//2 - 80, 10))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Only allow human move when it's white's turn and AI not thinking
        elif event.type == pygame.MOUSEBUTTONDOWN and board.turn == chess.WHITE and not ai_thinking:
            sq = to_square(pygame.mouse.get_pos())
            piece = board.piece_at(sq)
            if piece and piece.color == chess.WHITE:
                dragging = True
                drag_square = sq
                selected_square = sq
                legal_moves = get_legal_targets(sq)

        elif event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = pygame.mouse.get_pos()

        elif event.type == pygame.MOUSEBUTTONUP and dragging and board.turn == chess.WHITE and not ai_thinking:
            end_sq = to_square(pygame.mouse.get_pos())
            if drag_square is not None:
                if make_move(drag_square, end_sq):
                    # After human move, trigger AI move
                    pygame.time.wait(300)  # small delay
                    ai_move()
            dragging = False
            drag_square = None
            legal_moves = []

    pygame.display.flip()
    clock.tick(60)

    # Check game over
    if board.is_game_over():
        result = "Checkmate! " + ("AI Wins" if board.turn == chess.WHITE else "You Win!")
        print(result)
        pygame.display.set_caption(f"Game Over - {result}")
        pygame.time.wait(3000)
        running = False

pygame.quit()