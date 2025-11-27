"use client";

import { useEffect, useState } from "react";
import { getUserConfig, updateUserConfig, type UserConfig } from "@/services/user";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
    const [config, setConfig] = useState<UserConfig>({
        window_start: "06:00",
        window_end: "23:00",
        min_delay_seconds: 300,
        blacklist_stores: [],
    });
    const [blacklistText, setBlacklistText] = useState("");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        async function loadConfig() {
            try {
                const data = await getUserConfig();
                if (data) {
                    setConfig(data);
                    setBlacklistText(data.blacklist_stores?.join(", ") || "");
                }
            } catch (error) {
                console.error("Failed to load config", error);
            } finally {
                setLoading(false);
            }
        }
        loadConfig();
    }, []);

    async function handleSave() {
        setSaving(true);
        try {
            // Parse blacklist text back to array
            const blacklistArray = blacklistText
                .split(",")
                .map((s) => s.trim())
                .filter((s) => s.length > 0);

            const newConfig = {
                ...config,
                blacklist_stores: blacklistArray,
            };

            await updateUserConfig(newConfig);
            alert("Configurações salvas com sucesso!");
        } catch (error) {
            console.error("Failed to save config", error);
            alert("Erro ao salvar configurações");
        } finally {
            setSaving(false);
        }
    }

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold">Configurações</h1>

            <Card>
                <CardHeader>
                    <CardTitle>Preferências de Envio</CardTitle>
                    <CardDescription>
                        Configure como e quando o AutoPromo deve enviar ofertas.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div>
                        <h3 className="text-lg font-medium mb-2">Janela de Horário</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                            Defina os horários permitidos para envio de mensagens.
                        </p>

                        <div className="grid grid-cols-2 gap-4 max-w-md">
                            <div>
                                <label className="block text-sm font-medium mb-1">
                                    Início
                                </label>
                                <Input
                                    type="time"
                                    value={config.window_start}
                                    onChange={(e) => setConfig({ ...config, window_start: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">
                                    Fim
                                </label>
                                <Input
                                    type="time"
                                    value={config.window_end}
                                    onChange={(e) => setConfig({ ...config, window_end: e.target.value })}
                                />
                            </div>
                        </div>
                    </div>

                    <div>
                        <h3 className="text-lg font-medium mb-2">Rate Limiting (Anti-Ban)</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                            Tempo mínimo de espera entre envios para o mesmo grupo.
                        </p>

                        <div className="flex items-center gap-2 max-w-xs">
                            <Input
                                type="number"
                                value={config.min_delay_seconds}
                                onChange={(e) => setConfig({ ...config, min_delay_seconds: parseInt(e.target.value) })}
                            />
                            <span className="text-sm text-muted-foreground">segundos</span>
                        </div>
                    </div>

                    <div>
                        <h3 className="text-lg font-medium mb-2">Blacklist de Lojas</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                            Lojas que serão bloqueadas automaticamente (separe por vírgula).
                        </p>

                        <textarea
                            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                            placeholder="shopee, aliexpress"
                            value={blacklistText}
                            onChange={(e) => setBlacklistText(e.target.value)}
                            rows={3}
                        />
                    </div>
                </CardContent>
                <CardFooter>
                    <Button onClick={handleSave} disabled={saving}>
                        {saving ? "Salvando..." : "Salvar Configurações"}
                    </Button>
                </CardFooter>
            </Card>
        </div>
    );
}
