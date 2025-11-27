"use client";

import api from "@/lib/api";

export type GroupSource = {
    id: string;
    name: string;
    platform: "whatsapp" | "telegram";
    source_group_id: string;
    is_active: boolean;
};

export type GroupDestination = {
    id: string;
    name: string;
    platform: "whatsapp" | "telegram";
    destination_group_id: string;
    is_active: boolean;
};

export type CreateGroupPayload = {
    name: string;
    platform: "whatsapp" | "telegram";
    group_id: string; // source_group_id or destination_group_id
};

// --- Source Groups ---

export async function getSourceGroups() {
    const { data } = await api.get<GroupSource[]>("/groups/source");
    return data;
}

export async function createSourceGroup(payload: CreateGroupPayload) {
    const { data } = await api.post<GroupSource>("/groups/source", {
        name: payload.name,
        platform: payload.platform,
        source_group_id: payload.group_id,
    });
    return data;
}

export async function deleteSourceGroup(id: string) {
    await api.delete(`/groups/source/${id}`);
}

// --- Destination Groups ---

export async function getDestinationGroups() {
    const { data } = await api.get<GroupDestination[]>("/groups/destination");
    return data;
}

export async function createDestinationGroup(payload: CreateGroupPayload) {
    const { data } = await api.post<GroupDestination>("/groups/destination", {
        name: payload.name,
        platform: payload.platform,
        destination_group_id: payload.group_id,
    });
    return data;
}

export async function deleteDestinationGroup(id: string) {
    await api.delete(`/groups/destination/${id}`);
}
