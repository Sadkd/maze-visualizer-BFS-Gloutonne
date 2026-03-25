"""
Labyrinthe — BFS vs Recherche Gloutonne
Dépendance : python -m pip install pygame
Lancement   : python maze_pygame.py
"""

import pygame
import random
import heapq
import math
from collections import deque

# ─── Palette de Couleurs "Soft Light" (Pas de noir) ──────────────────────────
BG          = (245, 247, 250)  # Gris très clair bleuté
WALL        = (180, 188, 201)  # Gris moyen froid
FLOOR       = (255, 255, 255)  # Blanc pur
PLAYER      = (55, 138, 221)
PLAYER_EYE  = (230, 241, 251)
EXIT_COLOR  = (99, 153, 34)

# Couleurs des algos (plus saturées pour le mode clair)
BFS_EXP     = (93, 202, 165, 60)   # Vert translucide
BFS_PATH    = (45, 156, 118)
GREEDY_EXP  = (155, 145, 235, 70)  # Violet translucide
GREEDY_PATH = (214, 91, 153)

TEXT_MAIN   = (45, 55, 72)         # Gris anthracite (pas noir)
TEXT_MUTED  = (113, 128, 150)
PANEL_BG    = (232, 236, 241)
PANEL_BOR   = (203, 213, 224)
TAB_ACTIVE  = (255, 255, 255)      # Blanc pour l'élément sélectionné
TAB_HOVER   = (222, 228, 235)
STAT_BFS    = (38, 115, 90)
STAT_GRE    = (140, 60, 100)

# ─── Constantes ──────────────────────────────────────────────────────────────
WIN_W, WIN_H   = 960, 700
PANEL_W        = 280
SIZES          = [("Petit 11×11", 11), ("Moyen 21×21", 21), ("Grand 31×31", 31)]
ALGOS          = ["BFS", "Glouton", "Comparer"]
ANIM_SPEED     = 6 

