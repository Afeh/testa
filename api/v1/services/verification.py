import cv2 as cv
import dlib
import numpy as np
from PIL import Image
from io import BytesIO
import requests
import face_recognition
import logging
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# IMPORTANT: Download this file and place it in your project's root directory
# or a dedicated 'assets' folder.
SHAPE_PREDICTOR_PATH = 'shape_predictor_68_face_landmarks.dat'


class FaceVerificationSystem:
    def __init__(self,
                 reference_image_url,
                 face_match_threshold=0.6,
                 eye_ar_threshold=0.25,
                 eye_ar_consec_frames=3,
                 required_blinks=1):

        self.reference_image_url = reference_image_url
        self.face_match_threshold = face_match_threshold
        self.eye_ar_threshold = eye_ar_threshold
        self.eye_ar_consec_frames = eye_ar_consec_frames
        self.required_blinks = required_blinks

        # State tracking
        self.blink_counter = 0
        self.total_blinks = 0
        self.verification_passed = False
        self.liveness_passed = False

        self.known_face_encodings = []

        # Load models once
        self.predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
        self.detector = dlib.get_frontal_face_detector()
        
        # This will be called separately now
        # self.initialize_reference_encoding()

    def eye_aspect_ratio(self, eye):
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        C = np.linalg.norm(eye[0] - eye[3])
        return (A + B) / (2.0 * C)

    def fetch_reference_image(self):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(self.reference_image_url, headers=headers)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            return cv.cvtColor(np.array(img), cv.COLOR_RGB2BGR)
        except Exception as e:
            logging.error(f"Error fetching reference image: {e}")
            return None

    def initialize_reference_encoding(self):
        """Loads and encodes the reference image. Returns True on success, False on failure."""
        reference_image_np = self.fetch_reference_image()
        if reference_image_np is None:
            logging.error("Reference image could not be loaded.")
            return False

        reference_image_rgb = cv.cvtColor(reference_image_np, cv.COLOR_BGR2RGB)
        ref_face_locations = face_recognition.face_locations(reference_image_rgb)
        if not ref_face_locations:
            logging.error("No face found in the reference image.")
            return False

        ref_face_encoding = face_recognition.face_encodings(reference_image_rgb, ref_face_locations)[0]
        self.known_face_encodings = [ref_face_encoding]
        return True

    def process_frame(self, frame_b64):
        """Processes a single base64 encoded frame and returns the verification status."""
        try:
            # Decode base64 frame
            img_data = base64.b64decode(frame_b64)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv.imdecode(np_arr, cv.IMREAD_COLOR)
        except Exception as e:
            return {"status": "error", "message": "Invalid frame data."}

        # Main logic from the original run_verification, but for a single frame
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        faces = self.detector(gray)

        if len(faces) == 0:
            return {"status": "fail", "message": "No face detected."}
        if len(faces) > 1:
            return {"status": "fail", "message": "Multiple faces detected."}
        
        # --- Verification Logic ---
        if not self.verification_passed:
            face_locations = face_recognition.face_locations(rgb)
            if not face_locations:
                return {"status": "fail", "message": "Detecting face..."}

            face_encodings = face_recognition.face_encodings(rgb, face_locations)
            face_encoding = face_encodings[0]
            
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=self.face_match_threshold)
            if True not in matches:
                self.reset_state()
                return {"status": "fail", "message": "Verification Failed: User does not match."}
            
            self.verification_passed = True
            
        # --- Liveness Logic (only runs if verification passed) ---
        if not self.liveness_passed:
            shape = self.predictor(gray, faces[0])
            landmarks = np.array([(p.x, p.y) for p in shape.parts()])
            left_eye = landmarks[36:42]
            right_eye = landmarks[42:48]
            ear = (self.eye_aspect_ratio(left_eye) + self.eye_aspect_ratio(right_eye)) / 2.0

            if ear < self.eye_ar_threshold:
                self.blink_counter += 1
            else:
                if self.blink_counter >= self.eye_ar_consec_frames:
                    self.total_blinks += 1
                self.blink_counter = 0

            if self.total_blinks >= self.required_blinks:
                self.liveness_passed = True
                
            return {"status": "in_progress", "message": f"Blink {self.total_blinks}/{self.required_blinks} times.", "blinks": self.total_blinks}

        # --- Success Condition ---
        if self.verification_passed and self.liveness_passed:
            return {"status": "success", "message": "Verification and Liveness Passed!"}
            
        return {"status": "fail", "message": "Unknown state."}
        
    def reset_state(self):
        """Resets the state if verification fails or user moves away."""
        self.blink_counter = 0
        self.total_blinks = 0
        self.verification_passed = False
        self.liveness_passed = False