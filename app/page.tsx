"use client";

import { useEffect, useMemo, useState } from "react";

type Category = {
  id: number;
  name: string;
  difficulty: "Easy" | "Medium" | "Hard" | "Very Hard";
  value: number;
  description: string;
  color: string;
  completed?: boolean;
};

const seedCategories: Category[] = [
  { id: 1, name: "Average Anime Watcher", difficulty: "Easy", value: 100, description: "Popular shows, recognizable hooks.", color: "#ff6b5f" },
  { id: 2, name: "Vibe AMQer", difficulty: "Medium", value: 200, description: "Match the vibe to the right title.", color: "#9b8cff" },
  { id: 3, name: "md22", difficulty: "Hard", value: 300, description: "The doggest rigs from md22's list.", color: "#5ce1e6" },
  { id: 4, name: "Grond's Bangers Pt 2", difficulty: "Very Hard", value: 400, description: "A lovingly hostile selection.", color: "#ffd166" },
  { id: 5, name: "Six Seven", difficulty: "Easy", value: 100, description: "Six or seven appears in the title, song, or artist.", color: "#ff6b5f" },
  { id: 6, name: "Grond's Bangers Pt 1", difficulty: "Medium", value: 200, description: "The first wave of selected bangers.", color: "#9b8cff" },
  { id: 7, name: "Hargichungus Deluxe", difficulty: "Hard", value: 300, description: "Deep cuts with no mercy.", color: "#5ce1e6" },
  { id: 8, name: "AMQaraoke", difficulty: "Very Hard", value: 400, description: "Name it from the host's voice alone.", color: "#ffd166" },
  { id: 9, name: "Oldies But Goodies", difficulty: "Easy", value: 100, description: "Legacy songs that still hit.", color: "#ff6b5f" },
  { id: 10, name: "Ridiculous Isekai Titles", difficulty: "Medium", value: 200, description: "The answer is longer than the sample.", color: "#9b8cff" },
  { id: 11, name: "Sampled", difficulty: "Hard", value: 300, description: "Recognize the song from a tricky excerpt.", color: "#5ce1e6" },
  { id: 12, name: "Voiceable", difficulty: "Very Hard", value: 400, description: "Easy to voice, hard to roll.", color: "#ffd166" },
];

const clips = [
  { anime: "Hunter × Hunter", song: "Hyori Ittai", artist: "Yuzu" },
  { anime: "Code Geass", song: "COLORS", artist: "FLOW" },
  { anime: "Re:Zero", song: "STYX HELIX", artist: "MYTH & ROID" },
  { anime: "Bunny Girl Senpai", song: "Fukashigi no Karte", artist: "Mai Sakurajima et al." },
  { anime: "Overlord III", song: "VORACITY", artist: "MYTH & ROID" },
];

