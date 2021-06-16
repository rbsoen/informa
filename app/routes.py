# Fungsi utama website Informa

# umum
from flask import Blueprint, render_template, request, redirect, url_for, jsonify

# fungsi-fungsi database
from database import run

# manajemen login
from login import login_user, get_logged_in_user, logout_user

# fitur keamanan
from werkzeug.security import generate_password_hash, check_password_hash

# manipulasi format waktu dan tanggal
from datetime import datetime

# register URL untuk fungsi website
site = Blueprint('site', __name__)

# fungsi umum
get_user = lambda id: run('select * from forum_user where id=:id', id=id).fetchone()
make_user_link = lambda id: (url_for('site.show_user', user_id=id), get_user(id).nama or 'Tidak ada')
get_topik = lambda id: run('select * from topik where id=:id', id=id).fetchone()

# Mengambil row yang berisi user yang sedang log in
def get_current_user():
    user_id = get_logged_in_user()
    if user_id is not None:
        username = run('''
            select * from forum_user
            where id=:uid
            ''',
            uid=user_id).fetchone()
        return username
    return None

# ------------------------ Main page ------------------------ #
# Halaman utama, menampilkan topik-topik yang ada.
# Ini juga akan melakukan setup database
# 
# Implementasi: Create, Read
#
@site.route('/')
def main():
    # buat tipe data Reaksi
    #run('''
    #    do $$
    #    begin
    #        if not exists(select 1 from pg_type where typname='reaksi') then
    #            create type reaksi as enum
    #            ('Terkejut', 'Senang', 'Marah', 'Bangga');
    #        end if;
    #    end $$;
    #''')
    # jika tidak ada tabelnya, buat secara otomatis
    run('''
        create table if not exists forum_user(
            id serial primary key,
            email varchar unique,
            password varchar,
            nama varchar(64),
            institusi varchar,
            is_admin boolean default false
        );
        
        create table if not exists topik(
            id serial primary key,
            judul varchar unique
        );
        
        create table if not exists thread(
            id serial primary key,
            judul varchar,
            waktu timestamp default now(),
            topik int references topik(id),
            pembuat int references forum_user(id)
        );
        
        create table if not exists post(
            id serial primary key,
            judul varchar,
            isi varchar,
            waktu timestamp default now(),
            thread int references thread(id),
            pembuat int references forum_user(id)
        );
        
        create table if not exists reaksi_post(
            reaksi reaksi,
            dari int references forum_user(id),
            post int references post(id)
        )
    ''')
    
    # daftar topik
    topics = run('select * from topik;')
    return render_template('topics.html', topics=topics, current_user=get_current_user())

# ------------------------ Topic page ------------------------ #
# Halaman ini berisi isi dari topik yaitu thread-thread di
# dalamnya.
#
# Implementasi: Read
#
@site.route('/topik/<topic_id>', methods=['GET'])
def show_topic(topic_id):
    # Ambil topik
    topic = run('''
        select * from topik
        where id=:id
        ''', id=topic_id
        ).fetchone()
    
    if topic is None:
        return render_template('generic_message.html', message='Topik tidak ditemukan.', current_user=get_current_user())
    
    # Daftar thread dalam topik
    threads = run('''
        select * from thread
        where topik=:id
        ''', id=topic_id
    )
    
    return render_template('threads.html', threads=threads, topic=topic, make_user_link=make_user_link, current_user=get_current_user())

# ------------------------ Add topic ------------------------ #
# Halaman untuk admin menambahkan topik.
# User selain admin tidak boleh menambahkan topik.
#
# Implementasi: Create
#
@site.route('/admin', methods=['GET'])
def admin():
    return render_template('admin.html')
    
@site.route('/topik/add', methods=['POST'])
def add_topic():
    user = get_current_user()
    
    if not user:
        return render_template('admin.html', message='Anda tidak dapat menambah topik.', current_user=user) 
    
    if not user.is_admin:
        return render_template('admin.html', message='Anda tidak dapat menambah topik.', current_user=user) 
    
    judul = request.form.get('judul')
    
    if not judul:
        return render_template('admin.html', message='Judul tidak boleh kosong.', current_user=get_current_user()) 
    
    topik = run('''
        select * from topik
        where judul=:judul
        ''', judul=judul
        ).fetchone()
    
    if topik is None:
        run('''
            insert into topik (judul)
            values (:judul);
        ''', judul=judul)
        return redirect(url_for('site.main'))
    
    return render_template('generic_message.html', message='Topik telah ada.', current_user=get_current_user())
    

