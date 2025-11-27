"use client";

import { useEffect, useState } from "react";
import {
    getSourceGroups, getDestinationGroups,
    createSourceGroup, createDestinationGroup,
    deleteSourceGroup, deleteDestinationGroup,
    type GroupSource, type GroupDestination
} from "@/services/groups";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Trash2, Plus } from "lucide-react";

export default function GroupsPage() {
    const [sourceGroups, setSourceGroups] = useState<GroupSource[]>([]);
    const [destGroups, setDestGroups] = useState<GroupDestination[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [activeTab, setActiveTab] = useState("source");
    const [formData, setFormData] = useState({
        name: "",
        platform: "whatsapp" as "whatsapp" | "telegram",
        group_id: "",
    });

    async function loadGroups() {
        setLoading(true);
        try {
            const [sources, dests] = await Promise.all([
                getSourceGroups(),
                getDestinationGroups(),
            ]);
            setSourceGroups(sources);
            setDestGroups(dests);
        } catch (error) {
            console.error("Failed to load groups", error);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadGroups();
    }, []);

    async function handleCreate() {
        try {
            if (activeTab === "source") {
                await createSourceGroup(formData);
            } else {
                await createDestinationGroup(formData);
            }
            setIsModalOpen(false);
            setFormData({ name: "", platform: "whatsapp", group_id: "" });
            loadGroups();
        } catch (error) {
            console.error("Failed to create group", error);
            alert("Erro ao criar grupo");
        }
    }

    async function handleDelete(id: string, type: "source" | "destination") {
        if (!confirm("Tem certeza que deseja deletar este grupo?")) return;

        try {
            if (type === "source") {
                await deleteSourceGroup(id);
            } else {
                await deleteDestinationGroup(id);
            }
            loadGroups();
        } catch (error) {
            console.error("Failed to delete group", error);
            alert("Erro ao deletar grupo");
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Gestão de Grupos</h1>

                <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" /> Adicionar Grupo
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Adicionar Grupo {activeTab === "source" ? "de Origem" : "de Destino"}</DialogTitle>
                            <DialogDescription>
                                Configure um novo grupo para {activeTab === "source" ? "monitorar ofertas" : "enviar ofertas"}.
                            </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Nome do Grupo</label>
                                <Input
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="Ex: Promoções Tech"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Plataforma</label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={formData.platform}
                                    onChange={(e) => setFormData({ ...formData, platform: e.target.value as any })}
                                >
                                    <option value="whatsapp">WhatsApp</option>
                                    <option value="telegram">Telegram</option>
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">ID do Grupo (JID ou Chat ID)</label>
                                <Input
                                    value={formData.group_id}
                                    onChange={(e) => setFormData({ ...formData, group_id: e.target.value })}
                                    placeholder={formData.platform === "whatsapp" ? "123456@g.us" : "-100123456789"}
                                />
                            </div>
                        </div>

                        <DialogFooter>
                            <Button variant="outline" onClick={() => setIsModalOpen(false)}>Cancelar</Button>
                            <Button onClick={handleCreate}>Salvar</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2 max-w-[400px]">
                    <TabsTrigger value="source">Grupos Fonte (Origem)</TabsTrigger>
                    <TabsTrigger value="destination">Grupos Destino (Envio)</TabsTrigger>
                </TabsList>

                <TabsContent value="source" className="mt-6">
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Nome</TableHead>
                                    <TableHead>Plataforma</TableHead>
                                    <TableHead>ID Externo</TableHead>
                                    <TableHead className="w-[100px]">Ações</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {sourceGroups.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                                            Nenhum grupo de origem cadastrado.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    sourceGroups.map((group) => (
                                        <TableRow key={group.id}>
                                            <TableCell className="font-medium">{group.name}</TableCell>
                                            <TableCell className="capitalize">{group.platform}</TableCell>
                                            <TableCell className="font-mono text-xs">{group.source_group_id}</TableCell>
                                            <TableCell>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="text-destructive hover:text-destructive"
                                                    onClick={() => handleDelete(group.id, "source")}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </TabsContent>

                <TabsContent value="destination" className="mt-6">
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Nome</TableHead>
                                    <TableHead>Plataforma</TableHead>
                                    <TableHead>ID Externo</TableHead>
                                    <TableHead className="w-[100px]">Ações</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {destGroups.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                                            Nenhum grupo de destino cadastrado.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    destGroups.map((group) => (
                                        <TableRow key={group.id}>
                                            <TableCell className="font-medium">{group.name}</TableCell>
                                            <TableCell className="capitalize">{group.platform}</TableCell>
                                            <TableCell className="font-mono text-xs">{group.destination_group_id}</TableCell>
                                            <TableCell>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="text-destructive hover:text-destructive"
                                                    onClick={() => handleDelete(group.id, "destination")}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
