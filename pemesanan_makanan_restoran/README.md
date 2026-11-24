# Sistem Pemesanan Makanan Restoran

Aplikasi desktop sederhana menggunakan Python, Tkinter, dan MySQL (XAMPP).

## Fitur
- CRUD data menu makanan/minuman.
- Data kategori menu dan meja.
- Pemesanan berdasarkan meja.
- Keranjang pesanan dan total otomatis.
- Pengurangan stok setelah pesanan disimpan.
- Status pesanan: Menunggu, Diproses, Selesai, Dibatalkan.
- Pembuatan nota pembayaran dalam file TXT.

## 1. Persiapan
1. Install Python 3.
2. Install XAMPP dan jalankan **MySQL** dari Control Panel XAMPP.
3. Buka phpMyAdmin (`http://localhost/phpmyadmin`).
4. Pilih tab **Import**, lalu import file `database.sql` dari folder ini.
5. Pastikan database `restoran_db` berhasil dibuat.

## 2. Atur koneksi database
Buka `app.py`, cari bagian `DB_CONFIG`:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "restoran_db",
}
```
Jika MySQL kamu memakai password, isi nilai `password`.

## 3. Install library
Buka terminal VS Code pada folder proyek, jalankan:
```bash
python -m pip install -r requirements.txt
```

## 4. Jalankan aplikasi
```bash
python app.py
```

## 5. Cara menggunakan
1. Buka tab **Data Menu** untuk menambah, mengubah, atau menghapus menu.
2. Buka tab **Pemesanan**, pilih meja yang kosong.
3. Pilih menu, masukkan jumlah, lalu tekan **Tambah**.
4. Tekan **Simpan Pesanan** untuk menyimpan transaksi.
5. Buka tab **Data Pesanan** untuk melihat transaksi.
6. Pilih pesanan lalu tekan **Ubah Status** atau **Cetak Nota**.

## Struktur database dan relasi
- `kategori_menu` 1 ke banyak `menu`.
- `meja` 1 ke banyak `pesanan`.
- `pesanan` 1 ke banyak `detail_pesanan`.
- `menu` 1 ke banyak `detail_pesanan`.

Primary key:
- kategori_menu.id_kategori
- menu.id_menu
- meja.id_meja
- pesanan.id_pesanan
- detail_pesanan.id_detail

Foreign key:
- menu.id_kategori -> kategori_menu.id_kategori
- pesanan.id_meja -> meja.id_meja
- detail_pesanan.id_pesanan -> pesanan.id_pesanan
- detail_pesanan.id_menu -> menu.id_menu

## Catatan
Ini merupakan versi dasar untuk tugas sekolah. Uji aplikasi setelah database diimpor. Fitur login, ekspor Excel/PDF, dashboard grafik, backup/restore, dan file EXE dapat dikembangkan sebagai tahap lanjutan.
