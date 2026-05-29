import { agentStatus } from '../data/mockData';

export default function AgentPanel() {
  return (
    <div>
      {(agentStatus || []).map((agent) => (
        <div key={agent.id} className="agent-card">
          <div
            className="agent-icon"
            style={{ background: agent.bg, color: agent.color, fontFamily: 'var(--font-mono)' }}
          >
            {agent.name.slice(0, 2)}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span className="agent-name" style={{ color: agent.color }}>{agent.name}</span>
              <span
                style={{
                  width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                  background: agent.status === 'active' ? 'var(--green)' : 'var(--yellow)',
                  animation: agent.status === 'active' ? 'pulse-live 1.8s ease-in-out infinite' : 'none',
                }}
              />
            </div>
            <div className="agent-role">{agent.role}</div>
            <div className="agent-activity">{agent.lastAction}</div>
          </div>
          <div style={{ fontSize: 9, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
            {agent.activity}
          </div>
        </div>
      ))}
    </div>
  );
}
