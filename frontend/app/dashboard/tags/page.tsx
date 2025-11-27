"use client";

import { useEffect, useState } from "react";
import { getTags, createTag, deleteTag, type AffiliateTag } from "@/services/tags";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Trash2, Plus, Tag } from "lucide-react";

export default function TagsPage() {
    const [tags, setTags] = useState<AffiliateTag[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState({
        store_slug: "",
        tag_code: "",
    });

    async function loadTags() {
        setLoading(true);
        try {
            const data = await getTags();
            setTags(data);
        } catch (error) {
            console.error("Failed to load tags", error);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadTags();
    }, []);

    async function handleCreate() {
        try {
            await createTag(formData);
            setIsModalOpen(false);
            setFormData({ store_slug: "", tag_code: "" });
            loadTags();
        } catch (error) {
            console.error("Failed to create tag", error);
            alert("Erro ao criar tag");
        }
    }

    async function handleDelete(id: string) {
        if (!confirm("Tem certeza que deseja deletar esta tag?")) return;
        try {
            await deleteTag(id);
            loadTags();
        } catch (error) {
            console.error("Failed to delete tag", error);
            alert("Erro ao deletar tag");
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Tags de Afiliado</h1>

                <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" /> Adicionar Tag
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Nova Tag de Afiliado</DialogTitle>
                            <DialogDescription>
                                Cadastre seu código de afiliado para uma loja específica.
                            </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Loja (Slug)</label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={formData.store_slug}
                                    onChange={(e) => setFormData({ ...formData, store_slug: e.target.value })}
                                >
                                    <option value="">Selecione uma loja...</option>
                                    <option value="amazon">Amazon</option>
                                    <option value="magalu">Magalu</option>
                                    <option value="mercadolivre">Mercado Livre</option>
                                    <option value="shopee">Shopee</option>
                                    <option value="americanas">Americanas</option>
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Código da Tag</label>
                                <Input
                                    value={formData.tag_code}
                                    onChange={(e) => setFormData({ ...formData, tag_code: e.target.value })}
                                    placeholder="Ex: minha-tag-20"
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

            <div className="rounded-md border bg-white">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Loja</TableHead>
                            <TableHead>Tag Code</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="w-[100px]">Ações</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {tags.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                                    <div className="flex flex-col items-center justify-center space-y-2">
                                        <Tag className="h-8 w-8 text-muted-foreground/50" />
                                        <p>Nenhuma tag cadastrada.</p>
                                    </div>
                                </TableCell>
                            </TableRow>
                        ) : (
                            tags.map((tag) => (
                                <TableRow key={tag.id}>
                                    <TableCell className="font-medium capitalize">{tag.store_slug}</TableCell>
                                    <TableCell className="font-mono">{tag.tag_code}</TableCell>
                                    <TableCell>
                                        <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-800">
                                            Ativo
                                        </span>
                                    </TableCell>
                                    <TableCell>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="text-destructive hover:text-destructive"
                                            onClick={() => handleDelete(tag.id)}
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
        </div>
    );
}
