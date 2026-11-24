CREATE DATABASE IF NOT EXISTS restoran_db;
USE restoran_db;

CREATE TABLE IF NOT EXISTS kategori_menu (
    id_kategori INT AUTO_INCREMENT PRIMARY KEY,
    nama_kategori VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS menu (
    id_menu INT AUTO_INCREMENT PRIMARY KEY,
    id_kategori INT NOT NULL,
    nama_menu VARCHAR(100) NOT NULL,
    harga DECIMAL(12,2) NOT NULL,
    stok INT NOT NULL DEFAULT 0,
    FOREIGN KEY (id_kategori) REFERENCES kategori_menu(id_kategori)
);

CREATE TABLE IF NOT EXISTS meja (
    id_meja INT AUTO_INCREMENT PRIMARY KEY,
    nomor_meja VARCHAR(10) NOT NULL UNIQUE,
    kapasitas INT NOT NULL DEFAULT 2,
    status_meja ENUM('Kosong','Terisi') NOT NULL DEFAULT 'Kosong'
);

CREATE TABLE IF NOT EXISTS pesanan (
    id_pesanan INT AUTO_INCREMENT PRIMARY KEY,
    id_meja INT NOT NULL,
    tanggal DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) NOT NULL DEFAULT 0,
    status_pesanan ENUM('Menunggu','Diproses','Selesai','Dibatalkan') NOT NULL DEFAULT 'Menunggu',
    FOREIGN KEY (id_meja) REFERENCES meja(id_meja)
);

CREATE TABLE IF NOT EXISTS detail_pesanan (
    id_detail INT AUTO_INCREMENT PRIMARY KEY,
    id_pesanan INT NOT NULL,
    id_menu INT NOT NULL,
    jumlah INT NOT NULL,
    harga_satuan DECIMAL(12,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (id_pesanan) REFERENCES pesanan(id_pesanan) ON DELETE CASCADE,
    FOREIGN KEY (id_menu) REFERENCES menu(id_menu)
);

INSERT INTO kategori_menu (nama_kategori)
SELECT 'Makanan' WHERE NOT EXISTS (SELECT 1 FROM kategori_menu WHERE nama_kategori='Makanan');
INSERT INTO kategori_menu (nama_kategori)
SELECT 'Minuman' WHERE NOT EXISTS (SELECT 1 FROM kategori_menu WHERE nama_kategori='Minuman');

INSERT INTO meja (nomor_meja, kapasitas)
SELECT 'M01', 4 WHERE NOT EXISTS (SELECT 1 FROM meja WHERE nomor_meja='M01');
INSERT INTO meja (nomor_meja, kapasitas)
SELECT 'M02', 2 WHERE NOT EXISTS (SELECT 1 FROM meja WHERE nomor_meja='M02');
INSERT INTO meja (nomor_meja, kapasitas)
SELECT 'M03', 4 WHERE NOT EXISTS (SELECT 1 FROM meja WHERE nomor_meja='M03');

INSERT INTO menu (id_kategori, nama_menu, harga, stok)
SELECT k.id_kategori, 'Nasi Goreng', 18000, 30 FROM kategori_menu k
WHERE k.nama_kategori='Makanan' AND NOT EXISTS (SELECT 1 FROM menu WHERE nama_menu='Nasi Goreng');
INSERT INTO menu (id_kategori, nama_menu, harga, stok)
SELECT k.id_kategori, 'Mie Ayam', 15000, 25 FROM kategori_menu k
WHERE k.nama_kategori='Makanan' AND NOT EXISTS (SELECT 1 FROM menu WHERE nama_menu='Mie Ayam');
INSERT INTO menu (id_kategori, nama_menu, harga, stok)
SELECT k.id_kategori, 'Es Teh', 5000, 40 FROM kategori_menu k
WHERE k.nama_kategori='Minuman' AND NOT EXISTS (SELECT 1 FROM menu WHERE nama_menu='Es Teh');
