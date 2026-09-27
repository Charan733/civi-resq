import { useEffect, useState, useRef } from "react";
import { Send, MessageSquareText, Bot, User } from "lucide-react";
import { zonesApi, assistantApi } from "../api/client";

const SUGGESTED = [
  "Why is this zone high risk?",
  "What is the main cause of flooding in this area?",
  "Which intervention should be prioritized?",
  "What happens if drainage capacity is improved by 30%?",
];

export default function Assistant() {
  const [zones, setZones] = useState([]);
  const [selectedZoneId, setSelectedZoneId] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi, I'm the CIVI-AI Assistant. Select a zone, then ask me about its risk factors, causes, or interventions — every answer is grounded in this system's actual model output, not general knowledge." },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    zonesApi.list().then((zs) => {
      setZones(zs);
      if (zs.length) setSelectedZoneId(zs[0].id);
    });
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const send = async (question) => {
    const q = question ?? input;
    if (!q.trim()) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setSending(true);
    try {
      const res = await assistantApi.ask(q, selectedZoneId || null);
      setMessages((m) => [...m, { role: "assistant", text: res.answer }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: "Sorry, I hit an error reaching the assessment data. Please try again." }]);
    } finally {
      setSending(false);
    }
  };

  const selectedZone = zones.find((z) => z.id === selectedZoneId);

  return (
    <div className="flex flex-col h-screen">
      <div className="bg-white border-b border-ink-100 px-5 py-3 flex flex-wrap items-center gap-3">
        <h1 className="font-display font-semibold text-ink-800 flex items-center gap-2">
          <MessageSquareText size={19} className="text-monsoon-500" /> CIVI-AI Assistant
        </h1>
        <select
          value={selectedZoneId}
          onChange={(e) => setSelectedZoneId(e.target.value)}
          className="ml-auto border border-ink-200 rounded-md px-3 py-1.5 text-sm bg-paper-50"
        >
          {zones.map((z) => (
            <option key={z.id} value={z.id}>{z.zone_name} ({z.zone_code})</option>
          ))}
        </select>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 md:px-8 space-y-4 max-w-3xl w-full mx-auto">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${m.role === "user" ? "bg-ink-600" : "bg-monsoon-500"}`}>
              {m.role === "user" ? <User size={15} className="text-white" /> : <Bot size={15} className="text-white" />}
            </div>
            <div
              className={`rounded-lg px-4 py-2.5 text-sm max-w-[80%] ${
                m.role === "user" ? "bg-ink-700 text-white" : "bg-white border border-ink-100 text-ink-700"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-monsoon-500 flex items-center justify-center flex-shrink-0">
              <Bot size={15} className="text-white" />
            </div>
            <div className="rounded-lg px-4 py-2.5 text-sm bg-white border border-ink-100 text-ink-400 font-mono">
              analyzing data…
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-ink-100 bg-white p-4">
        <div className="max-w-3xl w-full mx-auto">
          {selectedZone && (
            <div className="flex flex-wrap gap-1.5 mb-2.5">
              {SUGGESTED.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-xs bg-paper-100 hover:bg-paper-300 text-ink-600 px-2.5 py-1 rounded-full transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder={`Ask about ${selectedZone?.zone_name || "a zone"}…`}
              className="flex-1 border border-ink-200 rounded-md px-3 py-2.5 text-sm outline-none focus:border-monsoon-400"
            />
            <button
              onClick={() => send()}
              disabled={sending}
              className="bg-monsoon-500 hover:bg-monsoon-600 text-white p-2.5 rounded-md disabled:opacity-40"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