# ------------------------ Thread page ------------------------ #
# Halaman thread yang menampilkan semua post dalam thread
#
# Implementasi: Read
#
@site.route('/thread/<thread_id>', methods=['GET'])
def show_thread(thread_id):
    # cari thread dalam database
    thread = run('''
        select * from thread
        where id=:id
        ''', id=thread_id
        ).fetchone()
    
    if thread is None:
        return render_template('generic_message.html', message='Thread tidak ditemukan.', current_user=get_current_user())
    
    # tampilkan semua post dalam thread
    posts = run('''
        select * from post
        where thread=:id
        order by id asc;
        ''', id=thread_id
    )
    
    # fungsi untuk menampilkan reaksi dan memformat tanggal dan waktu
    find_reactions = lambda post: run('select * from reaksi_post where post=:post', post=post)
    reformat_time = lambda time: datetime.strftime(time, '%c')
    
    return render_template('posts.html', thread=thread, posts=posts, make_user_link=make_user_link, get_topik=get_topik, reformat_time=reformat_time, find_reactions=find_reactions, current_user=get_current_user())

# ------------------------ Form posting dalam thread ------------------------ #
# Memungkinkan user untuk menambahkan postingan dalam sebuah thread.
#
# Implementasi: Create
#
@site.route('/thread/<thread_id>/reply', methods=['GET'])
def thread_reply_form(thread_id):
    if get_logged_in_user() is None:
        return render_template('generic_message.html', message='Anda tidak dapat memberikan balasan pada thread ini.')
    
    thread = run('''
        select * from thread
        where id=:id
        ''', id=thread_id
        ).fetchone()
    
    if thread is None:
        return render_template('generic_message.html', message='Thread tidak ditemukan.', current_user=get_current_user())
     
    return render_template('reply_to_thread.html', current_user=get_current_user(), thread=thread)

@site.route('/thread/<thread_id>/reply', methods=['POST'])
def thread_reply_form_submit(thread_id):
    if get_logged_in_user() is None:
        return render_template('generic_message.html', message='Anda tidak dapat memberikan balasan pada thread ini.')
    
    thread = run('''
        select * from thread
        where id=:id
        ''', id=thread_id
        ).fetchone()
    
    if thread is None:
        return render_template('generic_message.html', message='Thread tidak ditemukan.', current_user=get_current_user())
    
    judul = request.form.get('judul')
    isi = request.form.get('isi')
    
    if not judul:
        return render_template('reply_to_thread.html', current_user=get_current_user(), thread=thread, message="Judul tidak boleh kosong.")
    if not isi:
        return render_template('reply_to_thread.html', current_user=get_current_user(), thread=thread, message="Isi tidak boleh kosong.")
    
    # masukkan balasan untuk thread
    run('''
        insert into post(judul, isi, thread, pembuat)
        values (:judul, :isi, :thread, :pembuat);
    ''',
        judul=judul,
        isi=isi,
        thread=thread.id,
        pembuat=get_logged_in_user()
    )
    
    return redirect(url_for('site.show_thread', thread_id=thread_id))

# ------------------------ Delete thread ------------------------ #
# Hanya untuk admin
#
# Implementasi: Delete
#
@site.route('/thread/<thread_id>/delete', methods=['GET'])
def thread_delete(thread_id):
    if get_logged_in_user() is None:
        return render_template('generic_message.html', message='Anda tidak dapat menghapus thread.')
    
    if get_current_user().is_admin is not True:
        return render_template('generic_message.html', message='Anda tidak dapat menghapus thread.')
    
    thread = run('''
        select * from thread
        where id=:id
        ''', id=thread_id
        ).fetchone()
    
    if thread is None:
        return render_template('generic_message.html', message='Thread tidak ditemukan.', current_user=get_current_user())
    
    topik_id = thread.topik

    # hapus thread beserta post-postnya
    run('''
    	delete from reaksi_post where post in (select id from post where thread=:id);
    	delete from post where thread=:id;
        delete from thread where id=:id;
    ''',
        id=thread_id
    )
    
    return redirect(url_for('site.show_topic', topic_id=topik_id))


