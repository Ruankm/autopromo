"use client";

import { useEffect, useState } from "react";
import { getDashboardStats, getRecentOffers, type DashboardStats, type RecentOffer } from "@/services/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function DashboardPage() {
    const [stats, setStats] = useState<DashboardStats>({
        total_queue: 0,
        sent_today: 0,
        active_groups: 0,
        active_tags: 0,
    });
    const [recentOffers, setRecentOffers] = useState<RecentOffer[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadData() {
            try {
                const [statsData, offersData] = await Promise.all([
                    getDashboardStats(),
                    getRecentOffers(),
                ]);
                setStats(statsData);
                setRecentOffers(offersData);
            } catch (error) {
                console.error("Failed to load dashboard data", error);
            } finally {
                setLoading(false);
            }
        }

        loadData();
    }, []);

    return (
        <div className="space-y-8">
            <h1 className="text-3xl font-bold">Dashboard</h1>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total na Fila</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.total_queue}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Enviados Hoje</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.sent_today}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Grupos Ativos</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.active_groups}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Tags Ativas</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.active_tags}</div>
                    </CardContent>
                </Card>
            </div>

            {/* Recent Offers Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Últimas Ofertas Processadas</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>ID Produto</TableHead>
                                <TableHead>Loja</TableHead>
                                <TableHead>Preço</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Data</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {recentOffers.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                                        Nenhuma oferta recente.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                recentOffers.map((offer) => (
                                    <TableRow key={offer.id}>
                                        <TableCell>{offer.product_unique_id}</TableCell>
                                        <TableCell>{offer.store_slug}</TableCell>
                                        <TableCell>
                                            {offer.price_cents
                                                ? (offer.price_cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                                                : '-'}
                                        </TableCell>
                                        <TableCell>{offer.status}</TableCell>
                                        <TableCell>{new Date(offer.created_at).toLocaleString()}</TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
