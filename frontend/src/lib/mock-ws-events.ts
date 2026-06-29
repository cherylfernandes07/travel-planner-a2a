// ─────────────────────────────────────────────────────────────
// mock-ws-events.ts
// Hardcoded event sequence with realistic timing.
// Swap this out by just changing the hook — nothing else.
// ─────────────────────────────────────────────────────────────

import { WSEvent } from "./ws-events";

// Each entry: [delayMs, event]
// Timing mirrors real async agent behavior:
//   - Flight + Itinerary finish fast (~3-4s)
//   - Hotel takes a bit longer (~5s)
//   - Budget runs last after Hotel completes
export const MOCK_WS_SEQUENCE: [number, WSEvent][] = [
    // ── Planner dispatches 3 parallel tasks ──────────────────
    [300, { event: "task_created", agent: "flight", status: "submitted", taskId: "task-flight-001" }],
    [400, { event: "task_created", agent: "hotel", status: "submitted", taskId: "task-hotel-001" }],
    [500, { event: "task_created", agent: "itinerary", status: "submitted", taskId: "task-itin-001" }],

    // ── Agents start working ──────────────────────────────────
    [900, { event: "task_updated", agent: "flight", status: "working", taskId: "task-flight-001" }],
    [1000, { event: "task_updated", agent: "itinerary", status: "working", taskId: "task-itin-001" }],
    [1200, { event: "task_updated", agent: "hotel", status: "working", taskId: "task-hotel-001" }],

    // ── Flight completes first ────────────────────────────────
    [3200, {
        event: "artifact",
        agent: "flight",
        taskId: "task-flight-001",
        data: {
            options: [
                { id: "f1", airline: "ANA NH006", priceUsd: 840, durationMins: 690, stops: 0, bookingUrl: "#" },
                { id: "f2", airline: "JAL JL061", priceUsd: 910, durationMins: 700, stops: 0, bookingUrl: "#" },
                { id: "f3", airline: "UA 837", priceUsd: 760, durationMins: 780, stops: 1, bookingUrl: "#" },
            ],
            recommendedId: "f1",
        },
    }],
    [3300, { event: "task_updated", agent: "flight", status: "completed", taskId: "task-flight-001" }],

    // ── Itinerary completes second ────────────────────────────
    [4100, {
        event: "artifact",
        agent: "itinerary",
        taskId: "task-itin-001",
        data: {
            days: [
                { day: 1, theme: "Arrive + Shinjuku", activities: [{ time: "18:00", name: "Check in + evening walk", estCostUsd: 20 }, { time: "20:00", name: "Ramen at Ichiran", estCostUsd: 15 }] },
                { day: 2, theme: "Tsukiji + Asakusa", activities: [{ time: "07:00", name: "Tsukiji outer market", estCostUsd: 30 }, { time: "11:00", name: "Senso-ji temple", estCostUsd: 0 }, { time: "14:00", name: "Nakamise shopping", estCostUsd: 40 }] },
                { day: 3, theme: "Shibuya + Harajuku", activities: [{ time: "09:00", name: "Meiji Shrine", estCostUsd: 0 }, { time: "12:00", name: "Shibuya crossing", estCostUsd: 0 }, { time: "15:00", name: "Takeshita street", estCostUsd: 50 }] },
                { day: 4, theme: "Yanaka + Ueno", activities: [{ time: "09:00", name: "Yanaka old town walk", estCostUsd: 10 }, { time: "13:00", name: "Tokyo National Museum", estCostUsd: 15 }, { time: "19:00", name: "Izakaya dinner", estCostUsd: 35 }] },
                { day: 5, theme: "Ginza + Depart", activities: [{ time: "09:00", name: "Ginza browsing", estCostUsd: 60 }, { time: "13:00", name: "Airport transfer", estCostUsd: 35 }] },
            ],
        },
    }],
    [4200, { event: "task_updated", agent: "itinerary", status: "completed", taskId: "task-itin-001" }],

    // ── Hotel completes last of the parallel three ────────────
    [5400, {
        event: "artifact",
        agent: "hotel",
        taskId: "task-hotel-001",
        data: {
            options: [
                { id: "h1", name: "Shinjuku Granbell Hotel", nightlyRate: 135, totalCost: 675, stars: 4, neighborhood: "Shinjuku", amenities: ["WiFi", "Gym", "Bar"] },
                { id: "h2", name: "Asakusa View Hotel", nightlyRate: 110, totalCost: 550, stars: 3, neighborhood: "Asakusa", amenities: ["WiFi", "Restaurant"] },
                { id: "h3", name: "Park Hyatt Tokyo", nightlyRate: 420, totalCost: 2100, stars: 5, neighborhood: "Shinjuku", amenities: ["WiFi", "Spa", "Pool", "Restaurant"] },
            ],
            recommendedId: "h1",
        },
    }],
    [5500, { event: "task_updated", agent: "hotel", status: "completed", taskId: "task-hotel-001" }],

    // ── Budget agent runs (sequential — waits for flight + hotel) ──
    [5700, { event: "task_created", agent: "budget", status: "submitted", taskId: "task-budget-001" }],
    [5900, { event: "task_updated", agent: "budget", status: "working", taskId: "task-budget-001" }],

    [7200, {
        event: "artifact",
        agent: "budget",
        taskId: "task-budget-001",
        data: {
            breakdown: { flights: 840, hotels: 675, activities: 410, dailyMisc: 350, total: 2275 },
            fitsBudget: true,
            surplusDeficit: 725,
        },
    }],
    [7300, { event: "task_updated", agent: "budget", status: "completed", taskId: "task-budget-001" }],

    // ── Planner assembles + emits final plan ──────────────────
    [7800, {
        event: "plan_complete",
        data: {
            destination: "Tokyo, Japan",
            dates: "Oct 15–20",
            flight: {
                options: [
                    { id: "f1", airline: "ANA NH006", priceUsd: 840, durationMins: 690, stops: 0, bookingUrl: "#" },
                    { id: "f2", airline: "JAL JL061", priceUsd: 910, durationMins: 700, stops: 0, bookingUrl: "#" },
                    { id: "f3", airline: "UA 837", priceUsd: 760, durationMins: 780, stops: 1, bookingUrl: "#" },
                ],
                recommendedId: "f1",
            },
            hotel: {
                options: [
                    { id: "h1", name: "Shinjuku Granbell Hotel", nightlyRate: 135, totalCost: 675, stars: 4, neighborhood: "Shinjuku", amenities: ["WiFi", "Gym", "Bar"] },
                    { id: "h2", name: "Asakusa View Hotel", nightlyRate: 110, totalCost: 550, stars: 3, neighborhood: "Asakusa", amenities: ["WiFi", "Restaurant"] },
                    { id: "h3", name: "Park Hyatt Tokyo", nightlyRate: 420, totalCost: 2100, stars: 5, neighborhood: "Shinjuku", amenities: ["WiFi", "Spa", "Pool", "Restaurant"] },
                ],
                recommendedId: "h1",
            },
            itinerary: {
                days: [
                    { day: 1, theme: "Arrive + Shinjuku", activities: [{ time: "18:00", name: "Check in + evening walk", estCostUsd: 20 }, { time: "20:00", name: "Ramen at Ichiran", estCostUsd: 15 }] },
                    { day: 2, theme: "Tsukiji + Asakusa", activities: [{ time: "07:00", name: "Tsukiji outer market", estCostUsd: 30 }, { time: "11:00", name: "Senso-ji temple", estCostUsd: 0 }] },
                    { day: 3, theme: "Shibuya + Harajuku", activities: [{ time: "09:00", name: "Meiji Shrine", estCostUsd: 0 }, { time: "12:00", name: "Shibuya crossing", estCostUsd: 0 }] },
                    { day: 4, theme: "Yanaka + Ueno", activities: [{ time: "09:00", name: "Yanaka old town walk", estCostUsd: 10 }, { time: "13:00", name: "Tokyo National Museum", estCostUsd: 15 }] },
                    { day: 5, theme: "Ginza + Depart", activities: [{ time: "09:00", name: "Ginza browsing", estCostUsd: 60 }, { time: "13:00", name: "Airport transfer", estCostUsd: 35 }] },
                ],
            },
            budget: {
                breakdown: { flights: 840, hotels: 675, activities: 410, dailyMisc: 350, total: 2275 },
                fitsBudget: true,
                surplusDeficit: 725,
            },
        },
    }],
];