export default function HomePage() {
    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className="text-center">
                <h1 className="text-4xl font-bold mb-4">AutoPromo Cloud</h1>
                <p className="text-muted-foreground mb-8">
                    High-Frequency Trading SaaS for Affiliate Marketing
                </p>
                <div className="space-x-4">
                    <a
                        href="/login"
                        className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-md hover:opacity-90 transition"
                    >
                        Entrar
                    </a>
                    <a
                        href="/register"
                        className="inline-block px-6 py-3 bg-secondary text-secondary-foreground rounded-md hover:opacity-90 transition"
                    >
                        Criar Conta
                    </a>
                </div>
            </div>
        </div>
    );
}
