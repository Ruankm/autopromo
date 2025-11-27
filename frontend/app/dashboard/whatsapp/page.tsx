"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle2, QrCode, RefreshCw } from "lucide-react";
import { whatsappConnect, whatsappGetStatus, whatsappDiscoverGroups, whatsappDisconnect } from "@/lib/api";

type Status = "disconnected" | "connecting" | "connected";

interface Group {
    id: string;
    group_name: string;
    participant_count: number;
}

export default function WhatsAppPage() {
    const [status, setStatus] = useState<Status>("disconnected");
    const [qrCode, setQrCode] = useState<string | null>(null);
    const [groups, setGroups] = useState<Group[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    // Check status on mount
    useEffect(() => {
        checkStatus();
    }, []);

    // Polling when connecting
    useEffect(() => {
        if (status === "connecting") {
            const interval = setInterval(() => {
                checkStatus();
            }, 3000);

            // Stop after 2min
            const timeout = setTimeout(() => {
                clearInterval(interval);
                setStatus("disconnected");
                setError("QR Code expirado. Tente novamente.");
            }, 120000);

            return () => {
                clearInterval(interval);
                clearTimeout(timeout);
            };
        }
    }, [status]);

    const checkStatus = async () => {
        try {
            const data = await whatsappGetStatus();

            if (data.status === "connected") {
                setStatus("connected");
                setQrCode(null);
            } else if (data.status === "connecting") {
                setStatus("connecting");
            } else {
                setStatus("disconnected");
            }
        } catch (err: any) {
            if (err.response?.status !== 404) {
                console.error("Error checking status:", err);
            }
        }
    };

    const handleConnect = async () => {
        setLoading(true);
        setError("");

        try {
            const data = await whatsappConnect();

            if (data.qr_code) {
                setQrCode(data.qr_code);
                setStatus("connecting");
            } else {
                setError("QR Code não foi gerado. Tente novamente.");
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro ao conectar");
        } finally {
            setLoading(false);
        }
    };

    const handleDiscoverGroups = async () => {
        setLoading(true);
        setError("");

        try {
            const data = await whatsappDiscoverGroups();
            setGroups(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro ao descobrir grupos");
        } finally {
            setLoading(false);
        }
    };

    const handleDisconnect = async () => {
        if (!confirm("Desconectar WhatsApp?")) return;

        try {
            await whatsappDisconnect();
            setStatus("disconnected");
            setQrCode(null);
            setGroups([]);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro ao desconectar");
        }
    };

    // Connected view
    if (status === "connected") {
        return (
            <div className="container max-w-4xl mx-auto p-6">
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="flex items-center gap-2">
                                    <CheckCircle2 className="w-6 h-6 text-green-500" />
                                    WhatsApp Conectado
                                </CardTitle>
                                <CardDescription>Seu WhatsApp está ativo e pronto para uso</CardDescription>
                            </div>
                            <Button variant="destructive" onClick={handleDisconnect}>
                                Desconectar
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {error && (
                            <Alert variant="destructive">
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        <Alert>
                            <CheckCircle2 className="h-4 w-4" />
                            <AlertDescription>
                                ✅ Conexão ativa. Você pode descobrir grupos e gerenciá-los em /dashboard/groups
                            </AlertDescription>
                        </Alert>

                        <div className="space-y-4">
                            <Button onClick={handleDiscoverGroups} disabled={loading} className="w-full">
                                {loading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Descobrindo...
                                    </>
                                ) : (
                                    "Descobrir Grupos do WhatsApp"
                                )}
                            </Button>

                            {groups.length > 0 && (
                                <div className="border rounded-lg p-4">
                                    <h3 className="font-semibold mb-2">Grupos Descobertos ({groups.length})</h3>
                                    <div className="space-y-2 max-h-64 overflow-y-auto">
                                        {groups.map((group) => (
                                            <div key={group.id} className="flex justify-between items-center p-2 border rounded">
                                                <span>{group.group_name}</span>
                                                <span className="text-sm text-gray-500">{group.participant_count} membros</span>
                                            </div>
                                        ))}
                                    </div>
                                    <p className="text-sm text-gray-500 mt-4">
                                        Vá para <a href="/dashboard/groups" className="underline">Grupos</a> para ativar/gerenciar
                                    </p>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Disconnected / Connecting view
    return (
        <div className="container max-w-4xl mx-auto p-6">
            <Card>
                <CardHeader>
                    <CardTitle>Conectar WhatsApp</CardTitle>
                    <CardDescription>
                        Conecte seu WhatsApp pessoal para gerenciar grupos e enviar promoções
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {error && (
                        <Alert variant="destructive">
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    {!qrCode && status === "disconnected" && (
                        <div className="flex flex-col items-center justify-center py-8 space-y-4">
                            <QrCode className="w-24 h-24 text-gray-400" />
                            <p className="text-center text-gray-600">
                                Clique abaixo para gerar o QR Code e conectar seu WhatsApp
                            </p>
                            <Button onClick={handleConnect} disabled={loading} size="lg">
                                {loading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Gerando QR Code...
                                    </>
                                ) : (
                                    "Conectar via QR Code"
                                )}
                            </Button>
                        </div>
                    )}

                    {qrCode && status === "connecting" && (
                        <div className="flex flex-col items-center justify-center py-4 space-y-4">
                            <div className="relative">
                                <Image
                                    src={`data:image/png;base64,${qrCode}`}
                                    alt="QR Code WhatsApp"
                                    width={256}
                                    height={256}
                                    className="border-4 border-gray-800 rounded-lg"
                                />
                            </div>
                            <Alert>
                                <AlertDescription>
                                    <div className="space-y-2">
                                        <p className="font-semibold">Como escanear:</p>
                                        <ol className="text-sm space-y-1 ml-4 list-decimal">
                                            <li>Abra o WhatsApp no seu celular</li>
                                            <li>Vá em Configurações → Aparelhos Conectados</li>
                                            <li>Toque em "Conectar um aparelho"</li>
                                            <li>Aponte a câmera para este QR Code</li>
                                        </ol>
                                    </div>
                                </AlertDescription>
                            </Alert>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Aguardando leitura do QR Code...
                            </div>
                            <Button variant="outline" onClick={handleConnect} size="sm">
                                <RefreshCw className="w-4 h-4 mr-2" />
                                Gerar Novo QR Code
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
