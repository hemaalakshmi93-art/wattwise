import React from "react";
import { api } from "../api.js";
import { useAsync, fmt } from "../hooks.js";
import { Card, Loading, ErrorBox, Empty, PageHeader } from "../components/ui.jsx";

export default function Community({ user, version }) {
  const prog = useAsync(() => api.progress(user.id), [user.id, version]);
  const comm = useAsync(() => api.community(), [version]);
  const board = useAsync(() => api.leaderboard(), [version]);

  return (
    <>
      <PageHeader title="Community">
        Your own achievements are shown separately from results across all participants.
      </PageHeader>

      <h2 className="section-title">Your achievements</h2>
      {prog.loading && !prog.data ? <Loading /> : prog.error ? <ErrorBox error={prog.error} onRetry={prog.reload} /> : (
        <>
          <div className="stats three">
            <div className="card stat"><span className="stat-label">Total points</span><span className="stat-value">{prog.data.total_points}</span></div>
            <div className="card stat"><span className="stat-label">Current streak</span>
              <span className="stat-value">{prog.data.current_streak}<small> days</small></span>
              <span className="muted small">Longest: {prog.data.longest_streak}</span></div>
            <div className="card stat"><span className="stat-label">Missions completed</span><span className="stat-value">{prog.data.completed_count}</span></div>
          </div>
          <Card title="Badges">
            <ul className="badges">
              {prog.data.badges.map((b) => (
                <li key={b.code} className={b.earned ? "earned" : ""}>
                  <strong>{b.title}</strong>
                  <span className="small">{b.description}</span>
                  <span className="tag">{b.earned ? "Earned" : "Locked"}</span>
                </li>
              ))}
            </ul>
          </Card>
        </>
      )}

      <h2 className="section-title">Community results</h2>
      {comm.loading && !comm.data ? <Loading /> : comm.error ? <ErrorBox error={comm.error} onRetry={comm.reload} /> : (
        <Card title={comm.data.goal.title} subtitle={comm.data.goal.description}>
          <div className="progress" role="progressbar" aria-valuenow={comm.data.goal.percent} aria-valuemin={0} aria-valuemax={100}>
            <div style={{ width: `${comm.data.goal.percent}%` }} />
          </div>
          <p>
            <strong>{fmt(comm.data.goal.completions)}</strong> of {fmt(comm.data.goal.target_completions)} missions
            completed ({comm.data.goal.percent}%)
          </p>
          <div className="mini-stats">
            <div><span className="big">{comm.data.participants}</span><span className="muted small">participants</span></div>
            <div><span className="big">{comm.data.active_participants}</span><span className="muted small">with missions done</span></div>
            <div><span className="big">{fmt(comm.data.total_points)}</span><span className="muted small">points earned</span></div>
            <div><span className="big">{comm.data.readings_logged}</span><span className="muted small">readings logged</span></div>
          </div>
          <p className="muted small">{comm.data.note}</p>
        </Card>
      )}

      <Card title="Leaderboard" subtitle="Ranked by points from saved mission completions">
        {board.loading && !board.data ? <Loading /> : board.error ? <ErrorBox error={board.error} onRetry={board.reload} /> :
          board.data.leaderboard.length === 0 ? <Empty title="No participants yet" /> : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Rank</th><th>Participant</th><th className="num">Missions</th><th className="num">Points</th></tr></thead>
                <tbody>
                  {board.data.leaderboard.map((e) => (
                    <tr key={e.user_id} className={e.user_id === user.id ? "me" : ""}>
                      <td>{e.rank}</td>
                      <td>{e.name}{e.user_id === user.id && <span className="tag">You</span>}
                        {e.is_demo && <span className="tag demo">Demo data</span>}</td>
                      <td className="num">{e.completions}</td>
                      <td className="num">{e.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </Card>
    </>
  );
}
