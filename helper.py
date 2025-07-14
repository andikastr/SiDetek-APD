from PIL import Image
import io
import base64
from ultralytics import YOLO # Asumsi menggunakan ultralytics untuk YOLOv11
import settings
from database import SessionLocal, DetectionHistory
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Fungsi Model YOLO ---
MODEL_YOLO = None

def load_yolo_model(model_path=settings.DETECTION_MODEL_PATH):
    """Memuat model YOLO. Dipanggil dari app.py agar model tidak selalu reload."""
    global MODEL_YOLO
    if MODEL_YOLO is None:
        try:
            MODEL_YOLO = YOLO(model_path)
            print("Model YOLOv11 berhasil dimuat.")
        except Exception as e:
            print(f"Error memuat model YOLOv11: {e}")
            MODEL_YOLO = None
    return MODEL_YOLO

def perform_detection(image_pil, confidence_threshold=0.35):
    if MODEL_YOLO is None:
        raise Exception("Model YOLOv11 belum dimuat.")

    results = MODEL_YOLO(image_pil, conf=confidence_threshold)

    # Dapatkan gambar hasil dengan bounding box dari ultralytics
    annotated_frame_bgr = results[0].plot() # Menghasilkan numpy array BGR
    annotated_frame_rgb = annotated_frame_bgr[..., ::-1] # Konversi BGR ke RGB
    result_image_pil = Image.fromarray(annotated_frame_rgb)

    # Ekstrak data deteksi
    detections_data = []
    names = MODEL_YOLO.names 
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            label = names.get(class_id, f'Class_{class_id}')
            confidence = float(box.conf[0])
            # Koordinat bbox dalam format [x1, y1, x2, y2]
            bbox = [int(coord) for coord in box.xyxy[0].tolist()]
            
            detections_data.append({
                'label': label,
                'confidence': round(confidence, 3),
                'bbox': bbox
            })
            
    return result_image_pil, detections_data

# --- Fungsi Konversi Gambar & BLOB ---
def pil_to_blob(image_pil):
    """Mengkonversi objek PIL Image ke data byte (BLOB)."""
    byte_io = io.BytesIO()
    image_pil.save(byte_io, format=image_pil.format if image_pil.format else 'PNG')
    return byte_io.getvalue()

def blob_to_pil(image_blob):
    """Mengkonversi data byte (BLOB) kembali ke objek PIL Image."""
    return Image.open(io.BytesIO(image_blob))

def blob_to_base64(image_blob):
    """Mengkonversi data byte (BLOB) ke string base64 untuk ditampilkan di HTML."""
    return base64.b64encode(image_blob).decode('utf-8')

# --- Fungsi Database ---
def save_detection_to_db(original_image_name, original_image_pil, detected_image_pil, detections_data_list):
    """Menyimpan hasil deteksi ke database."""
    db = SessionLocal()
    try:
        original_blob = pil_to_blob(original_image_pil)
        detected_blob = pil_to_blob(detected_image_pil)

        new_record = DetectionHistory(
            original_image_name=original_image_name,
            original_image_blob=original_blob,
            detected_image_blob=detected_blob,
            detections_data=detections_data_list,
            timestamp=datetime.now(ZoneInfo("Asia/Jakarta"))
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record
    except Exception as e:
        db.rollback()
        print(f"Error menyimpan ke database: {e}")
        return None
    finally:
        db.close()

def get_all_detection_results_from_db():
    """Mengambil semua riwayat deteksi dari database, diurutkan terbaru dulu."""
    db = SessionLocal()
    try:
        return db.query(DetectionHistory).order_by(DetectionHistory.timestamp.desc()).all()
    finally:
        db.close()

def delete_detection_record_from_db(record_id):
    """Menghapus record deteksi berdasarkan ID."""
    db = SessionLocal()
    try:
        record = db.query(DetectionHistory).get(record_id)
        if record:
            db.delete(record)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error menghapus record: {e}")
        return False
    finally:
        db.close()