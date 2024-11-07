import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import io
from PIL import Image
import time
import base64

class SafeCamera:
    def __init__(self):
        self.cap = None
        self.initialized = False
        self.resolutions = [
            (640, 480),    # VGA
            (1280, 720),   # HD
            (1920, 1080),  # Full HD
            (2592, 1944)   # 5MP
        ]
        self.current_resolution_index = 0
    
    def initialize(self, index):
        try:
            if self.cap is not None:
                self.release()
            
            self.cap = cv2.VideoCapture(index)
            if not self.cap.isOpened():
                return False
            
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            
            resolution = self.resolutions[self.current_resolution_index]
            self.set_resolution(resolution[0], resolution[1])
            
            self.initialized = True
            return True
            
        except Exception as e:
            st.error(f"Erro na inicialização da câmera: {str(e)}")
            self.release()
            return False
    
    def set_resolution(self, width, height):
        if not self.initialized:
            return None, None
            
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            return actual_width, actual_height
            
        except Exception as e:
            st.error(f"Erro ao definir resolução: {str(e)}")
            return None, None
    
    def read(self):
        if not self.initialized or self.cap is None:
            return False, None
        return self.cap.read()
    
    def release(self):
        try:
            if self.cap is not None:
                self.cap.release()
            self.cap = None
            self.initialized = False
        except Exception as e:
            st.error(f"Erro ao liberar câmera: {str(e)}")

def detect_cameras():
    """Detecta câmeras disponíveis no sistema."""
    available_cameras = []
    for i in [-1] + list(range(11)):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                name = f"Camera {i}"
                if i == -1:
                    name = "Tricoscópio USB (índice -1)"
                available_cameras.append((i, name))
            cap.release()
        except Exception:
            continue
    
    if not available_cameras:
        available_cameras.append((-1, "Tricoscópio USB (índice -1)"))  # Fallback option
    
    return available_cameras

def get_image_download_link(img, filename, text):
    """Gera um link para download da imagem."""
    buffered = io.BytesIO()
    img_pil = Image.fromarray(img)
    img_pil.save(buffered, format="JPEG", quality=100)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:image/jpeg;base64,{img_str}" download="{filename}">{text}</a>'
    return href

def main():
    st.set_page_config(page_title="Tricoscópio Digital", layout="wide")
    
    st.title("Visualizador de Tricoscópio Digital")
    
    # Initialize session state
    if 'camera' not in st.session_state:
        st.session_state.camera = SafeCamera()
        st.session_state.camera_active = False
        st.session_state.available_cameras = detect_cameras()
        st.session_state.last_capture = None
        st.session_state.selected_camera_index = None
    
    with st.sidebar:
        st.header("Controles")

        # Create camera options dictionary with proper error handling
        available_cameras = st.session_state.available_cameras
        camera_options = [(idx, name) for idx, name in available_cameras]
        
        if not camera_options:
            st.error("Nenhuma câmera detectada")
            return
        
        # Camera selection
        camera_names = [name for _, name in camera_options]
        selected_camera_name = st.selectbox(
            "Selecione o dispositivo",
            camera_names,
            index=0
        )
        
        # Find the corresponding camera index
        selected_camera_index = next(
            (idx for idx, name in camera_options if name == selected_camera_name),
            camera_options[0][0]  # Fallback to first camera if not found
        )
        st.session_state.selected_camera_index = selected_camera_index
        
        # Resolution selection
        resolutions = {
            "640x480 (VGA)": (640, 480),
            "1280x720 (HD)": (1280, 720),
            "1920x1080 (Full HD)": (1920, 1080),
            "2592x1944 (5MP)": (2592, 1944)
        }
        selected_resolution = st.selectbox(
            "Selecione a resolução",
            list(resolutions.keys())
        )
        
        # Camera control buttons
        if not st.session_state.camera_active:
            if st.button("Iniciar Câmera"):
                if st.session_state.camera.initialize(selected_camera_index):
                    width, height = resolutions[selected_resolution]
                    st.session_state.camera.set_resolution(width, height)
                    st.session_state.camera_active = True
                    st.success(f"Câmera iniciada com índice {selected_camera_index}")
                else:
                    st.error(f"Não foi possível inicializar a câmera com índice {selected_camera_index}")
        else:
            if st.button("Parar Câmera"):
                st.session_state.camera.release()
                st.session_state.camera_active = False
        
        # Capture button
        if st.session_state.camera_active:
            if st.button("Capturar Imagem"):
                ret, frame = st.session_state.camera.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st.session_state.last_capture = frame_rgb
                    st.success("Imagem capturada! Verifique a seção de download.")
                else:
                    st.error("Erro ao capturar imagem")
    
    # Main display area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Visualização em Tempo Real")
        video_placeholder = st.empty()
        
        while st.session_state.camera_active:
            ret, frame = st.session_state.camera.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)
            time.sleep(0.033)
    
    with col2:
        st.header("Última Captura")
        if st.session_state.last_capture is not None:
            st.image(st.session_state.last_capture, caption="Imagem Capturada", use_column_width=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tricoscopia_{timestamp}.jpg"
            
            st.markdown(
                get_image_download_link(
                    st.session_state.last_capture,
                    filename,
                    "📥 Clique aqui para baixar a imagem"
                ),
                unsafe_allow_html=True
            )
            
            if st.button("Limpar última captura"):
                st.session_state.last_capture = None
                st.rerun()

if __name__ == "__main__":
    main()