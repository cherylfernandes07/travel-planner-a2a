"use client";

import { useState } from "react";

export default function WaitlistSection() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async () => {
    if (!email || !email.includes("@")) {
      setMessage("Please enter a valid email address.");
      setStatus("error");
      return;
    }

    setStatus("loading");

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_WS_URL!
          .replace("wss://", "https://")
          .replace("ws://", "http://")
          .replace("/ws", "")}/waitlist`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        }
      );

      if (res.ok) {
        setStatus("success");
        setMessage("You're on the list! We'll be in touch.");
        setEmail("");
      } else {
        throw new Error("Request failed");
      }
    } catch {
      setStatus("error");
      setMessage("Something went wrong. Please try again.");
    }
  };

  return (
    <section style={{
      padding: "48px 24px",
      textAlign: "center",
      borderTop: "0.5px solid var(--border, #e5e7eb)",
      marginTop: "48px",
    }}>
      <h2 style={{
        fontSize: "24px",
        fontWeight: 500,
        marginBottom: "8px",
        color: "var(--text-primary, #111)",
      }}>
        Get early access
      </h2>

      <p style={{
        fontSize: "15px",
        color: "var(--text-secondary, #6b7280)",
        marginBottom: "24px",
        maxWidth: "420px",
        margin: "0 auto 24px",
        lineHeight: 1.6,
      }}>
        We're building an AI travel planner powered by multi-agent orchestration.
        Join the waitlist and we'll let you know when it's ready.
      </p>

      {status === "success" ? (
        <p style={{
          fontSize: "15px",
          color: "#065f46",
          fontWeight: 500,
        }}>
          ✓ {message}
        </p>
      ) : (
        <div style={{
          display: "flex",
          gap: "8px",
          justifyContent: "center",
          flexWrap: "wrap",
        }}>
          <input
            type="email"
            placeholder="your@email.com"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setStatus("idle");
              setMessage("");
            }}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            style={{
              padding: "10px 14px",
              fontSize: "14px",
              border: "0.5px solid #d1d5db",
              borderRadius: "8px",
              width: "260px",
              outline: "none",
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={status === "loading"}
            style={{
              padding: "10px 20px",
              fontSize: "14px",
              fontWeight: 500,
              background: "#111",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              cursor: status === "loading" ? "not-allowed" : "pointer",
              opacity: status === "loading" ? 0.7 : 1,
            }}
          >
            {status === "loading" ? "Joining..." : "Join waitlist"}
          </button>
        </div>
      )}

      {status === "error" && (
        <p style={{
          fontSize: "13px",
          color: "#b91c1c",
          marginTop: "8px",
        }}>
          {message}
        </p>
      )}
    </section>
  );
}