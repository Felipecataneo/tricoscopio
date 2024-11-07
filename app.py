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
    # Testa índices de 0 a 2, reduzir o teste aos índices mais prováveis
    for i in range(0, 3):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                name = f"Camera {i}"
                available_cameras.append((i, name))
            cap.release()
        except Exception:
            continue
    
    if not available_cameras:
        available_cameras.append((-1, "Nenhuma câmera detectada"))  # Fallback option
    
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
    
    # Inicialização da sessão state
    if 'camera' not in st.session_state:
        st.session_state.camera = SafeCamera()
        st.session_state.camera_active = False
        st.session_state.available_cameras = detect_cameras()
        st.session_state.last_capture = None
        st.session_state.current_camera_index = 0
    
    with st.sidebar:
        st.header("Controles")

        # Seleção de dispositivo
        available_cameras = st.session_state.available_cameras
        
        camera_names = [name for _, name in available_cameras]

        # Garantir que a lista não está vazia
        if not camera_names:
            camera_names = ["Nenhuma câmera detectada"]

        # Validate current_camera_index
        if st.session_state.current_camera_index >= len(camera_names):
            st.session_state.current_camera_index = 0  # Ajusta para o primeiro índice válido

        selected_camera_name = st.selectbox(
            "Selecione o dispositivo",
            camera_names,
            index=st.session_state.current_camera_index
        )
        
        # Mapeia a seleção do selectbox para o índice de câmera
        selected_camera_index = -1  # Fallback
        for idx, name in available_cameras:
            if name == selected_camera_name:
                selected_camera_index = idx
                break

        st.session_state.current_camera_index = camera_names.index(selected_camera_name)
        
        # Seleção de resolução
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
        
        # Botão para iniciar/parar câmera
        if not st.session_state.camera_active:
            if st.button("Iniciar Câmera") and selected_camera_index != -1:
                # Tenta inicializar a câmera selecionada
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
        
        # Botão para capturar imagem
        if st.session_state.camera_active:
            if st.button("Capturar Imagem"):
                ret, frame = st.session_state.camera.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st.session_state.last_capture = frame_rgb
                    st.success("Imagem capturada! Verifique a seção de download.")
                else:
                    st.error("Erro ao capturar imagem")
    
    # Área principal para exibição da imagem
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