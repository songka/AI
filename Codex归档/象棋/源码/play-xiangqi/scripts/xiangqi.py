#!/usr/bin/env python3
"""Render Xiangqi FEN and validate/apply one UCCI move. Standard library only."""
import argparse
import sys

START = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w"
GLYPH = {
    "r":"車","n":"馬","b":"象","a":"士","k":"將","c":"砲","p":"卒",
    "R":"俥","N":"傌","B":"相","A":"仕","K":"帥","C":"炮","P":"兵",
}

def parse_fen(fen):
    parts = fen.strip().split()
    rows = parts[0].split("/")
    if len(rows) != 10:
        raise ValueError("FEN must contain 10 ranks")
    board = []
    for row in rows:
        out = []
        for ch in row:
            out.extend([None] * int(ch) if ch.isdigit() else [ch])
        if len(out) != 9 or any(x and x not in GLYPH for x in out):
            raise ValueError("each FEN rank must contain 9 valid squares")
        board.append(out)
    side = parts[1].lower() if len(parts) > 1 else "w"
    if side not in ("w", "b", "r"):
        raise ValueError("side to move must be w/r or b")
    return board, "w" if side == "r" else side

def make_fen(board, side):
    rows = []
    for row in board:
        s, gap = "", 0
        for p in row:
            if p is None: gap += 1
            else:
                if gap: s += str(gap); gap = 0
                s += p
        rows.append(s + (str(gap) if gap else ""))
    return "/".join(rows) + " " + side

def render(board):
    lines = ["    a  b  c  d  e  f  g  h  i"]
    for y, row in enumerate(board):
        lines.append(f" {y}  " + "  ".join(GLYPH.get(p, "·") for p in row) + f"  {y}")
        if y == 4: lines.append("    楚 河       漢 界")
    lines.append("    a  b  c  d  e  f  g  h  i")
    return "\n".join(lines)

def red(p): return p is not None and p.isupper()
def own(p, side): return p is not None and red(p) == (side == "w")
def inside(x, y): return 0 <= x < 9 and 0 <= y < 10
def clear_line(b, x1, y1, x2, y2):
    dx = (x2 > x1) - (x2 < x1); dy = (y2 > y1) - (y2 < y1)
    x, y, n = x1 + dx, y1 + dy, 0
    while (x, y) != (x2, y2):
        if b[y][x] is not None: n += 1
        x += dx; y += dy
    return n

def piece_ok(b, p, x1, y1, x2, y2, capture):
    dx, dy, adx, ady = x2-x1, y2-y1, abs(x2-x1), abs(y2-y1)
    t = p.lower(); is_red = red(p)
    if t == "r": return (dx == 0 or dy == 0) and clear_line(b,x1,y1,x2,y2) == 0
    if t == "c": return (dx == 0 or dy == 0) and clear_line(b,x1,y1,x2,y2) == (1 if capture else 0)
    if t == "n":
        if sorted((adx,ady)) != [1,2]: return False
        leg = (x1 + (dx//2 if adx == 2 else 0), y1 + (dy//2 if ady == 2 else 0))
        return b[leg[1]][leg[0]] is None
    if t == "b":
        home = y2 >= 5 if is_red else y2 <= 4
        return adx == ady == 2 and home and b[(y1+y2)//2][(x1+x2)//2] is None
    if t == "a":
        palace = 3 <= x2 <= 5 and (7 <= y2 <= 9 if is_red else 0 <= y2 <= 2)
        return adx == ady == 1 and palace
    if t == "k":
        palace = 3 <= x2 <= 5 and (7 <= y2 <= 9 if is_red else 0 <= y2 <= 2)
        return adx + ady == 1 and palace
    if t == "p":
        forward = -1 if is_red else 1
        crossed = y1 <= 4 if is_red else y1 >= 5
        return (dx == 0 and dy == forward) or (crossed and adx == 1 and dy == 0)
    return False

def attacks(b, side, tx, ty):
    for y in range(10):
        for x in range(9):
            p = b[y][x]
            if own(p, side) and piece_ok(b,p,x,y,tx,ty,b[ty][tx] is not None): return True
    return False

def in_check(b, side):
    king = "K" if side == "w" else "k"
    pos = next(((x,y) for y in range(10) for x in range(9) if b[y][x] == king), None)
    if pos is None: return True
    x, y = pos
    # Flying generals are naturally a rook-like line attack, but kings otherwise move one square.
    enemy = "k" if side == "w" else "K"
    for yy in range(10):
        if b[yy][x] == enemy and clear_line(b,x,y,x,yy) == 0: return True
    return attacks(b, "b" if side == "w" else "w", x, y)

def apply_move(b, side, mv):
    if len(mv) != 4 or mv[0] not in "abcdefghi" or mv[2] not in "abcdefghi" or mv[1] not in "0123456789" or mv[3] not in "0123456789":
        raise ValueError("move must use UCCI form such as h2e2")
    x1,y1,x2,y2 = ord(mv[0])-97,int(mv[1]),ord(mv[2])-97,int(mv[3])
    p, q = b[y1][x1], b[y2][x2]
    if not own(p, side): raise ValueError("origin does not contain a piece of the side to move")
    if own(q, side): raise ValueError("destination contains a friendly piece")
    if not piece_ok(b,p,x1,y1,x2,y2,q is not None): raise ValueError("piece movement or path is illegal")
    out = [row[:] for row in b]; out[y2][x2], out[y1][x1] = p, None
    if in_check(out, side): raise ValueError("move leaves own general in check or exposes flying generals")
    return out

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("show","move"):
        p = sub.add_parser(name); p.add_argument("--fen", default=START)
        if name == "move": p.add_argument("--move", required=True)
    a = ap.parse_args()
    try:
        b, side = parse_fen(a.fen)
        if a.cmd == "move": b = apply_move(b,side,a.move.lower()); side = "b" if side == "w" else "w"
        print(make_fen(b,side)); print(render(b)); print("红方走" if side == "w" else "黑方走")
    except ValueError as e:
        print(f"非法：{e}", file=sys.stderr); return 2
    return 0

if __name__ == "__main__": raise SystemExit(main())
