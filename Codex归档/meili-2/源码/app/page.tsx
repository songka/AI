"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const SIZE = 15;
type Stone = "black" | "white";
type Cell = Stone | null;
type Move = { row: number; col: number; color: Stone };
type Mode = "ai" | "friend";

const emptyBoard = (): Cell[][] =>
  Array.from({ length: SIZE }, () => Array<Cell>(SIZE).fill(null));

const other = (color: Stone): Stone => (color === "black" ? "white" : "black");

function hasFive(board: Cell[][], row: number, col: number, color: Stone) {
  return [[1, 0], [0, 1], [1, 1], [1, -1]].some(([dr, dc]) => {
    let count = 1;
    for (const sign of [-1, 1]) {
      let r = row + dr * sign;
      let c = col + dc * sign;
      while (r >= 0 && r < SIZE && c >= 0 && c < SIZE && board[r][c] === color) {
        count += 1;
        r += dr * sign;
        c += dc * sign;
      }
    }
    return count >= 5;
  });
}

function lineScore(board: Cell[][], row: number, col: number, color: Stone) {
  const weights = [0, 8, 55, 420, 5000, 100000];
  let total = 0;
  for (const [dr, dc] of [[1, 0], [0, 1], [1, 1], [1, -1]]) {
    let count = 1;
    let open = 0;
    for (const sign of [-1, 1]) {
      let r = row + dr * sign;
      let c = col + dc * sign;
      while (r >= 0 && r < SIZE && c >= 0 && c < SIZE && board[r][c] === color) {
        count += 1;
        r += dr * sign;
        c += dc * sign;
      }
      if (r >= 0 && r < SIZE && c >= 0 && c < SIZE && board[r][c] === null) open += 1;
    }
    total += weights[Math.min(count, 5)] * (open === 2 ? 1.8 : open === 1 ? 1 : 0.1);
  }
  return total;
}

function chooseAiMove(board: Cell[][], ai: Stone) {
  let best: { row: number; col: number; score: number } | null = null;
  const human = other(ai);
  const hasStone = board.some((row) => row.some(Boolean));
  if (!hasStone) return { row: 7, col: 7 };

  for (let row = 0; row < SIZE; row += 1) {
    for (let col = 0; col < SIZE; col += 1) {
      if (board[row][col]) continue;
      let nearby = false;
      for (let dr = -2; dr <= 2 && !nearby; dr += 1) {
        for (let dc = -2; dc <= 2; dc += 1) {
          if (board[row + dr]?.[col + dc]) { nearby = true; break; }
        }
      }
      if (!nearby) continue;
      board[row][col] = ai;
      const win = hasFive(board, row, col, ai);
      const attack = lineScore(board, row, col, ai);
      board[row][col] = human;
      const block = hasFive(board, row, col, human);
      const defend = lineScore(board, row, col, human);
      board[row][col] = null;
      const centerBias = 14 - (Math.abs(row - 7) + Math.abs(col - 7));
      const score = win ? 1e9 : block ? 5e8 : attack + defend * 1.16 + centerBias + Math.random() * 3;
      if (!best || score > best.score) best = { row, col, score };
    }
  }
  return best ? { row: best.row, col: best.col } : { row: 7, col: 7 };
}

