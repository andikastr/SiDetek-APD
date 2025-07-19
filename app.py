import PIL
import streamlit as st
from PIL import Image
import settings 
import helper   
import database   
from zoneinfo import ZoneInfo
from pathlib import Path
import time     
import av       
import re
import threading
import queue
from datetime import datetime
import streamlit_webrtc

# Import komponen dari streamlit-webrtc
from streamlit_webrtc import (
    VideoTransformerBase,
    webrtc_streamer,
    WebRtcMode,
)

# Impor library yang diperlukan untuk komunikasi antar-thread


# --- Konfigurasi Halaman dan Pemuatan Model ---
st.set_page_config(
    page_title="Deteksi APD Konstruksi",
    page_icon="👷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi database
try:
    database.init_db()
except Exception as e:
    st.sidebar.warning(f"Tidak dapat menginisialisasi DB (mungkin sudah ada).")


@st.cache_resource
def load_model_cached():
    model = helper.load_yolo_model()
    if model is None:
        st.error("Model YOLOv11 gagal dimuat. Periksa path model dan instalasi library yang dibutuhkan (misal: ultralytics).")
    return model

MODEL = load_model_cached()


# --- Controller untuk Menyimpan Frame dari Webcam ---
class FrameSaveController:
    def __init__(self):
        self._lock = threading.Lock()
        self._request_save = False
        self.result_queue = queue.Queue()

    def request_save(self):
        with self._lock:
            self._request_save = True

    def check_and_reset_request(self):
        with self._lock:
            if self._request_save:
                self._request_save = False
                return True
            return False

# Inisialisasi controller di session state agar persisten antar-rerun
if 'frame_save_controller' not in st.session_state:
    st.session_state.frame_save_controller = FrameSaveController()


# --- CSS Kustom ---
st.markdown("""
<style>
    

    /* Kontainer utama aplikasi */
    .main .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 2rem;
    }

    /* Latar belakang gradien untuk seluruh halaman */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(45deg, #e0eafc 0%, #cfdef3 100%);
        background-attachment: fixed;
    }

    /* Styling untuk kartu (cards) */
    .custom-card {
        border-radius: 12px;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #cccccc;
        color: #333333;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .custom-card h3 {
        color: #0056b3;
        margin-top: 0;
        border-bottom: 2px solid #0056b3;
        padding-bottom: 0.5rem;
    }
     .custom-card h5, .custom-card h6 {
        color: #004085;
        margin-top: 0.5rem;
        margin-bottom: 0.3rem;
    }

    /* Tombol Aksi Utama */
    div[data-testid="stButton"] > button {
        background-color: #007bff;
        color: white;
        border-radius: 25px;
        padding: 0.6rem 1.8rem;
        border: none;
        font-weight: bold;
        transition: background-color 0.3s ease, transform 0.2s ease;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #0056b3;
        transform: translateY(-2px);
    }
    /* Tombol Simpan Frame (sedikit berbeda untuk membedakan) */
    div[data-testid="stButton"] > button:has(span:contains("Simpan Frame")) {
        background-color: #28a745; /* Warna hijau */
    }
    div[data-testid="stButton"] > button:has(span:contains("Simpan Frame")):hover {
        background-color: #218838;
    }
    /* Tombol Hapus di Riwayat */
    div[data-testid="stButton"] > button:has(span[aria-label="wastebasket"]) { /* Target tombol hapus dengan ikon sampah */
        background-color: #dc3545 !important;
    }
    div[data-testid="stButton"] > button:has(span[aria-label="wastebasket"]):hover {
        background-color: #c82333 !important;
    }
    /* Tombol konfirmasi hapus (merah) */
    div[data-testid="stButton"] > button[kind="primary"] {
         background-color: #dc3545 !important;
         border-color: #dc3545 !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
         background-color: #c82333 !important;
         border-color: #c82333 !important;
    }
     /* Tombol batalkan hapus (default/secondary) */
    div[data-testid="stButton"] > button[kind="secondary"] {
         background-color: #6c757d !important;
         color: white !important;
         border-color: #6c757d !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
         background-color: #5a6268 !important;
         border-color: #545b62 !important;
    }


    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: rgba(245, 245, 245, 0.95);
        backdrop-filter: blur(5px);
        border-right: 1px solid #dddddd;
    }
    .sidebar-header-custom {
        background-color: #007bff;
        padding: 20px;
        border-radius: 10px;
        margin: 15px;
        text-align: center;
    }
    .sidebar-header-custom h2 {
         color: white;
         margin:0;
    }

    /* Styling untuk kontainer video webcam */
    .webrtc-video-container {
        border: 3px solid #007bff;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        margin-bottom: 1rem;
        background-color: #000;
    }
    .webrtc-video-container video {
        width: 100% !important;
        height: auto !important;
        border-radius: 7px;
    }

    /* History image styling */
    .history-image {
        width: 100%;
        max-width: 400px;
        height: auto;
        border-radius: 8px;
        margin-bottom: 0.75rem;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)


# --- Navigasi Sidebar ---
st.sidebar.markdown('<div class="sidebar-header-custom"><h2>👷 SiDetek APD</h2></div>', unsafe_allow_html=True)

page = st.sidebar.selectbox(
    "Pilih Halaman Navigasi:",
    ["🏠 Beranda", "🔎 Deteksi APD", "📜 Riwayat Deteksi"],
    key='page_selector'
)
st.sidebar.info(f"streamlit-webrtc version: {streamlit_webrtc.__version__}")



# --- Kelas VideoTransformer ---
class APDVideoTransformer(VideoTransformerBase):

    # Modifikasi __init__ untuk menerima controller
    def __init__(self, controller, confidence_threshold=0.35):
        self.confidence_threshold = confidence_threshold
        self.model = MODEL
        self.controller = controller # Simpan instance controller

    def update_confidence(self, new_confidence):
        self.confidence_threshold = new_confidence

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        image_np_bgr = frame.to_ndarray(format="bgr24")

        if self.model is None:
            return frame

        try:
            image_np_rgb = image_np_bgr[:, :, ::-1] # Konversi BGR ke RGB
            image_pil = Image.fromarray(image_np_rgb)

            result_image_pil, detections = helper.perform_detection(
                image_pil,
                self.confidence_threshold
            )

            # Periksa apakah ada permintaan untuk menyimpan frame
            if self.controller.check_and_reset_request():
                frame_name = f"Webcam Capture {datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%Y-%m-%d %H_%M_%S')}.png"

                # Panggil fungsi helper untuk menyimpan ke DB
                saved_record = helper.save_detection_to_db(
                    original_image_name=frame_name,
                    original_image_pil=image_pil,       
                    detected_image_pil=result_image_pil,
                    detections_data_list=detections
                )
                self.controller.result_queue.put(saved_record)

            return av.VideoFrame.from_image(result_image_pil)

        except Exception as e:
            print(f"Error processing webcam frame in APDVideoTransformer.recv: {e}")
            return frame


# --- Konten Halaman ---

if page == "🏠 Beranda":
    st.markdown("<h1 style='text-align: center; color: #007bff;'>Selamat Datang di Aplikasi Deteksi APD</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #333; font-size: 1.2rem; max-width: 800px; margin: auto;'>Aplikasi ini memanfaatkan model YOLOv11 untuk mengidentifikasi penggunaan Alat Pelindung Diri (APD) pada pekerja konstruksi secara otomatis dari gambar atau stream video langsung menggunakan webcam.</p>", unsafe_allow_html=True)
    st.markdown("---", unsafe_allow_html=True)
    
    st.sidebar.info(
        "Aplikasi ini dikembangkan untuk mendeteksi Alat Pelindung Diri (APD) "
        "pada pekerja konstruksi menggunakan model YOLOv11. "
        "Pilih halaman dari menu di atas."
    )

    col_intro1, col_intro2 = st.columns(2)
    with col_intro1:
        st.markdown("<div class='custom-card'><h3>🚀 Fitur Unggulan</h3><ul><li>Deteksi APD via unggah gambar (JPG, PNG, JPEG).</li><li>Analisis APD secara realtime menggunakan kamera webcam.</li><li>Identifikasi APD vital seperti Safety Helmet dan Reflective Jacket.</li><li>Penyimpanan riwayat deteksi (untuk unggah gambar) guna keperluan audit dan analisis tren kepatuhan.</li><li>Antarmuka pengguna yang modern, intuitif, dan mudah dinavigasi.</li></ul></div>", unsafe_allow_html=True)
    with col_intro2:
        st.markdown("<div class='custom-card'><h3>📖 Panduan Singkat</h3><ol><li><b>Pilih Halaman:</b> Gunakan menu navigasi di sidebar kiri untuk berpindah antar halaman.</li><li><b>Deteksi APD:</b> Buka halaman 'Deteksi APD'.</li><li><b>Pilih Sumber:</b> Tentukan apakah Anda ingin 'Unggah Gambar' atau 'Deteksi Realtime via Webcam'.</li><li><b>Proses:</b> Ikuti instruksi pada halaman tersebut untuk memulai deteksi.</li><li><b>Hasil:</b> Amati hasil deteksi yang ditampilkan, lengkap dengan visualisasi dan ringkasan.</li><li><b>Riwayat:</b> Kunjungi halaman 'Riwayat Deteksi' untuk meninjau deteksi dari unggahan gambar sebelumnya.</li></ol></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<h3 style='text-align:center; color: #007bff;'>Contoh Deteksi APD</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        default_image_path = str(settings.DEFAULT_IMAGE)
        default_image = PIL.Image.open(default_image_path)
        st.image(default_image_path, caption="Uploaded Image", use_container_width=True)
    
    with col2:
        default_detected_image_path = str(settings.DEFAULT_DETECT_IMAGE)
        default_detected_image = PIL.Image.open(default_detected_image_path)
        st.image(default_detected_image_path, caption='Detected Image', use_container_width=True)


elif page == "🔎 Deteksi APD":
    st.header("🔎 Deteksi Penggunaan Alat Pelindung Diri (APD)")
    st.markdown("Pilih sumber input Anda di sidebar: unggah gambar statis atau gunakan kamera webcam untuk analisis realtime.")

    source_type = st.sidebar.radio(
        "Pilih Sumber Input Deteksi:",
        ["🖼️ Unggah Gambar", "📹 Deteksi Realtime via Webcam"],
        key="source_type_selector_radio"
    )
    st.sidebar.markdown("---")
    confidence_thresh_slider = st.sidebar.slider("🎯 Ambang Kepercayaan Deteksi (%)", 0, 100, 40, 5) / 100

    if source_type == "🖼️ Unggah Gambar":
        st.subheader("🖼️ Unggah Gambar Pekerja Konstruksi")
        uploaded_image_file = st.file_uploader(
            "Seret & lepas file gambar di sini, atau klik untuk memilih (Format: JPG, JPEG, PNG)",
            type=["jpg", "jpeg", "png"]
        )

        if uploaded_image_file is not None:
            try:
                original_image_pil = Image.open(uploaded_image_file)
                original_image_name = uploaded_image_file.name

                col_img_upload1, col_img_upload2 = st.columns(2)
                with col_img_upload1:
                    st.markdown("<div class='custom-card'><h5>Gambar Asli yang Diunggah:</h5></div>", unsafe_allow_html=True)
                    st.image(original_image_pil, caption=f"Nama file: {original_image_name}", use_container_width=True)

                if st.button("🚀 Mulai Deteksi APD pada Gambar Ini", key="detect_image_button"):
                    if MODEL is None:
                        st.error("⚠️ Model deteksi tidak berhasil dimuat. Tidak dapat melanjutkan.")
                    else:
                        with st.spinner("🕵️ Sedang menganalisis gambar, mohon tunggu..."):
                            result_image_pil, detections = helper.perform_detection(original_image_pil, confidence_thresh_slider)
                            
                            with col_img_upload2:
                                st.markdown("<div class='custom-card'><h5>Gambar Hasil Deteksi:</h5></div>", unsafe_allow_html=True)
                                st.image(result_image_pil, caption="Gambar dengan anotasi deteksi", use_container_width=True)

                            if detections:
                                st.markdown("---")
                                st.markdown("<div class='custom-card'><h3>📊 Ringkasan Hasil Deteksi dari Gambar</h3></div>", unsafe_allow_html=True)
                                detected_counts = {}
                                for det_idx, det in enumerate(detections):
                                    label = det['label']
                                    normalized_label = str(label).strip().capitalize()
                                    if not normalized_label:
                                        normalized_label = "Tidak_Diketahui"
                                    detected_counts[normalized_label] = detected_counts.get(normalized_label, 0) + 1
                                
                                if detected_counts:
                                    num_metrics = len(detected_counts)
                                    cols_per_row = 3
                                    metric_cols = st.columns(cols_per_row)
                                    
                                    col_idx = 0
                                    for item_idx, (lbl, count) in enumerate(detected_counts.items()):
                                        with metric_cols[col_idx % cols_per_row]:
                                            st.metric(label=lbl, value=count)
                                        col_idx += 1
                                else:
                                    st.info("Tidak ada objek APD yang terdeteksi dengan jelas pada gambar ini.")

                                with st.expander("Lihat Detail Data Deteksi (Format JSON)"):
                                    st.json(detections)
                                
                                saved_record = helper.save_detection_to_db(
                                    original_image_name=original_image_name,
                                    original_image_pil=original_image_pil,
                                    detected_image_pil=result_image_pil,
                                    detections_data_list=detections
                                )
                                if saved_record:
                                    st.success(f"✅ Hasil deteksi berhasil disimpan ke database! (ID Record: {saved_record.id})")
                                else:
                                    st.error("❌ Gagal menyimpan hasil deteksi ke database.")
                            else:
                                st.info("ℹ️ Tidak ada APD yang terdeteksi pada gambar dengan ambang kepercayaan yang dipilih.")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses gambar yang diunggah: {e}")
                print(f"Error di halaman deteksi gambar (upload): {e}")

    elif source_type == "📹 Deteksi Realtime via Webcam":
        st.subheader("📹 Deteksi APD Langsung dari Webcam")
        st.info("Klik tombol 'START' di bawah untuk mengaktifkan kamera. Pastikan Anda memberikan izin akses kamera pada browser.")

        # Ambil controller dari session state
        frame_saver_controller = st.session_state.frame_save_controller

        with st.container():
            st.markdown('<div class="webrtc-video-container">', unsafe_allow_html=True)
            webrtc_ctx = webrtc_streamer(
                key="apd-detection-webcam",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=lambda: APDVideoTransformer(controller=frame_saver_controller, confidence_threshold=confidence_thresh_slider),
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True,
                trickle_ice=False
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Periksa queue untuk setiap hasil penyimpanan yang telah selesai
        try:
            save_result = frame_saver_controller.result_queue.get_nowait()
            if save_result:
                st.toast("✅ Frame berhasil disimpan ke riwayat!")
            else:
                st.error("❌ Gagal menyimpan frame ke database.")
        except queue.Empty:
            pass
        
        if webrtc_ctx.state.playing:
            # Tambahkan tombol simpan frame, hanya muncul saat video berjalan
            if st.button("📸 Simpan Frame Saat Ini"):
                frame_saver_controller.request_save()
                st.toast("✅ Frame berhasil disimpan ke riwayat!")
            
            st.success("Kamera aktif dan deteksi sedang berjalan.")
            st.caption("Untuk menghentikan, klik tombol 'STOP' pada pemutar video.")
        else:
            st.info("Kamera tidak aktif. Klik 'START' pada pemutar video di atas untuk memulai.")


        st.markdown("""
        ---
        **Catatan:**
        - Kualitas dan kecepatan deteksi realtime sangat bergantung pada spesifikasi komputer Anda.
        - Untuk menyimpan frame dari video, klik tombol **'Simpan Frame Saat Ini'** saat video berjalan. Frame yang berhasil disimpan akan dapat dilihat di halaman 'Riwayat Deteksi'.
        """)


elif page == "📜 Riwayat Deteksi":
    st.header("📜 Riwayat Hasil Deteksi APD dari Unggahan Gambar")
    st.markdown("Berikut adalah daftar deteksi yang telah dilakukan dan disimpan (hanya dari unggahan gambar), diurutkan dari yang terbaru.")

    history_records = helper.get_all_detection_results_from_db()

    if not history_records:
        st.info("ℹ️ Belum ada riwayat deteksi yang tersimpan di database.")
    else:
        if st.button("🗑️ Hapus Semua Riwayat", type="secondary", key="delete_all_history_main_button"):
            if 'confirm_delete_all_visible' not in st.session_state:
                st.session_state.confirm_delete_all_visible = False
            st.session_state.confirm_delete_all_visible = True

        if st.session_state.get('confirm_delete_all_visible', False):
            st.warning("⚠️ **PERINGATAN:** Anda akan menghapus SEMUA data riwayat deteksi. Tindakan ini tidak dapat diurungkan.")
            col_confirm1, col_confirm2, col_confirm_spacer = st.columns([1,1,2])
            with col_confirm1:
                if st.button("🔴 Ya, Hapus Semua", key="confirm_delete_all_action_button", type="primary"):
                    deleted_count = 0
                    for record_to_delete in list(history_records):
                        if helper.delete_detection_record_from_db(record_to_delete.id):
                            deleted_count +=1
                    st.success(f"Berhasil menghapus {deleted_count} record riwayat.")
                    st.session_state.confirm_delete_all_visible = False
                    st.rerun()
            with col_confirm2:
                if st.button("🟢 Batalkan", key="cancel_delete_all_action_button", type="secondary"):
                    st.session_state.confirm_delete_all_visible = False
                    st.rerun()
            st.markdown("---")

        st.markdown(f"Total deteksi tersimpan: **{len(history_records)}**")
        st.markdown("---")

        for record_idx, record in enumerate(history_records):
            with st.container():
                st.markdown(f"<div class='custom-card'>", unsafe_allow_html=True)
                st.subheader(f"📌 Deteksi ID: {record.id}")
                st.caption(f"Tanggal Deteksi: {record.timestamp.strftime('%d %B %Y, %H:%M:%S WIB')}")

                if record.original_image_name:
                    st.write(f"**Nama File Asli:** `{record.original_image_name}`")

                col_hist_img1, col_hist_img2 = st.columns(2)
                try:
                    with col_hist_img1:
                        st.markdown("<h6>Gambar Asli:</h6>", unsafe_allow_html=True)
                        original_img_pil = helper.blob_to_pil(record.original_image_blob)
                        st.image(original_img_pil, use_container_width=True, output_format='PNG')
                except Exception as e:
                    with col_hist_img1:
                        st.warning(f"Gagal menampilkan gambar asli: {e}")

                try:
                    with col_hist_img2:
                        st.markdown("<h6>Gambar Hasil Deteksi:</h6>", unsafe_allow_html=True)
                        detected_img_pil = helper.blob_to_pil(record.detected_image_blob)
                        st.image(detected_img_pil, use_container_width=True, output_format='PNG')
                except Exception as e:
                    with col_hist_img2:
                        st.warning(f"Gagal menampilkan gambar hasil deteksi: {e}")

                with st.expander("Lihat Detail Data Deteksi (Format JSON)"):
                    st.json(record.detections_data)

                delete_button_key = f"delete_single_record_button_{record.id}"
                confirm_delete_key = f"confirm_delete_single_visible_{record.id}"

                if st.button("🗑️ Hapus Record Ini", key=delete_button_key):
                    st.session_state[confirm_delete_key] = True

                if st.session_state.get(confirm_delete_key, False):
                    st.warning(f"Anda akan menghapus Record ID: {record.id}. Lanjutkan?")
                    col_confirm_single1, col_confirm_single2, _ = st.columns([1,1,2])
                    with col_confirm_single1:
                        if st.button("🔴 Ya, Hapus", key=f"confirm_delete_action_{record.id}", type="primary"):
                            if helper.delete_detection_record_from_db(record.id):
                                st.success(f"Record ID: {record.id} berhasil dihapus!")
                            else:
                                st.error(f"Gagal menghapus Record ID: {record.id}.")
                            st.session_state[confirm_delete_key] = False
                            st.rerun()
                    with col_confirm_single2:
                        if st.button("🟢 Batalkan", key=f"cancel_delete_action_{record.id}", type="secondary"):
                            st.session_state[confirm_delete_key] = False
                            st.rerun()

                st.markdown(f"</div>", unsafe_allow_html=True)
                st.markdown("---")

# --- Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #777; font-size: 0.9rem;'>© 2024-2025 Aplikasi Deteksi APD | Dikembangkan dengan Streamlit oleh ANDIKA SATRIA PUTRA</p>", unsafe_allow_html=True)