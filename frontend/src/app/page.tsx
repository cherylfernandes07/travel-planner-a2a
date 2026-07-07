import Image from "next/image";
import Link from "next/link";
import WaitlistSection from "@/components/WaitlistSection";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
    <section style={{
      padding: "0px 24px",
      textAlign: "center",
      marginTop: "48px",
    }}>
      <h2 style={{
        fontSize: "24px",
        fontWeight: 500,
        marginBottom: "8px",
        color: "var(--text-primary, #111)",
      }}>
        Travel Planner
      </h2>

      <p style={{
        fontSize: "15px",
        color: "var(--text-secondary, #6b7280)",
        marginBottom: "24px",
        maxWidth: "420px",
        margin: "0 auto 24px",
        lineHeight: 1.6,
      }}>
        Start planning your next trip by clicking the link below. you can also signup for a waitlist.
      </p>

        <div style={{
          display: "flex",
          gap: "8px",
          justifyContent: "center",
          flexWrap: "wrap",
        }}>
          <Link href="/test-ws" style={{border: '1px solid black', padding: '5px', borderRadius: '5px'}}>Start Planning Your Next Trip</Link>
        </div>
    </section>
      <main >
       <WaitlistSection />
      </main>
    </div>
  );
}