# ─── Fonctions Logiques (Inchangées) ─────────────────────────────────────────
def generate_maze(n):
    maze = [[1] * n for _ in range(n)]
    def carve(r, c):
        maze[r][c] = 0
        dirs = [(0,2),(0,-2),(2,0),(-2,0)]
        random.shuffle(dirs)
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if 0 < nr < n-1 and 0 < nc < n-1 and maze[nr][nc] == 1:
                maze[r+dr//2][c+dc//2] = 0
                carve(nr, nc)
    carve(1, 1)
    return maze

def bfs(maze, start, end):
    n = len(maze)
    queue = deque([start])
    visited = {start}
    parent = {start: None}
    explored = []
    while queue:
        r, c = queue.popleft()
        explored.append((r, c))
        if (r, c) == end:
            path = []; cur = end
            while cur: path.append(cur); cur = parent[cur]
            return list(reversed(path)), explored
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < n and 0 <= nc < n and maze[nr][nc] == 0 and (nr,nc) not in visited:
                visited.add((nr,nc)); parent[(nr,nc)] = (r,c); queue.append((nr,nc))
    return [], explored

def greedy(maze, start, end):
    n = len(maze)
    def h(r, c): return abs(r - end[0]) + abs(c - end[1])
    heap = [(h(*start), start)]; visited = {start}; parent = {start: None}; explored = []
    while heap:
        _, (r, c) = heapq.heappop(heap)
        explored.append((r, c))
        if (r, c) == end:
            path = []; cur = end
            while cur: path.append(cur); cur = parent[cur]
            return list(reversed(path)), explored
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < n and 0 <= nc < n and maze[nr][nc] == 0 and (nr,nc) not in visited:
                visited.add((nr,nc)); parent[(nr,nc)] = (r,c); heapq.heappush(heap, (h(nr,nc), (nr,nc)))
    return [], explored

# ─── Classe Principale ───────────────────────────────────────────────────────
class MazeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Labyrinthe — Visualiseur Académique")
        self.clock = pygame.time.Clock()

        # Polices (UI plus propre)
        self.font_title  = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_body   = pygame.font.SysFont("Segoe UI", 13)
        self.font_small  = pygame.font.SysFont("Segoe UI", 11, bold=True)
        self.font_stat   = pygame.font.SysFont("Consolas", 20, bold=True)

        self.size_idx = 1
        self.algo_idx = 0
        self.new_maze()

    def new_maze(self):
        self.n = SIZES[self.size_idx][1]
        self.maze = generate_maze(self.n)
        self.start, self.end = (1, 1), (self.n-2, self.n-2)
        self.player = list(self.start)
        self.steps = 0; self.won = False; self.msg = ""
        self.bfs_path = []; self.bfs_exp = []; self.gr_path = []; self.gr_exp = []
        self.anim_bfs = []; self.anim_gr = []; self.anim_idx = 0
        self.animating = False; self.show_bfs_path = False; self.show_gr_path = False
        self._compute_cell()

    def _compute_cell(self):
        max_w, max_h = WIN_W - PANEL_W - 60, WIN_H - 100
        self.cell = min(max_w // self.n, max_h // self.n)
        self.maze_px_w = self.n * self.cell
        self.maze_px_h = self.n * self.cell
        self.maze_ox = PANEL_W + (WIN_W - PANEL_W - self.maze_px_w) // 2
        self.maze_oy = (WIN_H - self.maze_px_h) // 2

    def solve(self):
        self.animating = True; self.anim_idx = 0; self.msg = "Calcul en cours..."
        algo = ALGOS[self.algo_idx]
        if algo in ("BFS", "Comparer"):
            self.bfs_path, self.bfs_exp = bfs(self.maze, self.start, self.end)
            self.anim_bfs = self.bfs_exp[:]
        if algo in ("Glouton", "Comparer"):
            self.gr_path, self.gr_exp = greedy(self.maze, self.start, self.end)
            self.anim_gr = self.gr_exp[:]

    def update_anim(self):
        if not self.animating: return
        total = max(len(self.anim_bfs), len(self.anim_gr))
        for _ in range(ANIM_SPEED):
            if self.anim_idx < total: self.anim_idx += 1
            else:
                self.animating = False
                self.show_bfs_path = bool(self.bfs_path); self.show_gr_path = bool(self.gr_path)
                self.msg = "Simulation terminée"
                break

    def move(self, dr, dc):
        if self.won: return
        nr, nc = self.player[0]+dr, self.player[1]+dc
        if 0 <= nr < self.n and 0 <= nc < self.n and self.maze[nr][nc] == 0:
            self.player = [nr, nc]; self.steps += 1
            if (nr, nc) == self.end: self.won = True; self.msg = "Arrivée atteinte !"

    def draw_maze(self):
        ox, oy, cell = self.maze_ox, self.maze_oy, self.cell
        # Ombre portée du labyrinthe
        pygame.draw.rect(self.screen, (220, 225, 232), (ox+4, oy+4, self.maze_px_w, self.maze_px_h), border_radius=4)
        pygame.draw.rect(self.screen, WALL, (ox, oy, self.maze_px_w, self.maze_px_h), border_radius=4)

        for r in range(self.n):
            for c in range(self.n):
                if self.maze[r][c] == 0:
                    pygame.draw.rect(self.screen, FLOOR, (ox+c*cell, oy+r*cell, cell, cell))

        # Exploration
        limit = self.anim_idx
        for res_exp, color in [(self.anim_bfs, BFS_EXP), (self.anim_gr, GREEDY_EXP)]:
            if res_exp:
                surf = pygame.Surface((cell, cell), pygame.SRCALPHA)
                surf.fill(color)
                for i, (r, c) in enumerate(res_exp[:limit]):
                    if (r,c) not in (self.start, self.end):
                        self.screen.blit(surf, (ox+c*cell, oy+r*cell))

        # Chemins
        for show, path, color in [(self.show_bfs_path, self.bfs_path, BFS_PATH), (self.show_gr_path, self.gr_path, GREEDY_PATH)]:
            if show:
                for r, c in path:
                    if (r,c) not in (self.start, self.end):
                        p = max(1, cell//4)
                        pygame.draw.rect(self.screen, color, (ox+c*cell+p, oy+r*cell+p, cell-2*p, cell-2*p), border_radius=2)

        # Sortie
        er, ec = self.end
        pygame.draw.rect(self.screen, EXIT_COLOR, (ox+ec*cell+2, oy+er*cell+2, cell-4, cell-4), border_radius=3)
        
        # Joueur
        pr, pc = self.player
        pygame.draw.circle(self.screen, PLAYER, (ox+pc*cell+cell//2, oy+pr*cell+cell//2), max(2, cell//2-2))

    def draw_panel(self):
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, PANEL_W, WIN_H))
        pygame.draw.line(self.screen, PANEL_BOR, (PANEL_W, 0), (PANEL_W, WIN_H), 1)

        x, y = 20, 30
        title = self.font_title.render("EXPLORATEUR IA", True, TEXT_MAIN)
        self.screen.blit(title, (x, y)); y += 40

        # Section Tailles
        lbl = self.font_small.render("DIMENSIONS", True, TEXT_MUTED)
        self.screen.blit(lbl, (x, y)); y += 20
        self.size_rects = []
        for i, (label, _) in enumerate(SIZES):
            rect = pygame.Rect(x, y, PANEL_W-40, 28)
            bg = TAB_ACTIVE if i == self.size_idx else PANEL_BG
            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            if i == self.size_idx: pygame.draw.rect(self.screen, PANEL_BOR, rect, 1, border_radius=6)
            txt = self.font_body.render(label, True, TEXT_MAIN if i == self.size_idx else TEXT_MUTED)
            self.screen.blit(txt, (x+10, y+5))
            self.size_rects.append(rect); y += 32
        
        y += 10
        # Section Algos
        lbl = self.font_small.render("ALGORITHME", True, TEXT_MUTED)
        self.screen.blit(lbl, (x, y)); y += 20
        self.algo_rects = []
        for i, label in enumerate(ALGOS):
            rect = pygame.Rect(x, y, PANEL_W-40, 28)
            bg = TAB_ACTIVE if i == self.algo_idx else PANEL_BG
            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            if i == self.algo_idx: pygame.draw.rect(self.screen, PANEL_BOR, rect, 1, border_radius=6)
            txt = self.font_body.render(label, True, TEXT_MAIN if i == self.algo_idx else TEXT_MUTED)
            self.screen.blit(txt, (x+10, y+5))
            self.algo_rects.append(rect); y += 32

        # Bouton Action
        y += 20
        self.btn_solve = pygame.Rect(x, y, PANEL_W-40, 40)
        pygame.draw.rect(self.screen, PLAYER, self.btn_solve, border_radius=8)
        txt = self.font_title.render("RÉSOUDRE", True, FLOOR)
        self.screen.blit(txt, (self.btn_solve.centerx - txt.get_width()//2, y+10))

        # Stats (bas de page)
        y = WIN_H - 240
        pygame.draw.line(self.screen, PANEL_BOR, (x, y), (PANEL_W-x, y)); y += 15
        for label, val, col in [("BFS Explorés", len(self.bfs_exp), STAT_BFS), 
                                ("Glouton Explorés", len(self.gr_exp), STAT_GRE),
                                ("Étapes Joueur", self.steps, TEXT_MAIN)]:
            lbl = self.font_small.render(label.upper(), True, TEXT_MUTED)
            self.screen.blit(lbl, (x, y))
            val_txt = self.font_stat.render(str(val) if val > 0 else "0", True, col)
            self.screen.blit(val_txt, (PANEL_W - val_txt.get_width() - 25, y-5))
            y += 35

    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            self.screen.fill(BG)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    for i, r in enumerate(self.size_rects):
                        if r.collidepoint(pos): self.size_idx = i; self.new_maze()
                    for i, r in enumerate(self.algo_rects):
                        if r.collidepoint(pos): self.algo_idx = i
                    if self.btn_solve.collidepoint(pos): self.solve()
                elif event.type == pygame.KEYDOWN:
                    keys = {pygame.K_UP:(-1,0), pygame.K_DOWN:(1,0), pygame.K_LEFT:(0,-1), pygame.K_RIGHT:(0,1)}
                    if event.key in keys: self.move(*keys[event.key])

            self.update_anim()
            self.draw_panel()
            self.draw_maze()
            
            # Message en bas
            if self.msg:
                m = self.font_body.render(self.msg, True, TEXT_MAIN)
                self.screen.blit(m, (PANEL_W + 20, WIN_H - 35))

            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    game = MazeGame()
    game.run()