export default function Home() {
  const [board, setBoard] = useState<Cell[][]>(emptyBoard);
  const [history, setHistory] = useState<Move[]>([]);
  const [turn, setTurn] = useState<Stone>("black");
  const [winner, setWinner] = useState<Stone | "draw" | null>(null);
  const [mode, setMode] = useState<Mode>("ai");
  const [humanFirst, setHumanFirst] = useState(true);
  const [thinking, setThinking] = useState(false);

  const humanColor: Stone = humanFirst ? "black" : "white";
  const aiColor: Stone = other(humanColor);

  const reset = useCallback(() => {
    setBoard(emptyBoard());
    setHistory([]);
    setTurn("black");
    setWinner(null);
    setThinking(false);
  }, []);

  const placeStone = useCallback((row: number, col: number, color: Stone) => {
    setBoard((current) => {
      if (current[row][col]) return current;
      const next = current.map((line) => [...line]);
      next[row][col] = color;
      const won = hasFive(next, row, col, color);
      setHistory((moves) => [...moves, { row, col, color }]);
      if (won) setWinner(color);
      else if (next.every((line) => line.every(Boolean))) setWinner("draw");
      else setTurn(other(color));
      return next;
    });
  }, []);

  useEffect(() => {
    if (mode !== "ai" || winner || turn !== aiColor) return;
    setThinking(true);
    const timer = window.setTimeout(() => {
      const move = chooseAiMove(board.map((row) => [...row]), aiColor);
      placeStone(move.row, move.col, aiColor);
      setThinking(false);
    }, 420);
    return () => window.clearTimeout(timer);
  }, [aiColor, board, mode, placeStone, turn, winner]);

  const handleCell = (row: number, col: number) => {
    if (winner || thinking || board[row][col]) return;
    if (mode === "ai" && turn !== humanColor) return;
    placeStone(row, col, turn);
  };

  const undo = () => {
    if (!history.length || thinking) return;
    const count = mode === "ai" && history.length >= 2 ? 2 : 1;
    const kept = history.slice(0, -count);
    const next = emptyBoard();
    kept.forEach((move) => { next[move.row][move.col] = move.color; });
    setBoard(next);
    setHistory(kept);
    setWinner(null);
    setTurn(kept.length % 2 === 0 ? "black" : "white");
  };

  const status = useMemo(() => {
    if (winner === "draw") return "棋逢对手，平局";
    if (winner) return `${winner === "black" ? "黑棋" : "白棋"}获胜`;
    if (thinking) return "电脑正在思考…";
    if (mode === "ai") return turn === humanColor ? "轮到你落子" : "电脑回合";
    return `轮到${turn === "black" ? "黑棋" : "白棋"}`;
  }, [humanColor, mode, thinking, turn, winner]);

  const lastMove = history.at(-1);

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="#game" aria-label="弈五子首页">
          <span className="brand-mark"><i /><i /></span>
          <span>弈五子</span>
        </a>
        <span className="tagline">一局静心 · 五子连珠</span>
      </header>

      <section className="game-layout" id="game">
        <div className="board-wrap">
          <div className="corner corner-a" /><div className="corner corner-b" />
          <div className="board" role="grid" aria-label="十五路五子棋棋盘">
            {board.map((row, rowIndex) => row.map((cell, colIndex) => {
              const isLast = lastMove?.row === rowIndex && lastMove?.col === colIndex;
              const star = [3, 7, 11].includes(rowIndex) && [3, 7, 11].includes(colIndex);
              return (
                <button
                  className={`cell${star ? " star" : ""}`}
                  key={`${rowIndex}-${colIndex}`}
                  onClick={() => handleCell(rowIndex, colIndex)}
                  disabled={Boolean(cell) || Boolean(winner) || thinking}
                  aria-label={`${String.fromCharCode(65 + colIndex)}${rowIndex + 1}${cell ? `，${cell === "black" ? "黑棋" : "白棋"}` : "，空位"}`}
                >
                  {cell && <span className={`stone ${cell}${isLast ? " last" : ""}`} />}
                </button>
              );
            }))}
          </div>
        </div>

        <aside className="panel">
          <div className="eyebrow">GOMOKU · 15 × 15</div>
          <h1>落子无悔<br /><em>胜负有声</em></h1>
          <p className="intro">在纵横交错之间，先连成五子者胜。</p>

          <div className={`status-card${winner ? " finished" : ""}`} aria-live="polite">
            <span className={`mini-stone ${winner && winner !== "draw" ? winner : turn}`} />
            <div><small>{winner ? "本局结果" : `第 ${history.length + 1} 手`}</small><strong>{status}</strong></div>
          </div>

          <div className="control-group">
            <span className="control-label">对局模式</span>
            <div className="segmented">
              <button className={mode === "ai" ? "active" : ""} onClick={() => { setMode("ai"); reset(); }}>人机对战</button>
              <button className={mode === "friend" ? "active" : ""} onClick={() => { setMode("friend"); reset(); }}>双人对弈</button>
            </div>
          </div>

          {mode === "ai" && <div className="control-group">
            <span className="control-label">谁先落子</span>
            <div className="color-choice">
              <button className={humanFirst ? "selected" : ""} onClick={() => { setHumanFirst(true); reset(); }}><i className="black-dot" />我要先下 · 黑棋</button>
              <button className={!humanFirst ? "selected" : ""} onClick={() => { setHumanFirst(false); reset(); }}><i className="white-dot" />让电脑先下 · 我执白</button>
            </div>
          </div>}

          <div className="actions">
            <button className="primary" onClick={reset}>重新开局 <span>↗</span></button>
            <button className="secondary" onClick={undo} disabled={!history.length || thinking}>悔棋</button>
          </div>

          <div className="rule"><span>规则</span><p>黑白双方交替落子，横、竖或斜线率先连成五子即获胜。</p></div>
        </aside>
      </section>
      <footer><span>黑白落定，方寸见心</span><span>NO. {String(history.length + 1).padStart(3, "0")}</span></footer>
    </main>
  );
}
