import tkinter as tk
import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from tkinter import ttk, messagebox, filedialog

from reportlab.lib.pagesizes import A6
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from xml.sax.saxutils import escape
import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "restoran_db",
}


def koneksi():
    return mysql.connector.connect(**DB_CONFIG)


def rupiah(angka):
    return "Rp" + f"{float(angka):,.0f}".replace(",", ".")


class AplikasiRestoran:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.role = user["role"]

        self.root.title("Sistem Pemesanan Makanan Restoran")
        self.root.geometry("1050x680")
        self.root.minsize(900, 600)

        self.cart = []
        self.menu_map = {}
        self.meja_map = {}

        self.buat_tampilan()
        self.muat_menu()
        self.muat_meja()
        self.muat_pesanan()

    def query(self, sql, params=(), fetch=False):
        conn = koneksi()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(sql, params)
            hasil = cur.fetchall() if fetch else None
            if not fetch:
                conn.commit()
            return hasil
        finally:
            cur.close()
            conn.close()

    def buat_tampilan(self):
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="PEMESANAN MAKANAN RESTORAN",
            font=("Arial", 18, "bold")
        ).pack(side="left")

        ttk.Label(
            header,
            text=f"Login: {self.user['username']} ({self.role.upper()})"
        ).pack(side="right")

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=8)

        self.tab_menu = ttk.Frame(self.tabs, padding=10)
        self.tab_transaksi = ttk.Frame(self.tabs, padding=10)
        self.tab_pesanan = ttk.Frame(self.tabs, padding=10)
        self.tab_dashboard = ttk.Frame(self.tabs, padding=10)
        self.tab_laporan = ttk.Frame(self.tabs, padding=10)

        if self.role == "admin":
            self.tabs.add(self.tab_menu, text="Data Menu")

        self.tabs.add(self.tab_transaksi, text="Pemesanan")
        self.tabs.add(self.tab_pesanan, text="Data Pesanan")
        self.tabs.add(self.tab_dashboard, text="Dashboard Statistik")
        if self.role == "admin":
            self.tabs.add(self.tab_laporan, text="Laporan & Backup")

        self.buat_tab_menu()
        self.buat_tab_transaksi()
        self.buat_tab_pesanan()
        self.buat_tab_dashboard()
        if self.role == "admin":
            self.buat_tab_laporan()

    def buat_tab_menu(self):
        form = ttk.LabelFrame(
            self.tab_menu, text="Form Menu", padding=10
        )
        form.pack(fill="x")

        self.menu_id = None
        self.nama_menu = tk.StringVar()
        self.kategori = tk.StringVar(value="Makanan")
        self.harga = tk.StringVar()
        self.stok = tk.StringVar()

        ttk.Label(form, text="Nama menu").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Entry(
            form, textvariable=self.nama_menu, width=25
        ).grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Kategori").grid(
            row=0, column=2, sticky="w", padx=5
        )
        ttk.Combobox(
            form,
            textvariable=self.kategori,
            values=["Makanan", "Minuman"],
            state="readonly",
            width=18
        ).grid(row=0, column=3, padx=5)

        ttk.Label(form, text="Harga").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Entry(
            form, textvariable=self.harga, width=25
        ).grid(row=1, column=1, padx=5)

        ttk.Label(form, text="Stok").grid(
            row=1, column=2, sticky="w", padx=5
        )
        ttk.Entry(
            form, textvariable=self.stok, width=20
        ).grid(row=1, column=3, padx=5)

        actions = ttk.Frame(form)
        actions.grid(
            row=2, column=0, columnspan=4,
            sticky="w", pady=8
        )

        ttk.Button(
            actions, text="Simpan",
            command=self.simpan_menu
        ).pack(side="left", padx=4)

        ttk.Button(
            actions, text="Ubah",
            command=self.ubah_menu
        ).pack(side="left", padx=4)

        ttk.Button(
            actions, text="Hapus",
            command=self.hapus_menu
        ).pack(side="left", padx=4)

        ttk.Button(
            actions, text="Bersihkan",
            command=self.bersihkan_form_menu
        ).pack(side="left", padx=4)

        cari = ttk.Frame(self.tab_menu)
        cari.pack(fill="x", pady=(10, 0))

        self.kata_cari = tk.StringVar()

        ttk.Label(cari, text="Cari menu:").pack(
            side="left", padx=5
        )
        ttk.Entry(
            cari, textvariable=self.kata_cari, width=30
        ).pack(side="left", padx=5)

        ttk.Button(
            cari, text="Cari",
            command=self.cari_menu
        ).pack(side="left", padx=3)

        ttk.Button(
            cari, text="Tampilkan Semua",
            command=self.muat_menu
        ).pack(side="left", padx=3)

        cols = ("id", "nama", "kategori", "harga", "stok")

        self.tree_menu = ttk.Treeview(
            self.tab_menu,
            columns=cols,
            show="headings",
            height=15
        )

        for c, t, w in [
            ("id", "ID", 55),
            ("nama", "Nama Menu", 280),
            ("kategori", "Kategori", 150),
            ("harga", "Harga", 150),
            ("stok", "Stok", 100)
        ]:
            self.tree_menu.heading(c, text=t)
            self.tree_menu.column(c, width=w)

        self.tree_menu.pack(
            fill="both", expand=True, pady=10
        )
        self.tree_menu.bind(
            "<<TreeviewSelect>>", self.pilih_menu
        )

    def buat_tab_transaksi(self):
        atas = ttk.LabelFrame(
            self.tab_transaksi,
            text="Buat Pesanan",
            padding=10
        )
        atas.pack(fill="x")

        self.pilih_meja = tk.StringVar()
        self.pilih_item = tk.StringVar()
        self.jumlah = tk.StringVar(value="1")

        ttk.Label(atas, text="Meja").grid(
            row=0, column=0, padx=5, pady=5
        )

        self.combo_meja = ttk.Combobox(
            atas,
            textvariable=self.pilih_meja,
            state="readonly",
            width=18
        )
        self.combo_meja.grid(row=0, column=1, padx=5)

        ttk.Label(atas, text="Menu").grid(
            row=0, column=2, padx=5
        )

        self.combo_menu = ttk.Combobox(
            atas,
            textvariable=self.pilih_item,
            state="readonly",
            width=32
        )
        self.combo_menu.grid(row=0, column=3, padx=5)

        ttk.Label(atas, text="Jumlah").grid(
            row=0, column=4, padx=5
        )

        ttk.Entry(
            atas, textvariable=self.jumlah, width=6
        ).grid(row=0, column=5, padx=5)

        ttk.Button(
            atas, text="Tambah",
            command=self.tambah_keranjang
        ).grid(row=0, column=6, padx=5)

        cols = ("nama", "harga", "jumlah", "subtotal")

        self.tree_cart = ttk.Treeview(
            self.tab_transaksi,
            columns=cols,
            show="headings",
            height=13
        )

        for c, t, w in [
            ("nama", "Menu", 300),
            ("harga", "Harga", 150),
            ("jumlah", "Jumlah", 100),
            ("subtotal", "Subtotal", 160)
        ]:
            self.tree_cart.heading(c, text=t)
            self.tree_cart.column(c, width=w)

        self.tree_cart.pack(
            fill="both", expand=True, pady=10
        )

        bawah = ttk.Frame(self.tab_transaksi)
        bawah.pack(fill="x")

        self.label_total = ttk.Label(
            bawah,
            text="Total: Rp0",
            font=("Arial", 14, "bold")
        )
        self.label_total.pack(side="left", padx=8)

        ttk.Button(
            bawah,
            text="Hapus Item Terpilih",
            command=self.hapus_item_cart
        ).pack(side="right", padx=5)

        ttk.Button(
            bawah,
            text="Simpan Pesanan",
            command=self.simpan_pesanan
        ).pack(side="right", padx=5)

    def buat_tab_pesanan(self):
        bar = ttk.Frame(self.tab_pesanan)
        bar.pack(fill="x", pady=5)

        ttk.Button(
            bar, text="Refresh",
            command=self.muat_pesanan
        ).pack(side="left", padx=4)

        ttk.Button(
            bar, text="Ubah Status",
            command=self.ubah_status
        ).pack(side="left", padx=4)

        ttk.Button(
            bar, text="Cetak Nota",
            command=self.cetak_nota
        ).pack(side="left", padx=4)

        cols = ("id", "meja", "tanggal", "total", "status")

        self.tree_pesanan = ttk.Treeview(
            self.tab_pesanan,
            columns=cols,
            show="headings",
            height=20
        )

        for c, t, w in [
            ("id", "ID Pesanan", 90),
            ("meja", "Meja", 100),
            ("tanggal", "Tanggal", 200),
            ("total", "Total", 180),
            ("status", "Status", 150)
        ]:
            self.tree_pesanan.heading(c, text=t)
            self.tree_pesanan.column(c, width=w)

        self.tree_pesanan.pack(
            fill="both", expand=True, pady=8
        )

    def muat_menu(self):
        try:
            rows = self.query("""
                SELECT m.id_menu, m.nama_menu,
                       k.nama_kategori, m.harga, m.stok
                FROM menu m
                JOIN kategori_menu k
                    ON m.id_kategori=k.id_kategori
                ORDER BY m.nama_menu
            """, fetch=True)

            self.tree_menu.delete(
                *self.tree_menu.get_children()
            )
            self.menu_map.clear()
            pilihan = []

            for r in rows:
                self.tree_menu.insert(
                    "", "end",
                    values=(
                        r["id_menu"],
                        r["nama_menu"],
                        r["nama_kategori"],
                        rupiah(r["harga"]),
                        r["stok"]
                    )
                )

                label = (
                    f'{r["nama_menu"]} | '
                    f'{rupiah(r["harga"])} | '
                    f'stok {r["stok"]}'
                )

                self.menu_map[label] = r
                pilihan.append(label)

            self.combo_menu["values"] = pilihan

        except Error as e:
            messagebox.showerror(
                "Database",
                f"Gagal memuat menu.\n{e}"
            )

    def cari_menu(self):
        kata = self.kata_cari.get().strip()

        try:
            rows = self.query("""
                SELECT m.id_menu, m.nama_menu,
                       k.nama_kategori, m.harga, m.stok
                FROM menu m
                JOIN kategori_menu k
                    ON m.id_kategori=k.id_kategori
                WHERE m.nama_menu LIKE %s
                   OR k.nama_kategori LIKE %s
                ORDER BY m.nama_menu
            """, (f"%{kata}%", f"%{kata}%"), True)

            self.tree_menu.delete(
                *self.tree_menu.get_children()
            )

            for r in rows:
                self.tree_menu.insert(
                    "", "end",
                    values=(
                        r["id_menu"],
                        r["nama_menu"],
                        r["nama_kategori"],
                        rupiah(r["harga"]),
                        r["stok"]
                    )
                )

        except Error as e:
            messagebox.showerror("Pencarian", str(e))

    def muat_meja(self):
        try:
            rows = self.query("""
                SELECT * FROM meja
                WHERE status_meja='Kosong'
                ORDER BY nomor_meja
            """, fetch=True)

            self.meja_map = {
                r["nomor_meja"]: r["id_meja"]
                for r in rows
            }

            self.combo_meja["values"] = list(
                self.meja_map.keys()
            )

            if self.meja_map:
                self.pilih_meja.set(
                    list(self.meja_map.keys())[0]
                )

        except Error as e:
            messagebox.showerror(
                "Database",
                f"Gagal memuat meja.\n{e}"
            )

    def muat_pesanan(self):
        try:
            rows = self.query("""
                SELECT p.id_pesanan, m.nomor_meja,
                       p.tanggal, p.total, p.status_pesanan
                FROM pesanan p
                JOIN meja m ON p.id_meja=m.id_meja
                ORDER BY p.id_pesanan DESC
            """, fetch=True)

            self.tree_pesanan.delete(
                *self.tree_pesanan.get_children()
            )

            for r in rows:
                self.tree_pesanan.insert(
                    "", "end",
                    values=(
                        r["id_pesanan"],
                        r["nomor_meja"],
                        r["tanggal"],
                        rupiah(r["total"]),
                        r["status_pesanan"]
                    )
                )

        except Error as e:
            messagebox.showerror(
                "Database",
                f"Gagal memuat pesanan.\n{e}"
            )

    def simpan_menu(self):
        if self.role != "admin":
            messagebox.showwarning(
                "Akses Ditolak",
                "Fitur ini hanya untuk admin."
            )
            return

        try:
            nama = self.nama_menu.get().strip()
            harga = float(self.harga.get())
            stok = int(self.stok.get())

            if not nama or harga < 0 or stok < 0:
                raise ValueError

            kat = self.query(
                "SELECT id_kategori FROM kategori_menu "
                "WHERE nama_kategori=%s",
                (self.kategori.get(),),
                True
            )[0]["id_kategori"]

            self.query("""
                INSERT INTO menu
                    (id_kategori,nama_menu,harga,stok)
                VALUES (%s,%s,%s,%s)
            """, (kat, nama, harga, stok))

            self.bersihkan_form_menu()
            self.muat_menu()

            messagebox.showinfo(
                "Berhasil",
                "Menu berhasil ditambahkan."
            )

        except (ValueError, IndexError):
            messagebox.showwarning(
                "Input",
                "Isi nama, harga angka, dan stok angka dengan benar."
            )

        except Error as e:
            messagebox.showerror("Database", str(e))

    def pilih_menu(self, event=None):
        selected = self.tree_menu.selection()
        if not selected:
            return

        v = self.tree_menu.item(
            selected[0], "values"
        )

        self.menu_id = int(v[0])
        self.nama_menu.set(v[1])
        self.kategori.set(v[2])
        self.harga.set(
            v[3].replace("Rp", "").replace(".", "")
        )
        self.stok.set(v[4])

    def ubah_menu(self):
        if self.role != "admin":
            messagebox.showwarning(
                "Akses Ditolak",
                "Fitur ini hanya untuk admin."
            )
            return

        if not self.menu_id:
            messagebox.showwarning(
                "Pilih menu",
                "Pilih data menu yang ingin diubah."
            )
            return

        try:
            kat = self.query(
                "SELECT id_kategori FROM kategori_menu "
                "WHERE nama_kategori=%s",
                (self.kategori.get(),),
                True
            )[0]["id_kategori"]

            self.query("""
                UPDATE menu
                SET nama_menu=%s,
                    id_kategori=%s,
                    harga=%s,
                    stok=%s
                WHERE id_menu=%s
            """, (
                self.nama_menu.get().strip(),
                kat,
                float(self.harga.get()),
                int(self.stok.get()),
                self.menu_id
            ))

            self.bersihkan_form_menu()
            self.muat_menu()

            messagebox.showinfo(
                "Berhasil",
                "Data menu diperbarui."
            )

        except (ValueError, IndexError):
            messagebox.showwarning(
                "Input",
                "Periksa kembali harga dan stok."
            )

        except Error as e:
            messagebox.showerror("Database", str(e))

    def hapus_menu(self):
        if self.role != "admin":
            messagebox.showwarning(
                "Akses Ditolak",
                "Fitur ini hanya untuk admin."
            )
            return

        if not self.menu_id:
            messagebox.showwarning(
                "Pilih menu",
                "Pilih menu yang ingin dihapus."
            )
            return

        if not messagebox.askyesno(
            "Konfirmasi", "Hapus menu ini?"
        ):
            return

        try:
            self.query(
                "DELETE FROM menu WHERE id_menu=%s",
                (self.menu_id,)
            )

            self.bersihkan_form_menu()
            self.muat_menu()

        except Error as e:
            messagebox.showerror(
                "Tidak dapat menghapus",
                f"Menu mungkin sudah pernah dipesan.\n{e}"
            )

    def bersihkan_form_menu(self):
        self.menu_id = None
        self.nama_menu.set("")
        self.kategori.set("Makanan")
        self.harga.set("")
        self.stok.set("")

    def tambah_keranjang(self):
        label = self.pilih_item.get()

        if label not in self.menu_map:
            messagebox.showwarning(
                "Menu",
                "Pilih menu terlebih dahulu."
            )
            return

        try:
            qty = int(self.jumlah.get())
            item = self.menu_map[label]

            if qty < 1 or qty > item["stok"]:
                raise ValueError

            for cart_item in self.cart:
                if cart_item["id_menu"] == item["id_menu"]:
                    if cart_item["jumlah"] + qty > item["stok"]:
                        raise ValueError

                    cart_item["jumlah"] += qty
                    break
            else:
                self.cart.append({
                    "id_menu": item["id_menu"],
                    "nama": item["nama_menu"],
                    "harga": float(item["harga"]),
                    "jumlah": qty
                })

            self.tampilkan_cart()

        except ValueError:
            messagebox.showwarning(
                "Jumlah",
                "Jumlah harus angka positif dan tidak melebihi stok."
            )

    def tampilkan_cart(self):
        self.tree_cart.delete(
            *self.tree_cart.get_children()
        )

        total = 0

        for x in self.cart:
            sub = x["harga"] * x["jumlah"]
            total += sub

            self.tree_cart.insert(
                "", "end",
                values=(
                    x["nama"],
                    rupiah(x["harga"]),
                    x["jumlah"],
                    rupiah(sub)
                )
            )

        self.label_total.config(
            text=f"Total: {rupiah(total)}"
        )

    def hapus_item_cart(self):
        sel = self.tree_cart.selection()
        if not sel:
            return

        idx = self.tree_cart.index(sel[0])
        self.cart.pop(idx)
        self.tampilkan_cart()

    def simpan_pesanan(self):
        if not self.cart:
            messagebox.showwarning(
                "Pesanan",
                "Keranjang masih kosong."
            )
            return

        meja = self.pilih_meja.get()

        if meja not in self.meja_map:
            messagebox.showwarning(
                "Meja",
                "Pilih meja yang tersedia."
            )
            return

        conn = None

        try:
            conn = koneksi()
            cur = conn.cursor()

            total = sum(
                x["harga"] * x["jumlah"]
                for x in self.cart
            )

            cur.execute(
                "INSERT INTO pesanan (id_meja,total) VALUES (%s,%s)",
                (self.meja_map[meja], total)
            )

            id_pesanan = cur.lastrowid

            for x in self.cart:
                cur.execute("""
                    INSERT INTO detail_pesanan
                        (id_pesanan,id_menu,jumlah,harga_satuan,subtotal)
                    VALUES (%s,%s,%s,%s,%s)
                """, (
                    id_pesanan,
                    x["id_menu"],
                    x["jumlah"],
                    x["harga"],
                    x["harga"] * x["jumlah"]
                ))

                cur.execute(
                    "UPDATE menu SET stok=stok-%s WHERE id_menu=%s",
                    (x["jumlah"], x["id_menu"])
                )

            cur.execute(
                "UPDATE meja SET status_meja='Terisi' WHERE id_meja=%s",
                (self.meja_map[meja],)
            )

            conn.commit()

            messagebox.showinfo(
                "Berhasil",
                f"Pesanan tersimpan. Nomor pesanan: {id_pesanan}"
            )

            self.cart.clear()
            self.tampilkan_cart()
            self.muat_menu()
            self.muat_meja()
            self.muat_pesanan()

        except Error as e:
            if conn:
                conn.rollback()

            messagebox.showerror(
                "Database",
                f"Pesanan gagal disimpan.\n{e}"
            )

        finally:
            if conn:
                conn.close()

    def ubah_status(self):
        sel = self.tree_pesanan.selection()

        if not sel:
            messagebox.showwarning(
                "Pesanan",
                "Pilih pesanan terlebih dahulu."
            )
            return

        v = self.tree_pesanan.item(
            sel[0], "values"
        )
        pid = int(v[0])

        win = tk.Toplevel(self.root)
        win.title("Ubah Status Pesanan")
        win.geometry("280x140")

        ttk.Label(
            win, text=f"Pesanan #{pid}"
        ).pack(pady=8)

        status = tk.StringVar(value=v[4])

        cb = ttk.Combobox(
            win,
            textvariable=status,
            values=[
                "Menunggu",
                "Diproses",
                "Selesai",
                "Dibatalkan"
            ],
            state="readonly"
        )
        cb.pack(pady=5)

        def simpan():
            try:
                self.query(
                    "UPDATE pesanan SET status_pesanan=%s "
                    "WHERE id_pesanan=%s",
                    (status.get(), pid)
                )

                if status.get() in ("Selesai", "Dibatalkan"):
                    self.query("""
                        UPDATE meja
                        SET status_meja='Kosong'
                        WHERE id_meja=(
                            SELECT id_meja FROM pesanan
                            WHERE id_pesanan=%s
                        )
                    """, (pid,))

                self.muat_pesanan()
                self.muat_meja()
                win.destroy()

            except Error as e:
                messagebox.showerror("Database", str(e))

        ttk.Button(
            win, text="Simpan",
            command=simpan
        ).pack(pady=8)


    # ==============================
    # DASHBOARD, LAPORAN, DAN BACKUP
    # ==============================

    def buat_tab_dashboard(self):
        ttk.Label(
            self.tab_dashboard,
            text="RINGKASAN PENJUALAN RESTORAN",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", pady=(0, 12))

        kartu = ttk.Frame(self.tab_dashboard)
        kartu.pack(fill="x", pady=5)

        self.stat_transaksi = tk.StringVar(value="0")
        self.stat_omzet = tk.StringVar(value="Rp0")
        self.stat_menu = tk.StringVar(value="-")

        for judul, variabel in [
            ("Jumlah Pesanan", self.stat_transaksi),
            ("Total Omzet", self.stat_omzet),
            ("Menu Terlaris", self.stat_menu),
        ]:
            box = ttk.LabelFrame(kartu, text=judul, padding=12)
            box.pack(side="left", fill="both", expand=True, padx=5)
            ttk.Label(box, textvariable=variabel,
                      font=("Arial", 15, "bold")).pack(pady=8)

        ttk.Button(
            self.tab_dashboard,
            text="Perbarui Statistik",
            command=self.perbarui_dashboard
        ).pack(anchor="e", pady=8)

        ttk.Label(
            self.tab_dashboard,
            text="Grafik omzet 7 hari terakhir",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        self.grafik = tk.Canvas(
            self.tab_dashboard, height=300,
            background="white", highlightthickness=1,
            highlightbackground="#cccccc"
        )
        self.grafik.pack(fill="both", expand=True, pady=8)
        self.grafik.bind("<Configure>", lambda event: self.perbarui_dashboard())
        self.perbarui_dashboard()

    def perbarui_dashboard(self):
        try:
            ringkas = self.query("""
                SELECT COUNT(*) AS jumlah, COALESCE(SUM(total),0) AS omzet
                FROM pesanan
                WHERE status_pesanan <> 'Dibatalkan'
            """, fetch=True)[0]

            terlaris = self.query("""
                SELECT m.nama_menu, COALESCE(SUM(d.jumlah),0) AS terjual
                FROM detail_pesanan d
                JOIN menu m ON m.id_menu=d.id_menu
                JOIN pesanan p ON p.id_pesanan=d.id_pesanan
                WHERE p.status_pesanan <> 'Dibatalkan'
                GROUP BY m.id_menu, m.nama_menu
                ORDER BY terjual DESC
                LIMIT 1
            """, fetch=True)

            self.stat_transaksi.set(str(ringkas["jumlah"]))
            self.stat_omzet.set(rupiah(ringkas["omzet"]))
            self.stat_menu.set(
                f'{terlaris[0]["nama_menu"]} ({terlaris[0]["terjual"]})'
                if terlaris else "Belum ada"
            )

            harian = self.query("""
                SELECT DATE(tanggal) AS hari, COALESCE(SUM(total),0) AS omzet
                FROM pesanan
                WHERE tanggal >= CURDATE() - INTERVAL 6 DAY
                  AND status_pesanan <> 'Dibatalkan'
                GROUP BY DATE(tanggal)
                ORDER BY hari
            """, fetch=True)
            data = {str(r["hari"]): float(r["omzet"]) for r in harian}
            self.gambar_grafik(data)
        except Exception as e:
            if hasattr(self, "grafik"):
                self.grafik.delete("all")
                self.grafik.create_text(
                    20, 20, anchor="nw",
                    text=f"Statistik belum dapat dimuat: {e}",
                    fill="red"
                )

    def gambar_grafik(self, data):
        if not hasattr(self, "grafik"):
            return
        self.grafik.delete("all")
        width = max(self.grafik.winfo_width(), 500)
        height = max(self.grafik.winfo_height(), 250)
        kiri, kanan, atas, bawah = 65, 20, 25, 45
        plot_w = width - kiri - kanan
        plot_h = height - atas - bawah
        labels = [(date.today().fromordinal(date.today().toordinal()-i)).isoformat()
                  for i in range(6, -1, -1)]
        values = [data.get(x, 0) for x in labels]
        maksimum = max(values) if max(values, default=0) > 0 else 1

        for i in range(5):
            y = atas + plot_h - (plot_h * i / 4)
            self.grafik.create_line(kiri, y, width-kanan, y, fill="#e5e7eb")
            self.grafik.create_text(kiri-8, y, text=f"{int(maksimum*i/4):,}",
                                    anchor="e", font=("Arial", 8))

        jarak = plot_w / 7
        lebar = min(35, jarak * 0.55)
        for i, (label, nilai) in enumerate(zip(labels, values)):
            tinggi = (nilai / maksimum) * plot_h
            x = kiri + i * jarak + (jarak-lebar)/2
            y = atas + plot_h - tinggi
            self.grafik.create_rectangle(x, y, x+lebar, atas+plot_h,
                                         fill="#2878b5", outline="")
            self.grafik.create_text(x+lebar/2, atas+plot_h+15,
                                    text=label[5:], font=("Arial", 8))

    def buat_tab_laporan(self):
        ttk.Label(
            self.tab_laporan,
            text="EKSPOR LAPORAN DAN DATABASE",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", pady=(0, 15))

        ttk.Label(
            self.tab_laporan,
            text="Pilih fitur yang ingin digunakan:",
        ).pack(anchor="w", pady=5)

        ttk.Button(
            self.tab_laporan, text="Ekspor Laporan Excel (.xlsx)",
            command=self.ekspor_excel
        ).pack(fill="x", pady=6)

        ttk.Button(
            self.tab_laporan, text="Ekspor Laporan PDF (.pdf)",
            command=self.ekspor_laporan_pdf
        ).pack(fill="x", pady=6)

        ttk.Separator(self.tab_laporan).pack(fill="x", pady=15)

        ttk.Button(
            self.tab_laporan, text="Backup Database (.json)",
            command=self.backup_database
        ).pack(fill="x", pady=6)

        ttk.Button(
            self.tab_laporan, text="Restore Database dari Backup",
            command=self.restore_database
        ).pack(fill="x", pady=6)

        ttk.Label(
            self.tab_laporan,
            text="Catatan: Restore akan mengganti seluruh isi database restoran_db.\n"
                 "Pastikan membuat backup terbaru sebelum melakukan restore.",
            foreground="#a33"
        ).pack(anchor="w", pady=15)

    def ambil_data_laporan(self):
        return self.query("""
            SELECT p.id_pesanan, m.nomor_meja, p.tanggal,
                   p.total, p.status_pesanan
            FROM pesanan p
            JOIN meja m ON m.id_meja=p.id_meja
            ORDER BY p.tanggal DESC, p.id_pesanan DESC
        """, fetch=True)

    def ekspor_excel(self):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            messagebox.showerror(
                "Modul belum tersedia",
                "Pasang openpyxl melalui Terminal: python -m pip install openpyxl"
            )
            return

        nama = filedialog.asksaveasfilename(
            parent=self.root, title="Simpan Laporan Excel",
            defaultextension=".xlsx",
            initialfile="laporan_penjualan.xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not nama:
            return
        try:
            rows = self.ambil_data_laporan()
            wb = Workbook()
            ws = wb.active
            ws.title = "Laporan Penjualan"
            ws.append(["ID Pesanan", "Nomor Meja", "Tanggal", "Total", "Status"])
            for r in rows:
                ws.append([r["id_pesanan"], r["nomor_meja"],
                           str(r["tanggal"]), float(r["total"]),
                           r["status_pesanan"]])
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="24527A")
                cell.alignment = Alignment(horizontal="center")
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for col, width in {"A":14, "B":14, "C":22, "D":18, "E":18}.items():
                ws.column_dimensions[col].width = width
            wb.save(nama)
            messagebox.showinfo("Berhasil", f"Laporan Excel tersimpan:\n{nama}")
        except Exception as e:
            messagebox.showerror("Ekspor Excel", str(e))

    def ekspor_laporan_pdf(self):
        nama = filedialog.asksaveasfilename(
            parent=self.root, title="Simpan Laporan PDF",
            defaultextension=".pdf", initialfile="laporan_penjualan.pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        if not nama:
            return
        try:
            rows = self.ambil_data_laporan()
            doc = SimpleDocTemplate(nama, pagesize=(595, 842))
            styles = getSampleStyleSheet()
            isi = [Paragraph("LAPORAN PENJUALAN RESTORAN", styles["Title"]),
                   Spacer(1, 16)]
            data = [["ID", "Meja", "Tanggal", "Total", "Status"]]
            for r in rows:
                data.append([str(r["id_pesanan"]), str(r["nomor_meja"]),
                             str(r["tanggal"]), rupiah(r["total"]),
                             str(r["status_pesanan"])])
            if not rows:
                data.append(["-", "-", "Belum ada data", "-", "-"])
            tabel = Table(data, repeatRows=1,
                          colWidths=[45, 55, 150, 110, 100])
            tabel.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#24527A")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("FONTSIZE", (0,0), (-1,-1), 8),
                ("PADDING", (0,0), (-1,-1), 6),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ]))
            isi.append(tabel)
            omzet = sum(float(r["total"]) for r in rows
                        if r["status_pesanan"] != "Dibatalkan")
            isi.extend([Spacer(1, 15),
                        Paragraph(f"Total omzet (tidak termasuk dibatalkan): {rupiah(omzet)}",
                                  styles["Heading3"])])
            doc.build(isi)
            messagebox.showinfo("Berhasil", f"Laporan PDF tersimpan:\n{nama}")
        except Exception as e:
            messagebox.showerror("Ekspor PDF", str(e))

    @staticmethod
    def nilai_json(nilai):
        if isinstance(nilai, (datetime, date)):
            return nilai.isoformat()
        if isinstance(nilai, Decimal):
            return str(nilai)
        if isinstance(nilai, bytes):
            return {"__bytes__": nilai.hex()}
        return str(nilai) if nilai is not None else None

    def backup_database(self):
        nama = filedialog.asksaveasfilename(
            parent=self.root, title="Simpan Backup Database",
            defaultextension=".json", initialfile="backup_restoran.json",
            filetypes=[("Backup JSON", "*.json")]
        )
        if not nama:
            return
        conn = None
        cur = None
        try:
            conn = koneksi()
            cur = conn.cursor()
            cur.execute("SHOW TABLES")
            nama_tabel = [baris[0] for baris in cur.fetchall()]
            backup = {"database": DB_CONFIG["database"], "tables": []}
            for tabel in nama_tabel:
                aman = tabel.replace("`", "``")
                cur.execute(f"SHOW CREATE TABLE `{aman}`")
                create_sql = cur.fetchone()[1]
                cur.execute(f"SELECT * FROM `{aman}`")
                kolom = [d[0] for d in cur.description]
                baris_data = cur.fetchall()
                backup["tables"].append({
                    "name": tabel,
                    "create_sql": create_sql,
                    "columns": kolom,
                    "rows": [[self.nilai_json(v) for v in row]
                             for row in baris_data]
                })
            with open(nama, "w", encoding="utf-8") as f:
                json.dump(backup, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Backup Berhasil", f"Backup tersimpan:\n{nama}")
        except Exception as e:
            messagebox.showerror("Backup Gagal", str(e))
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def restore_database(self):
        nama = filedialog.askopenfilename(
            parent=self.root, title="Pilih File Backup",
            filetypes=[("Backup JSON", "*.json")]
        )
        if not nama:
            return
        if not messagebox.askyesno(
            "Konfirmasi Restore",
            "PERINGATAN: seluruh tabel dan data database restoran_db akan diganti\n"
            "dengan isi backup. Lanjutkan?"
        ):
            return
        conn = None
        cur = None
        try:
            with open(nama, "r", encoding="utf-8") as f:
                backup = json.load(f)
            if backup.get("database") != DB_CONFIG["database"]:
                raise ValueError("File backup bukan untuk database restoran_db.")
            tabel = backup.get("tables")
            if not isinstance(tabel, list) or not tabel:
                raise ValueError("Isi file backup tidak valid.")

            conn = koneksi()
            cur = conn.cursor()
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            cur.execute("SHOW TABLES")
            for row in cur.fetchall():
                aman = row[0].replace("`", "``")
                cur.execute(f"DROP TABLE IF EXISTS `{aman}`")

            for item in tabel:
                cur.execute(item["create_sql"])
                kolom = item.get("columns", [])
                data = item.get("rows", [])
                if kolom and data:
                    daftar_kolom = ", ".join(
                        "`" + c.replace("`", "``") + "`" for c in kolom
                    )
                    placeholder = ", ".join(["%s"] * len(kolom))
                    sql = (f"INSERT INTO `{item['name'].replace('`', '``')}` "
                           f"({daftar_kolom}) VALUES ({placeholder})")
                    for row in data:
                        row = [bytes.fromhex(v["__bytes__"])
                               if isinstance(v, dict) and "__bytes__" in v else v
                               for v in row]
                        cur.execute(sql, row)
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
            conn.commit()
            messagebox.showinfo(
                "Restore Berhasil",
                "Database berhasil dipulihkan. Aplikasi akan dimuat ulang."
            )
            self.muat_menu()
            self.muat_meja()
            self.muat_pesanan()
            self.perbarui_dashboard()
        except Exception as e:
            if conn:
                conn.rollback()
                try:
                    cur.execute("SET FOREIGN_KEY_CHECKS=1")
                except Exception:
                    pass
            messagebox.showerror("Restore Gagal", str(e))
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()


    def cetak_nota(self):
        sel = self.tree_pesanan.selection()

        if not sel:
            messagebox.showwarning(
                "Nota",
                "Pilih pesanan yang ingin dicetak."
            )
            return

        v = self.tree_pesanan.item(
            sel[0], "values"
        )
        pid = int(v[0])

        try:
            header = self.query("""
                SELECT p.id_pesanan, m.nomor_meja,
                       p.tanggal, p.total, p.status_pesanan
                FROM pesanan p
                JOIN meja m ON p.id_meja = m.id_meja
                WHERE p.id_pesanan = %s
            """, (pid,), True)

            if not header:
                messagebox.showerror(
                    "Nota",
                    "Pesanan tidak ditemukan."
                )
                return

            h = header[0]

            rows = self.query("""
                SELECT m.nama_menu, d.jumlah,
                       d.harga_satuan, d.subtotal
                FROM detail_pesanan d
                JOIN menu m ON d.id_menu = m.id_menu
                WHERE d.id_pesanan = %s
            """, (pid,), True)

            nama_file = filedialog.asksaveasfilename(
                parent=self.root,
                title="Simpan Nota PDF",
                initialfile=f"nota_pesanan_{pid}.pdf",
                defaultextension=".pdf",
                filetypes=[("File PDF", "*.pdf")]
            )

            if not nama_file:
                return

            doc = SimpleDocTemplate(
                nama_file,
                pagesize=A6,
                rightMargin=18,
                leftMargin=18,
                topMargin=20,
                bottomMargin=20
            )

            styles = getSampleStyleSheet()

            judul = ParagraphStyle(
                "JudulNota",
                parent=styles["Title"],
                fontSize=16,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#17365D"),
                spaceAfter=4
            )

            tengah = ParagraphStyle(
                "Tengah",
                parent=styles["Normal"],
                fontSize=8,
                alignment=TA_CENTER
            )

            normal = ParagraphStyle(
                "NormalKecil",
                parent=styles["Normal"],
                fontSize=8
            )

            isi = []

            isi.append(Paragraph("RESTORAN", judul))
            isi.append(Paragraph("NOTA PEMBAYARAN", tengah))
            isi.append(Spacer(1, 12))

            isi.append(Paragraph(
                f"No. Pesanan: {h['id_pesanan']}",
                normal
            ))

            isi.append(Paragraph(
                f"Meja: {escape(str(h['nomor_meja']))}",
                normal
            ))

            isi.append(Paragraph(
                f"Tanggal: {h['tanggal']}",
                normal
            ))

            isi.append(Paragraph(
                f"Status: {escape(str(h['status_pesanan']))}",
                normal
            ))

            isi.append(Spacer(1, 10))

            data = [["Menu", "Qty", "Harga", "Subtotal"]]

            for r in rows:
                data.append([
                    Paragraph(
                        escape(str(r["nama_menu"])),
                        normal
                    ),
                    str(r["jumlah"]),
                    rupiah(r["harga_satuan"]),
                    rupiah(r["subtotal"])
                ])

            tabel = Table(
                data,
                colWidths=[85, 27, 65, 84],
                repeatRows=1
            )

            tabel.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0),
                 colors.HexColor("#17365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))

            isi.append(tabel)
            isi.append(Spacer(1, 12))

            isi.append(Paragraph(
                f"<b>TOTAL: {rupiah(h['total'])}</b>",
                normal
            ))

            isi.append(Spacer(1, 20))

            isi.append(Paragraph(
                "Terima kasih telah berkunjung!",
                tengah
            ))

            isi.append(Paragraph(
                "Selamat menikmati hidangan Anda.",
                tengah
            ))

            doc.build(isi)

            messagebox.showinfo(
                "Berhasil",
                f"Nota PDF berhasil dibuat!\n\n{nama_file}"
            )

        except Exception as e:
            messagebox.showerror(
                "Gagal Membuat PDF",
                str(e)
            )



class LoginWindow:
    def __init__(self, root, on_login):
        self.root = root
        self.on_login = on_login

        # Membuat jendela login
        self.window = tk.Toplevel(root)
        self.window.title("Login Restoran")
        self.window.geometry("380x300")
        self.window.resizable(False, False)

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.tutup
        )

        frame = ttk.Frame(
            self.window,
            padding=25
        )
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="LOGIN RESTORAN",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        ttk.Label(
            frame,
            text="Username"
        ).pack(anchor="w")

        self.username = tk.StringVar()

        ttk.Entry(
            frame,
            textvariable=self.username
        ).pack(fill="x", pady=7)

        ttk.Label(
            frame,
            text="Password"
        ).pack(anchor="w")

        self.password = tk.StringVar()

        ttk.Entry(
            frame,
            textvariable=self.password,
            show="*"
        ).pack(fill="x", pady=7)

        ttk.Button(
            frame,
            text="MASUK",
            command=self.proses_login
        ).pack(fill="x", pady=15)

        self.window.bind(
            "<Return>",
            lambda event: self.proses_login()
        )

        # Menampilkan jendela login
        self.window.update_idletasks()
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def proses_login(self):
        username = self.username.get().strip()
        password = self.password.get()

        if not username or not password:
            messagebox.showwarning(
                "Peringatan",
                "Username dan password wajib diisi.",
                parent=self.window
            )
            return

        conn = None
        cur = None

        try:
            conn = koneksi()
            cur = conn.cursor(dictionary=True)

            cur.execute(
                """
                SELECT id_user, username, password, role
                FROM users
                WHERE username = %s
                """,
                (username,)
            )

            user = cur.fetchone()

            password_hash = hashlib.sha256(
                password.encode("utf-8")
            ).hexdigest()

            if user and user["password"] == password_hash:

                self.window.destroy()

                self.root.deiconify()
                self.root.update()

                self.on_login(user)

            else:
                messagebox.showerror(
                    "Login Gagal",
                    "Username atau password salah.",
                    parent=self.window
                )

                self.password.set("")

        except Error as e:
            messagebox.showerror(
                "Kesalahan Database",
                f"Gagal menghubungkan database:\n{e}",
                parent=self.window
            )

        except Exception as e:
            messagebox.showerror(
                "Kesalahan",
                str(e),
                parent=self.window
            )

        finally:
            if cur:
                cur.close()

            if conn:
                conn.close()

    def tutup(self):
        self.root.destroy()


# ==============================
# MENJALANKAN APLIKASI
# ==============================

if __name__ == "__main__":

    root = tk.Tk()
    root.withdraw()

    def mulai_aplikasi(user):
        try:
            AplikasiRestoran(root, user)

        except Exception as e:
            messagebox.showerror(
                "Kesalahan Aplikasi",
                str(e)
            )
            root.destroy()

    LoginWindow(root, mulai_aplikasi)   

    root.mainloop()
