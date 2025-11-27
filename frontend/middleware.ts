import { NextRequest, NextResponse } from "next/server";

const AUTH_COOKIE_KEY = "autopromo_token";

// Rotas públicas que NÃO precisam de auth
const PUBLIC_PATHS = ["/", "/login", "/register"];

/**
 * Middleware de autenticação:
 * - Protege /dashboard/*
 * - Evita que usuário logado veja /login e /register
 */
export function middleware(req: NextRequest) {
    const { pathname } = req.nextUrl;

    // Ignorar assets estáticos e APIs internas do Next
    if (
        pathname.startsWith("/_next") ||
        pathname.startsWith("/api") ||
        pathname.startsWith("/static") ||
        pathname.match(/\.(.*)$/)
    ) {
        return NextResponse.next();
    }

    const token = req.cookies.get(AUTH_COOKIE_KEY)?.value || null;
    const isAuthenticated = Boolean(token);

    const isPublicPath = PUBLIC_PATHS.includes(pathname);
    const isDashboardPath = pathname.startsWith("/dashboard");

    // 1) Se for rota de dashboard e não estiver autenticado → /login
    if (isDashboardPath && !isAuthenticated) {
        const loginUrl = new URL("/login", req.url);
        // opcional: guardar from para redirecionar depois do login
        loginUrl.searchParams.set("from", pathname);
        return NextResponse.redirect(loginUrl);
    }

    // 2) Se já estiver logado e tentar acessar /login ou /register → /dashboard
    if (isAuthenticated && (pathname === "/login" || pathname === "/register")) {
        const dashboardUrl = new URL("/dashboard", req.url);
        return NextResponse.redirect(dashboardUrl);
    }

    // 3) Caso normal → segue o baile
    return NextResponse.next();
}

// Define em quais rotas o middleware roda
export const config = {
    matcher: [
        /**
         * Protege:
         * - /dashboard/*
         * E permite:
         * - /, /login, /register sem token
         */
        "/dashboard/:path*",
        "/login",
        "/register",
        "/",
    ],
};
