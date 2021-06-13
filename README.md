# Informa

**Ini Forum Mahasiswa** - Proyek Akhir Kelompok 8A Praktikum Sistem Basis Data

Teknik Komputer Universitas Indonesia

## Anggota

* **Febriana Pasonang Sidauruk** (1906300725)
* **Rodriguez Breil Soenoto** (1906355592)
* **Salma Shafira** (1906300832)
* **Tedi Setiawan** (1906300864)

## Deskripsi

Informa merupakan web application berbentuk forum

* **Server**: Python dengan library Flask
* **Database**: PostgreSQL

## Prerequisites

* flask
* flask_sqlalchemy
* psycopg2

## Isi file
1. 	**app/static/** - 
	Berisi CSS stylesheet, Javascript, serta gambar yang digunakan dalam tampilan halaman
	
2. 	**app/templates/** - 
	Berisi HTML yang digunakan sebagai dasar untuk membentuk halaman.
	Untuk header dan footer digunakan file _.html dan __.html.
	Khusus untuk posts.html (halaman isi thread) digunakan script dengan teknik AJAX menggunakan XMLHttpRequest() untuk mengirim reaksi pada post tanpa melalui halaman lain.
	
3. 	**app/app.py** - 
	Untuk menginisialisasi web server dan melakukan koneksi pada database
	
4. 	**app/database.py** - 
	Berisi function run yang berfungsi untuk mempersingkat panggilan untuk SQL query, contohnya: `run(‘select * from forum_user;’)`
	Output berupa hasil query dalam bentuk baris-baris

5. 	**informa.psql** - 
	Contoh isi database `informa`
	* Password (admin): admin
	* Password (user1, user2): user
	
6. 	**app/login.py** - 
	Berfungsi untuk membantu meng-handle browser session dalam hal login dan logout
	Mengambil dan menetapkan ID dari user yang sedang login dalam suatu browser session tertentu (`get_logged_in_user()`, `login_user()`)
	Menghapus ID user dari browser session (`logout_user()`)
	
7. 	**app/routes.py** - 
	Berisi kode kendali untuk seluruh laman dalam website (inti aplikasi)
