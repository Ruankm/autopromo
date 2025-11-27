"use client";

import api from "@/lib/api";
import Cookies from "js-cookie";
import { AUTH_COOKIE_KEY } from "@/lib/api";

type LoginPayload = {
    email: string;
    password: string;
};

type RegisterPayload = {
    email: string;
    password: string;
    full_name: string;
};

type LoginResponse = {
    access_token: string;
    token_type: string;
};

type UserResponse = {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    created_at: string;
};

/**
 * Faz login e salva token no cookie com flags de segurança.
 */
export async function login(payload: LoginPayload) {
    const formData = new FormData();
    formData.append("username", payload.email);
    formData.append("password", payload.password);

    const { data } = await api.post<LoginResponse>("/users/login", formData, {
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
    });

    // Salva token no cookie com flags de segurança
    const isProduction = window.location.protocol === "https:";

    Cookies.set(AUTH_COOKIE_KEY, data.access_token, {
        expires: 7, // 7 dias
        secure: isProduction, // HTTPS only em produção
        sameSite: "strict", // Proteção CSRF
        path: "/", // Disponível em todas as rotas
    });

    return data;
}

/**
 * Registra novo usuário.
 */
export async function register(payload: RegisterPayload) {
    const { data } = await api.post<UserResponse>("/users/register", payload);
    return data;
}

/**
 * Faz logout limpando cookie e redirecionando.
 */
export async function logout() {
    Cookies.remove(AUTH_COOKIE_KEY, { path: "/" });
    window.location.href = "/login";
}

/**
 * Busca dados do usuário atual.
 */
export async function me() {
    const { data } = await api.get<UserResponse>("/users/me");
    return data;
}
