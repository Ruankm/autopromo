"use client";

import { logout } from "@/services/auth";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <h1 className="text-2xl font-bold">AutoPromo Cloud</h1>
                    <button
                        onClick={logout}
                        className="text-sm text-gray-600 hover:text-gray-900"
                    >
                        Sair
                    </button>
                </div>
            </header>

            {/* Sidebar + Content */}
            <div className="flex">
                {/* Sidebar */}
                <aside className="w-64 bg-white shadow-sm min-h-[calc(100vh-73px)]">
                    <nav className="p-4 space-y-2">
                        <a
                            href="/dashboard"
                            className="block px-4 py-2 rounded hover:bg-gray-100"
                        >
                            📊 Dashboard
                        </a>
                        <a
                            href="/dashboard/whatsapp"
                            className="block px-4 py-2 rounded hover:bg-gray-100"
                        >
                            💬 WhatsApp
                        </a>
                        <a
                            href="/dashboard/groups"
                            className="block px-4 py-2 rounded hover:bg-gray-100"
                        >
                            👥 Grupos
                        </a>
                        <a
                            href="/dashboard/tags"
                            className="block px-4 py-2 rounded hover:bg-gray-100"
                        >
                            🏷️ Tags de Afiliado
                        </a>
                        <a
                            href="/dashboard/settings"
                            className="block px-4 py-2 rounded hover:bg-gray-100"
                        >
                            ⚙️ Configurações
                        </a>
                    </nav>
                </aside>

                {/* Main Content */}
                <main className="flex-1 p-8">{children}</main>
            </div>
        </div>
    );
}
