"use client";

import api from "@/lib/api";

export type DashboardStats = {
    total_queue: number;
    sent_today: number;
    active_groups: number;
    active_tags: number;
};

export type RecentOffer = {
    id: string;
    product_unique_id: string;
    store_slug: string;
    price_cents: number;
    created_at: string;
    status: string;
};

export async function getDashboardStats() {
    // Mock implementation until backend endpoint is ready
    // In a real scenario: const { data } = await api.get<DashboardStats>("/dashboard/stats");
    return {
        total_queue: 0,
        sent_today: 0,
        active_groups: 0,
        active_tags: 0,
    };
}

export async function getRecentOffers() {
    // Mock implementation
    // const { data } = await api.get<RecentOffer[]>("/dashboard/recent-offers");
    return [];
}
