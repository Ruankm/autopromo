"use client";

import api from "@/lib/api";

export type UserConfig = {
    window_start?: string;
    window_end?: string;
    min_delay_seconds?: number;
    blacklist_stores?: string[];
};

export async function getUserConfig() {
    const { data } = await api.get<{ config_json: UserConfig }>("/users/me");
    return data.config_json;
}

export async function updateUserConfig(config: UserConfig) {
    const { data } = await api.patch("/users/me/config", config);
    return data;
}
