# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
# from sqlalchemy.orm import Session
# from api.db.database import get_db
# from api.v1.services.user import user_service
# from api.v1.services.verification import FaceVerificationSystem
# from fastapi.security import HTTPAuthorizationCredentials
# # from api.v1.services.user import bearer_scheme # Import the scheme

# router = APIRouter(prefix="/verification", tags=["Verification"])

# @router.websocket("/ws/face-verify")
# async def websocket_face_verification(
#     websocket: WebSocket,
#     db: Session = Depends(get_db)
# ):
#     await websocket.accept()
    
#     # 1. Authenticate the user from the first message
#     try:
#         token_data = await websocket.receive_json()
#         token = token_data.get('token')
#         if not token:
#             await websocket.close(code=1008, reason="Token not provided")
#             return
            
#         # Manually get user from token
#         credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
#         user = user_service.get_current_user(token=credentials, db=db)
        
#         if not user or not user.avatar_url:
#             await websocket.close(code=1008, reason="User or avatar not found.")
#             return
            
#         await websocket.send_json({"status": "authenticated", "message": "Authentication successful. Initializing verifier..."})

#     except Exception as e:
#         await websocket.close(code=1008, reason=f"Authentication failed: {e}")
#         return
        
#     # 2. Initialize the verification system
#     verifier = FaceVerificationSystem(reference_image_url=user.avatar_url)
#     if not verifier.initialize_reference_encoding():
#         await websocket.close(code=1011, reason="Could not initialize from reference image.")
#         return
    
#     await websocket.send_json({"status": "ready", "message": "Verifier ready. Send video frames."})

#     # 3. Loop to process frames from the client
#     try:
#         while True:
#             # Receive base64 encoded frame from client
#             frame_b64 = await websocket.receive_text()
            
#             # Process the frame
#             result = verifier.process_frame(frame_b64)
            
#             # Send status back to client
#             await websocket.send_json(result)
            
#             # If successful, close the connection
#             if result.get("status") == "success":
#                 # Here you could set a flag in the DB or a short-lived cache (e.g., Redis)
#                 # to confirm that this user has passed verification for a specific exam.
#                 # For example: cache.set(f"user_verified_{user.id}", "true", ex=300)
#                 await websocket.close(code=1000, reason="Verification successful.")
#                 break

#     except WebSocketDisconnect:
#         print(f"Client {user.email} disconnected.")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         await websocket.close(code=1011, reason="An unexpected error occurred.")