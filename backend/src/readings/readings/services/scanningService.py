# import time
# from fastapi import Request, UploadFile
# from globals.utils.requestValidation import validate_request
# from globals.utils.logger import logger
# from globals.responses.responses import success_response
# from globals.exceptions.global_exceptions import ValidationError, InternalServerError
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import Optional
# from globals.utils.fileValidator import FileValidator, FileValidationConfigs
# import os
# from src.readings.queries.readingsQueries import ReadingsQueries
# import re 
# import asyncio  
# from ultralytics import YOLO
# import cv2
# import numpy as np
# from paddleocr import TextRecognition
# from io import BytesIO

# from uuid import UUID

# from src.meters.exceptions.exceptions import (
#     MeterNotFoundError,
#     MeterInactiveError
# )
# from src.readings.exceptions.exceptions import (
#     DuplicateReadingDateException,
#     ReadingFrequencyException,
#     InvalidReadingValueException,
#     FixedMeterCannotHaveUsageReadingsError,
    
# )



# class ScanningService:
#     def __init__(self, readings_queries: ReadingsQueries):
#         self.readings_queries = readings_queries
#         # Base models directory (absolute path)
#         base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))

#         # models path
#         yolo_model_path = os.path.join(base_dir, "yolo", "best.onnx")
#         ocr_model_dir = os.path.join(base_dir, "ocr", "PP-OCRv5_mobile_rec_infer")

#         # Initialize YOLO
#         self.yolo_model = YOLO(yolo_model_path, task="detect")

#         # Initialize OCR
#         self.ocr_model = TextRecognition(
#             model_name="PP-OCRv5_mobile_rec",
#             # model_name="PP-OCRv5_server_rec",
#             # model_name="en_PP-OCRv4_mobile_rec",
#             model_dir=ocr_model_dir,
#             device="cpu",
#             cpu_threads=1
#         )
#         self._warm_up_models()
#         logger.info("ScanningService initialized with YOLO and OCR models successfully.")


#     def _warm_up_models(self):
#         """Warm up models with dummy predictions to avoid first-time delays"""
#         try:
#             dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
            
#             # Warm up YOLO
#             logger.info("Warming up YOLO model...")
#             _ = self.yolo_model.predict(dummy_img, verbose=False)
            
#             # Warm up OCR
#             logger.info("Warming up OCR model...")
#             _ = self.ocr_model.predict(input=dummy_img, batch_size=1)
            
#             logger.info("Model warm-up completed.")
            
#         except Exception as e:
#             logger.warning(f"Model warm-up failed (but will continue): {e}")


#     def preprocess_image(self, img: UploadFile):
#         """
#         Preprocess meter display image for better OCR results
#         """    
#         print(f'original image shape: {img.shape}')
        
#         # 1. Resize image to make it bigger for better OCR
#         scale_factor = 10  # Adjust this value as needed (2x, 3x, 4x etc.)
#         height, width = img.shape[:2]
#         new_width = int(width * scale_factor)
#         new_height = int(height * scale_factor)
#         img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
#         print(f'resized image shape: {img.shape}')
        
#         # 2. Convert to grayscale for processing
#         img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
#         # 3. Noise reduction using Gaussian blur
#         # img = cv2.GaussianBlur(gray, (3, 3), 0)
        
#         # # 4. Advanced noise reduction using Non-local Means Denoising
#         # img = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)

#         # # 5. Contrast enhancement using CLAHE (Adaptive Histogram Equalization)
#         # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
#         # img = clahe.apply(img)
        
#         # # 6. Sharpening filter to make text clearer
#         # kernel = np.array([[-1,-1,-1],
#         #                 [-1, 9,-1],
#         #                 [-1,-1,-1]])
#         # img = cv2.filter2D(img, -1, kernel)
#         # 7. Morphological operations to clean up the image
#         # Remove small noise
#         # kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
#         # img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel_morph)

#         # 8. Adaptive thresholding for better text separation
#         # This helps with varying lighting conditions
#         # img = cv2.adaptiveThreshold(
#         #     img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         #     cv2.THRESH_BINARY, 11, 2
#         # )
        
#         # 9. Convert back to BGR for PaddleOCR (it expects 3-channel images)
#         img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
#         return img
         

#     def process_yolo_results(self, results, img_rgb, confidence_threshold=0.8):
#         try:
#             if not results or not hasattr(results[0], "boxes") or len(results[0].boxes) == 0:
#                 logger.info("No detections found in YOLO results.")
#                 return None

