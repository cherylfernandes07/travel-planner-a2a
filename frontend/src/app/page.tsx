import Image from "next/image";
import Link from "next/link";
import WaitlistSection from "@/components/WaitlistSection";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
    <div>
      <h1>Travel Planner</h1>
      <Link href="/test-ws">Start Planning</Link>
    </div>
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
       <WaitlistSection />
      </main>
    </div>
  );
}