# ------------------------ Form penambahan dalam thread ------------------------ #
# Memungkinkan user untuk menambahkan thread, sekaligus postingan pertama
# dalam thread.
#
# Implementasi: Create
#
@site.route('/thread/add', methods=['GET'])
def add_thread():
    if get_logged_in_user() is None:
        return render_template('generic_message.html', message='Anda tidak dapat membuat thread baru.')
    
    topik_id = request.args.get('topik')
    
    if topik_id:
        topik = run('''
            select * from topik
            where id=:id;
        ''', id=topik_id).fetchone()
        
        if topik is None:
            return render_template('generic_message.html', message='Topik tidak ditemukan.')
        
        return render_template('add_thread.html', current_user=get_current_user(), topik=topik)
    
    return render_template('generic_message.html', message='Harus menyertakan nomor topik.')

@site.route('/thread/add', methods=['POST'])
def add_thread_submit():
    if get_logged_in_user() is None:
        return render_template('generic_message.html', message='Anda tidak dapat membuat thread baru.')
    
    topik_id = request.args.get('topik')
    
    if topik_id:
        topik = run('''
            select * from topik
            where id=:id;
        ''', id=topik_id).fetchone()
        
        if topik is None:
            return render_template('generic_message.html', message='Topik tidak ditemukan.')
        
        judul = request.form.get('judul')
        isi = request.form.get('isi')
        
        if not judul:
            return render_template('add_thread.html', current_user=get_current_user(), topik=topik, message="Judul tidak boleh kosong.")
        if not isi:
            return render_template('add_thread.html', current_user=get_current_user(), topik=topik, message="Isi tidak boleh kosong.")
        
        # masukkan thread baru
        new_thread = run('''
            insert into thread(judul, topik, pembuat)
            values (:judul, :topik, :pembuat)
            returning *;
        ''',
            judul=judul,
            topik=topik.id,
            pembuat=get_logged_in_user()
        ).fetchone()
        
        run('''
            insert into post(judul, isi, thread, pembuat)
            values (:judul, :isi, :thread, :pembuat);
        ''',
            judul=judul,
            isi=isi,
            thread=new_thread.id,
            pembuat=get_logged_in_user()
        )
        
        return redirect(url_for('site.show_thread', thread_id=new_thread.id))
    
    return render_template('generic_message.html', message='Harus menyertakan nomor topik.')

# ------------------------ User page ------------------------ #
#
# Implamentasi: Read
#
@site.route('/user/<user_id>', methods=['GET'])
def show_user(user_id):
     user = run('''
        select * from forum_user
        where id=:id
        ''', id=user_id
        ).fetchone()
    
     if user is None:
        return render_template('generic_message.html', message='User tidak ditemukan.', current_user=get_current_user())
    
     return render_template('userpage.html', user=user)

# ------------------------ Update post ------------------------ #
#
# Implementasi: Update
#

@site.route('/post/<post_id>/edit', methods=['GET'])
def edit_post(post_id):
    if not get_logged_in_user:
        return render_template('generic_message.html', message='Tidak dapat mengedit post.',  current_user=get_current_user())
    
    post_exists = run('''
            select * from post
            where id=:id;
        ''',
        id=post_id).fetchone()
    
    if not post_exists:
        return render_template('generic_message.html', message='Post tidak ditemukan.',  current_user=get_current_user())
    
    if post_exists.pembuat != get_logged_in_user():
        return render_template('generic_message.html', message='Tidak dapat mengedit post.',  current_user=get_current_user())
    
    return render_template('edit_post.html', post=post_exists,  current_user=get_current_user() )


@site.route('/post/<post_id>/edit', methods=['POST'])
def edit_post_done(post_id):
    if not get_logged_in_user:
        return render_template('generic_message.html', message='Tidak dapat mengedit post.',  current_user=get_current_user())
    
    post_exists = run('''
            select * from post
            where id=:id;
        ''',
        id=post_id).fetchone()
    
    if not post_exists:
        return render_template('generic_message.html', message='Post tidak ditemukan.',  current_user=get_current_user())
    
    if post_exists.pembuat != get_logged_in_user():
        return render_template('generic_message.html', message='Tidak dapat mengedit post.',  current_user=get_current_user())
    
    
    judul = request.form.get('judul')
    isi = request.form.get('isi')
    
    run('''
        update post set judul=:judul, isi=:isi where id=:id;
    ''',
    id=post_id,
    judul=judul,
    isi=isi
    )
    return redirect(url_for('site.show_thread', thread_id=post_exists.thread))
   	
   	
    	
    

