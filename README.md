# 🚀 SiDetek-APD: Sistem Deteksi Alat Pelindung Diri (APD)


Sebuah sistem cerdas yang mampu mendeteksi penggunaan Alat Pelindung Diri (APD) seperti **helm dan rompi reflektif** secara *real-time* menggunakan kamera. Proyek ini dibangun untuk meningkatkan keselamatan di lingkungan kerja.


---

## 📜 Tentang Proyek

**SiDetek-APD** adalah sebuah aplikasi berbasis *Object Detection* yang dikembangkan untuk memonitor dan memastikan para pekerja menggunakan APD yang sesuai standar. Aplikasi ini menggunakan model *object detection* **YOLOv11** yang telah dilatih secara khusus untuk mengenali dua jenis APD utama: helm dan rompi reflektif.

Tujuan utama dari proyek ini adalah untuk mengurangi risiko kecelakaan kerja dengan memberikan peringatan dini jika ada pekerja yang terdeteksi tidak menggunakan APD lengkap.

---

## ✨ Fitur Utama

* **Deteksi Real-Time:** Menganalisis *feed* video dari kamera secara langsung.
* **Deteksi Multi-Objek:** Mampu mengenali helm dan rompi reflektif secara bersamaan dalam satu *frame*.
* **Antarmuka Sederhana:** GUI yang mudah digunakan dibangun dengan Tkinter untuk menampilkan hasil deteksi.
* **Model Kustom:** Menggunakan bobot model YOLOv11 (`yolov11m`) yang telah dilatih khusus untuk dataset APD.

---

## 💻 Teknologi yang Digunakan

* **Python:** Bahasa pemrograman utama.
* **Pillow (`PIL`):** Untuk membaca dan memanipulasi gambar.
* **WebRTC (`streamlit_webtrc`):** Untuk pemrosesan webcam.
* **YOLOv11:** Algoritma deteksi objek yang cepat dan akurat.
* **SQLAlchemy:** *Library* Python untuk koneksi dan pengelolaan database.
* **Streamlit:** Untuk membangun antarmuka web interaktif secara mudah.

---

## ⚙️ Instalasi & Persiapan

Ikuti langkah-langkah di bawah ini untuk menjalankan proyek ini di komputer Anda.

1.  **Clone repository ini**
    ```sh
    git clone https://github.com/andikastr/SiDetek-APD.git
    ```
2.  **Masuk ke direktori proyek**
    ```sh
    cd SiDetek-APD
    ```
3.  **Install semua dependency yang dibutuhkan**
    Disarankan untuk membuat *virtual environment* terlebih dahulu.
    ```sh
    pip install -r requirements.txt
    ```


---

## 🚀 Cara Penggunaan

Untuk menjalankan aplikasi deteksi APD secara lokal, cukup eksekusi file `app.py` dengan perintah berikut pada terminal proyek.

```sh
streamlit app.py
```

Jika ingin menggunakan aplikasi deteksi APD pada browser secara online, dapat mengakses tautan  [`https://sidetek-apd.streamlit.app`](https://sidetek-apd.streamlit.app)
