"use client";

import api from "@/lib/api";

export type AffiliateTag = {
    id: string;
    store_slug: string;
    tag_code: string;
    is_active: boolean;
};

export type CreateTagPayload = {
    store_slug: string;
    tag_code: string;
};

export async function getTags() {
    const { data } = await api.get<AffiliateTag[]>("/affiliate-tags");
    return data;
}

export async function createTag(payload: CreateTagPayload) {
    const { data } = await api.post<AffiliateTag>("/affiliate-tags", payload);
    return data;
}

export async function deleteTag(id: string) {
    await api.delete(`/affiliate-tags/${id}`);
}