# ------------------------ Reaksi menggunakan AJAX ------------------------ #
# Untuk reaksi, tidak digunakan output HTML seperti yang lain
# sebab menggunakan AJAX pada halaman thread.
#
# Implementasi: Create, Read, Delete
#
@site.route('/post/<post_id>/reaksi', methods=['POST'])
def add_reaction(post_id):
    if not get_logged_in_user:
        return f'Anda tidak dapat menambahkan reaksi'
    
    reaksi = request.form.get('reaksi')
    if not reaksi:
        return f'Tidak ada reaksi'
    
    # cek tipe data
    if reaksi not in ['Terkejut', 'Senang', 'Marah', 'Bangga']:
        return f'Reaksi tidak valid'
    
    reaksi_exists = run('''
            select * from reaksi_post
            where dari=:id and reaksi=:reaksi and post=:post;
        ''',
        id=get_logged_in_user(),
        reaksi=reaksi,
        post=post_id).fetchone()
    
    # toggle reaksi
    if reaksi_exists:
        run('''
            delete from reaksi_post
            where dari=:id and reaksi=:reaksi and post=:post;
        ''',
        id=get_logged_in_user(),
        reaksi=reaksi,
        post=post_id)
    else:
        run('''
            insert into reaksi_post(dari, reaksi, post)
            values (:id, :reaksi, :post);
        ''',
        id=get_logged_in_user(),
        reaksi=reaksi,
        post=post_id)
    
    return f'Reaksi berhasil ditambahkan'

@site.route('/post/<post_id>/reaksi', methods=['GET'])
def list_reaction(post_id):
    reaksi_reaksi = run('''
            select * from reaksi_post
            where post=:id;
        ''', id=post_id)
    
    reaksi = []
    for r in reaksi_reaksi:
        reaksi.append({"reaksi": r.reaksi, "dari": r.dari})
    
    return jsonify(reaksi)
    

#-------------------------------------------------------------------------------------------------------#

# ------------------------ Register user ------------------------ #
# Memungkinkan sebuah user untuk mendaftarkan diri sebagai pengguna
# menggunakan alamat e-mail
#
# Implementasi: Create
#
@site.route('/register', methods=['GET'])
def register():
    return render_template('register.html')

@site.route('/register', methods=['POST'])
def register_post():
    email = request.form.get('email')
    pw = request.form.get('password')
    nama = request.form.get('nama')
    institusi = request.form.get('institusi')
    
    # cek apabila terdapat user yg sudah ada dengan e-mail
    # memakai sanitasi yg terdapat pada library dengan
    # menggunakan :email, lebih aman dibandingkan langsung menggabungkan
    user_exists = run('select * from forum_user where email=:email',
    email=email)
    if user_exists.fetchone() is None:
        # insert user
        run('''
            insert into forum_user(email, password, nama, institusi) 
            values (:email, :password, :nama, :institusi);
            ''',
            email=email,
            password=generate_password_hash(pw, 'sha256'),
            nama=nama,
            institusi=institusi
        )
        
        # kemudian redirect ke login
        return redirect(url_for('site.login'))
    else:
        return render_template('register.html', message='Telah ada user dengan e-mail ini! Silahkan coba e-mail lain.')

# ------------------------ Login user ------------------------ #
# Memungkinkan sebuah user untuk login sebagai pengguna
# menggunakan alamat e-mail dan password
#
# Implementasi: Read
#
@site.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@site.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    pw = request.form.get('password')
    
    # cek apabila terdapat user yg sudah ada dengan e-mail
    user_exists = run('''
        select * from forum_user
        where email=:email
        ''',
        email=email
    )
    user = user_exists.fetchone()
    if user is None:
        return render_template('login.html', message='Tidak ada user dengan e-mail ini.')
    else:
        if check_password_hash(user.password, pw):
            login_user(user)
            return redirect(url_for('site.main'))
        else:
            return render_template('login.html', message='Password salah.')

# ------------------------ Logout user ------------------------ #
# Memungkinkan sebuah user untuk keluar secara manual
#
# Implementasi: Read
#
@site.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('site.main'))
