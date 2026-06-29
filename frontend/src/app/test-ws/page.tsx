'use client'

import { useState } from "react";
import { useTripPlanner, TripRequest } from "@/hooks/useTripPlanner";

export default function TestWSPage() {
  const { status, agents, eventLog, plan, error, startPlanning, reset } = useTripPlanner();

  const [form, setForm] = useState<TripRequest>({
    destination: "Tokyo",
    origin: "SFO",
    departureDate: "2026-10-10",
    returnDate: "2026-10-17",
    budget: 3500,
    travelers: 2,
    interests: ["food", "culture", "sightseeing"],
  });

  const [interestInput, setInterestInput] = useState("");

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    startPlanning(form);
  };

  const addInterest = () => {
    if (interestInput.trim() && !form.interests.includes(interestInput.trim())) {
      setForm({
        ...form,
        interests: [...form.interests, interestInput.trim()]
      });
      setInterestInput("");
    }
  };

  const removeInterest = (index: number) => {
    setForm({
      ...form,
      interests: form.interests.filter((_, i) => i !== index)
    });
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-zinc-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">Travel Planner WebSocket Playground</h1>
            <p className="text-zinc-400 mt-1">Test the multi-agent system orchestrator with mock or real WebSockets.</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-zinc-400 font-medium">Status:</span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${
              status === 'idle' ? 'bg-zinc-800 text-zinc-300' :
              status === 'connecting' ? 'bg-amber-900/40 text-amber-300 border border-amber-800/60 animate-pulse' :
              status === 'planning' ? 'bg-blue-900/40 text-blue-300 border border-blue-800/60 animate-pulse' :
              status === 'complete' ? 'bg-emerald-900/40 text-emerald-300 border border-emerald-800/60' :
              'bg-red-900/40 text-red-300 border border-red-800/60'
            }`}>
              {status}
            </span>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-900/30 border border-red-800/80 rounded-xl text-red-200 text-sm">
            <span className="font-semibold">Error:</span> {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Config Column */}
          <div className="lg:col-span-1 bg-zinc-900/50 border border-zinc-800/80 rounded-2xl p-6 space-y-6">
            <h2 className="text-xl font-semibold text-white">Planner Configuration</h2>
            <form onSubmit={handleStart} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Destination</label>
                <input
                  type="text"
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                  value={form.destination}
                  onChange={e => setForm({ ...form, destination: e.target.value })}
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Origin</label>
                <input
                  type="text"
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                  value={form.origin}
                  onChange={e => setForm({ ...form, origin: e.target.value })}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Departure Date</label>
                  <input
                    type="date"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                    value={form.departureDate}
                    onChange={e => setForm({ ...form, departureDate: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Return Date</label>
                  <input
                    type="date"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                    value={form.returnDate}
                    onChange={e => setForm({ ...form, returnDate: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Budget ($)</label>
                  <input
                    type="number"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                    value={form.budget}
                    onChange={e => setForm({ ...form, budget: parseInt(e.target.value) || 0 })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Travelers</label>
                  <input
                    type="number"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                    value={form.travelers}
                    onChange={e => setForm({ ...form, travelers: parseInt(e.target.value) || 1 })}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Interests</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Add interest..."
                    className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                    value={interestInput}
                    onChange={e => setInterestInput(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addInterest(); } }}
                  />
                  <button
                    type="button"
                    onClick={addInterest}
                    className="px-3.5 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm transition-colors"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {form.interests.map((interest, i) => (
                    <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 bg-zinc-800 rounded-md text-xs font-medium text-zinc-200">
                      {interest}
                      <button type="button" onClick={() => removeInterest(i)} className="text-zinc-400 hover:text-white font-bold ml-0.5">×</button>
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={status === 'planning' || status === 'connecting'}
                  className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-500 text-white font-semibold py-2 px-4 rounded-xl text-sm transition-colors cursor-pointer disabled:cursor-not-allowed"
                >
                  Start Planning
                </button>
                <button
                  type="button"
                  onClick={reset}
                  className="px-4 py-2 border border-zinc-850 hover:bg-zinc-800 text-zinc-300 font-semibold rounded-xl text-sm transition-colors"
                >
                  Reset
                </button>
              </div>
            </form>
          </div>

          {/* Agents & Event Feed Column */}
          <div className="lg:col-span-2 space-y-8">
            {/* Agent Status */}
            <div className="bg-zinc-900/50 border border-zinc-800/80 rounded-2xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Agent Coordinator Status</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {agents.map((agent) => (
                  <div key={agent.name} className="p-4 bg-zinc-900 border border-zinc-850 rounded-xl space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-semibold capitalize text-white">{agent.name}</span>
                      {agent.hasArtifact && (
                        <span className="text-[10px] font-bold text-blue-400 bg-blue-950 px-1.5 py-0.5 rounded border border-blue-900">
                          Artifact
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="text-xs text-zinc-500 block mb-1">Status</span>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        agent.status === 'idle' ? 'bg-zinc-800 text-zinc-400' :
                        agent.status === 'submitted' ? 'bg-zinc-800/80 text-zinc-300 border border-zinc-700' :
                        agent.status === 'working' ? 'bg-blue-950 text-blue-300 border border-blue-900 animate-pulse' :
                        agent.status === 'completed' ? 'bg-emerald-950 text-emerald-300 border border-emerald-900' :
                        'bg-red-950 text-red-300 border border-red-900'
                      }`}>
                        {agent.status}
                      </span>
                    </div>
                    {agent.taskId && (
                      <div className="text-[10px] text-zinc-500 truncate">
                        ID: <span className="font-mono">{agent.taskId}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Event Log */}
            <div className="bg-zinc-900/50 border border-zinc-800/80 rounded-2xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">WebSocket Event Log</h2>
              <div className="bg-zinc-950 border border-zinc-850 rounded-xl p-4 h-[240px] overflow-y-auto font-mono text-xs space-y-2.5">
                {eventLog.length === 0 ? (
                  <div className="text-zinc-600 text-center py-16">No WebSocket events received yet. Start planning to see logs.</div>
                ) : (
                  eventLog.map((log, idx) => (
                    <div key={idx} className="border-b border-zinc-900 pb-2 last:border-b-0 last:pb-0">
                      <div className="flex justify-between text-zinc-500 text-[10px] mb-1">
                        <span>[{log.timestamp}]</span>
                        <span className="text-blue-500">{log.event.event}</span>
                      </div>
                      <pre className="whitespace-pre-wrap overflow-x-auto text-zinc-300 leading-relaxed max-h-[120px]">
                        {JSON.stringify(log.event, null, 2)}
                      </pre>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Plan Display */}
            {plan && (
              <div className="bg-emerald-950/20 border border-emerald-800/40 rounded-2xl p-6 space-y-4">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-semibold text-emerald-400">🎉 Trip Plan Generated!</h2>
                  <span className="text-xs text-zinc-400 bg-zinc-900 px-3 py-1 rounded-lg border border-zinc-800">
                    {plan.destination} ({plan.dates})
                  </span>
                </div>
                <div className="bg-zinc-950 border border-zinc-850 rounded-xl p-4 text-xs font-mono max-h-[400px] overflow-y-auto">
                  <pre className="text-zinc-300 whitespace-pre-wrap">{JSON.stringify(plan, null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}