#             best_box = None
#             best_conf = -np.inf

#             for box in results[0].boxes:
#                 confidence = float(box.conf[0].cpu().numpy())
#                 if confidence >= confidence_threshold and confidence > best_conf:
#                     best_conf = confidence
#                     best_box = box

#             if best_box is not None:
#                 x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy().astype(int)
#                 cropped_detection = img_rgb[y1:y2, x1:x2]
#                 logger.info(f"Best detection found with confidence {best_conf:.2f} and shape {cropped_detection.shape}")
#                 return cropped_detection
#             else:
#                 logger.info(f"No detection above confidence threshold {confidence_threshold}")
#                 return None
            
#         except Exception as e:
#             logger.error(f"Error processing YOLO results: {e}")
#             raise e


#     def scan(self, image_bytes):
#         try:
#             np_arr = np.frombuffer(image_bytes, np.uint8)
#             img_rgb = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

#             results = self.yolo_model.predict(img_rgb)
#             cropped_detection = self.process_yolo_results(results,img_rgb)
#             if cropped_detection is None:
#                 logger.error("No valid detection found in the image.")
#                 return None

#             processed_detection = self.preprocess_image(cropped_detection)

#             output = self.ocr_model.predict(
#                 input=processed_detection, 
#                 batch_size=1
#             )
#             ocr_result = []
#             for res in output:
#                 print(f"Recognized text: {res.keys()}")
#                 text = res.get('rec_text')
#                 # Extract only digits from the recognized text
#                 digits = re.sub(r'\D', '', text) if text else ""
#                 result = {
#                     'rec_text': digits
#                 }
#                 ocr_result.append(result)
#                 # res.save_to_img(save_path="./output/")
#                 # res.save_to_json(save_path="./output/res.json")

#             return ocr_result


#         except Exception as e:
#             logger.error(f"Error occurred while scanning reading: {e}")
#             raise e


#     async def scan_reading(self, request: Request, session: AsyncSession, reading: Optional[UploadFile] = None):
#         await FileValidator.validate_file(
#                 file=reading,
#                 **FileValidationConfigs.IMAGES,
#                 require_file=True
#             )
#         meter_id = request.path_params.get('meter_id')
#         accept_reading = request.query_params.get('accept_reading', False)

#         try:
#             meter_id = UUID(meter_id)
#         except (TypeError, ValueError):
#             raise ValidationError({
#                 "field": "Meter ID",
#                 "error": "Invalid or missing meter ID."
#             })

#         try:
#             token = request.state.user
#             image_bytes = await reading.read()

#             if accept_reading:
#                 current_reading = request.query_params.get('current_reading')
#                 if not current_reading:
#                     raise ValidationError({
#                         "field": "current_reading",
#                         "error": "Current reading is required when accepting reading."
#                     })
#                 reading_data = {
#                     'meter_id': meter_id,
#                     'current_reading': float(current_reading),
#                     'created_by': token.get('user_id'),
#                     'updated_by': token.get('user_id'),
#                 }
#                 scanned_reading = await self.readings_queries.create_reading(
#                     session=session,
#                     reading_data=reading_data,
#                     image_bytes=BytesIO(image_bytes)
#                 )
#                 return success_response(
#                     message="Reading scanned successfully.",
#                     data=scanned_reading
#                 )

#             else:
#                 ocr_result = await asyncio.to_thread(self.scan, image_bytes)
#                 if not ocr_result:
#                     return success_response(
#                         message="No valid reading detected in the image.",
#                         data=None
#                     )

#                 reading_data = {
#                     'meter_id': meter_id,
#                     'current_reading': float(ocr_result[0]['rec_text']),
#                     'created_by': token.get('user_id'),
#                     'updated_by': token.get('user_id'),
#                 }

#                 return success_response(
#                     message="Are you sure you want to accept this reading?",
#                     data={
#                         "current_reading": float(ocr_result[0]['rec_text']),
#                     }
#                 )
        
#         except (
#             ValidationError,
#             DuplicateReadingDateException,
#             InvalidReadingValueException,
#             ReadingFrequencyException,
#             MeterNotFoundError,
#             InvalidReadingValueException,
#             FixedMeterCannotHaveUsageReadingsError,
#             MeterInactiveError
#             ):
#             raise

#         except Exception as e:
#             logger.error(f"Error occurred while scanning reading: {e}")
#             raise InternalServerError(message="An error occurred while scanning reading.")