export default function Home() {
  const [categories, setCategories] = useState(seedCategories);
  const [scores, setScores] = useState<[number, number]>([12, 19]);
  const [teamNames, setTeamNames] = useState<[string, string]>(["Kappachungus", "Cluegichungus"]);
  const [active, setActive] = useState<Category | null>(null);
  const [clip, setClip] = useState(0);
  const [roundScore, setRoundScore] = useState<[number, number]>([0, 0]);
  const [revealed, setRevealed] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(20);
  const [turn, setTurn] = useState<0 | 1>(0);

  useEffect(() => {
    if (!playing || time <= 0) return;
    const timer = window.setInterval(() => setTime((value) => value - 1), 1000);
    return () => window.clearInterval(timer);
  }, [playing, time]);

  useEffect(() => {
    if (time === 0) setPlaying(false);
  }, [time]);

  const completed = useMemo(() => categories.filter((item) => item.completed).length, [categories]);

  function openCategory(category: Category) {
    if (category.completed) return;
    setActive(category);
    setClip(0);
    setRoundScore([0, 0]);
    setRevealed(false);
    setPlaying(false);
    setTime(20);
  }

  function awardRound(team: 0 | 1) {
    setRoundScore((old) => team === 0 ? [old[0] + 1, old[1]] : [old[0], old[1] + 1]);
  }

  function nextClip() {
    if (clip < 4) {
      setClip((value) => value + 1);
      setRevealed(false);
      setPlaying(false);
      setTime(20);
    }
  }

  function finishCategory() {
    if (!active) return;
    const winner = roundScore[0] === roundScore[1] ? null : roundScore[0] > roundScore[1] ? 0 : 1;
    const points: [number, number] = winner === null ? [1, 1] : winner === turn ? (winner === 0 ? [3, 0] : [0, 3]) : (winner === 0 ? [2, 0] : [0, 2]);
    setScores((old) => [old[0] + points[0], old[1] + points[1]]);
    setCategories((old) => old.map((item) => item.id === active.id ? { ...item, completed: true } : item));
    setActive(null);
    setTurn((old) => old === 0 ? 1 : 0);
  }

  function resetGame() {
    setCategories(seedCategories);
    setScores([0, 0]);
    setActive(null);
    setTurn(0);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark">C</span><div><p>CHUNGUS STUDIOS</p><h1>AMQ Team Deathmatch</h1></div></div>
        <div className="top-actions"><span className="live-dot" /> HOST MODE <button className="icon-button" onClick={resetGame} title="Reset game">↻</button></div>
      </header>

      <section className="hero-strip">
        <div><span className="eyebrow">WINTER 2026 · MATCH 01</span><h2>Choose your next battleground.</h2></div>
        <div className="progress-wrap"><span>{completed}/12 CLEARED</span><div className="progress"><i style={{ width: `${completed / 12 * 100}%` }} /></div></div>
      </section>

      <section className="board" aria-label="Game categories">
        {categories.map((category, index) => (
          <button key={category.id} className={`category ${category.completed ? "completed" : ""}`} onClick={() => openCategory(category)} style={{ "--accent": category.color } as React.CSSProperties}>
            <span className="category-index">{String(index + 1).padStart(2, "0")}</span>
            <span className="difficulty">{category.difficulty} · {category.value}</span>
            <strong>{category.name}</strong>
            <span className="category-footer">{category.completed ? "CLAIMED" : "ENTER ROUND"}<b>↗</b></span>
          </button>
        ))}
      </section>

      <section className="scoreboard">
        {[0, 1].map((team) => (
          <div className={`team-card ${turn === team ? "picking" : ""}`} key={team}>
            <div><span>{turn === team ? "PICKING NOW" : "TEAM"}</span><input aria-label={`Team ${team + 1} name`} value={teamNames[team]} onChange={(event) => setTeamNames((old) => team === 0 ? [event.target.value, old[1]] : [old[0], event.target.value])} /></div>
            <div className="score-controls"><button onClick={() => setScores((old) => team === 0 ? [Math.max(0, old[0] - 1), old[1]] : [old[0], Math.max(0, old[1] - 1)])}>−</button><strong>{scores[team]}</strong><button onClick={() => setScores((old) => team === 0 ? [old[0] + 1, old[1]] : [old[0], old[1] + 1])}>+</button></div>
          </div>
        ))}
      </section>

      {active && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`${active.name} round`}>
          <section className="round-panel">
            <button className="close" onClick={() => setActive(null)} aria-label="Close round">×</button>
            <div className="round-head"><div><span className="eyebrow">{active.difficulty} · {active.value}</span><h2>{active.name}</h2><p>{active.description}</p></div><div className="clip-count">CLIP <strong>{clip + 1}</strong> / 5</div></div>
            <div className="player">
              <div className={`timer ${time <= 5 ? "urgent" : ""}`}><strong>{time}</strong><span>SECONDS</span></div>
              <button className="play" onClick={() => setPlaying((value) => !value)}>{playing ? "Ⅱ" : "▶"}<span>{playing ? "PAUSE SAMPLE" : time === 20 ? "PLAY SAMPLE" : "RESUME SAMPLE"}</span></button>
              <div className="wave" aria-hidden="true">{Array.from({ length: 25 }).map((_, i) => <i key={i} style={{ height: `${18 + ((i * 17) % 44)}px` }} />)}</div>
            </div>
            <div className="answer-card">
              {!revealed ? <button className="reveal" onClick={() => setRevealed(true)}>REVEAL ANSWER</button> : <div><span>ANSWER</span><h3>{clips[clip].anime}</h3><p>{clips[clip].song} · {clips[clip].artist}</p></div>}
            </div>
            <div className="round-scoring">
              {[0, 1].map((team) => <button key={team} onClick={() => awardRound(team as 0 | 1)}><span>POINT TO</span><strong>{teamNames[team]}</strong><b>{roundScore[team]}</b></button>)}
            </div>
            <div className="round-actions"><button onClick={() => setTime(20)}>RESET TIMER</button>{clip < 4 ? <button className="primary" onClick={nextClip}>NEXT CLIP →</button> : <button className="primary" onClick={finishCategory}>FINISH CATEGORY →</button>}</div>
          </section>
        </div>
      )}
    </main>
  );
}
