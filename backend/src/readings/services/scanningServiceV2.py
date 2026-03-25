import onnxruntime as ort
from fastapi import Request, UploadFile
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from globals.utils.fileValidator import FileValidator, FileValidationConfigs
import os
from src.readings.queries.readingsQueries import ReadingsQueries
import re 
import asyncio  
import cv2
import numpy as np
from io import BytesIO
from rapidocr import RapidOCR

from uuid import UUID

from src.meters.exceptions.exceptions import (
    MeterNotFoundError,
    MeterInactiveError
)
from src.readings.exceptions.exceptions import (
    DuplicateReadingDateException,
    ReadingFrequencyException,
    InvalidReadingValueException,
    FixedMeterCannotHaveUsageReadingsError,
    
)




class ScanningService:

    def __init__(self, readings_queries: ReadingsQueries):
        self.readings_queries = readings_queries
        # Base models directory (absolute path)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))

        # models path
        yolo_model_path = os.path.join(base_dir, "yolo", "best.onnx")
        ocr_model_config_path = os.path.join(base_dir, "ocr", "config.yml")

        
        # ocr_model_dir = os.path.join(base_dir, "ocr", "PP-OCRv5_mobile_rec_infer")
        self.ocr_model = RapidOCR(
            config_path=ocr_model_config_path
            )

        self.yolo_session = ort.InferenceSession(yolo_model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.yolo_session.get_inputs()[0].name
        _, _, h, w = self.yolo_session.get_inputs()[0].shape
        self.in_h, self.in_w = int(h), int(w)
        self.conf_threshold = 0.8
        self.iou_threshold = 0.45 

        self._warm_up_models()
        logger.info("ScanningService initialized with YOLO and OCR models successfully.")


    def _warm_up_models(self):
        """Warm up models with dummy predictions to avoid first-time delays"""
        try:
            dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
            
            # Warm up YOLO
            logger.info("Warming up YOLO (ONNX) yolo_session...")
            dummy_bgr = np.zeros((self.in_h, self.in_w, 3), dtype=np.uint8)
            img, _, _ = self.preprocess(dummy_bgr)  
            ort_inputs = {self.input_name: img.astype(np.float32)}
            _ = self.yolo_session.run(None, ort_inputs)
            logger.info("Warming up YOLO (ONNX) yolo_session completed.")

            # Warm up OCR
            logger.info("Warming up OCR model...")
            _ = self.ocr_model(dummy_img)
            
            logger.info("Model warm-up completed.")
            
        except Exception as e:
            logger.warning(f"Model warm-up failed (but will continue): {e}")


    def letterbox(self, im, new_shape=(640, 640), color=(114, 114, 114)):
        try:
            h, w = im.shape[:2]
            r = min(new_shape[0] / h, new_shape[1] / w)
            new_unpad = (int(round(w * r)), int(round(h * r)))
            dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
            dw /= 2
            dh /= 2
            if (w, h) != new_unpad:
                im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
            top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
            left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
            im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
            logger.info(f"Letterboxed image shape: {im.shape}")
            return im, r, (left, top)
        
        except Exception as e:
            logger.error(f"Error in letterbox: {e}")    
            raise e


    def nms(self, boxes, scores, iou_thres=0.45):
        try:    
            if len(boxes) == 0:
                return []
            boxes = np.array(boxes, dtype=np.float32)
            scores = np.array(scores, dtype=np.float32)
            x1, y1, x2, y2 = boxes.T
            areas = (x2 - x1 + 1) * (y2 - y1 + 1)
            order = scores.argsort()[::-1]
            keep = []
            while order.size > 0:
                i = order[0]
                keep.append(i)
                xx1 = np.maximum(x1[i], x1[order[1:]])
                yy1 = np.maximum(y1[i], y1[order[1:]])
                xx2 = np.minimum(x2[i], x2[order[1:]])
                yy2 = np.minimum(y2[i], y2[order[1:]])
                w = np.maximum(0.0, xx2 - xx1 + 1)
                h = np.maximum(0.0, yy2 - yy1 + 1)
                inter = w * h
                ovr = inter / (areas[i] + areas[order[1:]] - inter)
                inds = np.where(ovr <= iou_thres)[0]
                order = order[inds + 1]
            logger.info(f"NMS applied, {len(keep)} boxes kept after filtering.")
            return keep
        
        except Exception as e:
            logger.error(f"Error in NMS: {e}")
            raise e


    def sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-x))


    def preprocess(self, img_bgr):
        img_lb, gain, pad = self.letterbox(img_bgr, (self.in_h, self.in_w))
        try:
            img_rgb = cv2.cvtColor(img_lb, cv2.COLOR_BGR2RGB)
            img = img_rgb.astype(np.float32) / 255.0
            img = img.transpose(2, 0, 1)[None, ...]  # NCHW
            logger.info(f"Preprocessed image successfully, image shape: {img.shape}")
            return img, gain, pad
        
        except Exception as e:
            logger.error(f"Error in preprocessing image: {e}")
            raise e


    def decode(self, output):
        try:
            # Make shape (N, C)
            if output.ndim == 3:
                output = np.squeeze(output, 0)
            if output.shape[0] in (5, 6, 85):  # transpose if needed
                output = output.T

            # Single-class: (N, 5) -> [x,y,w,h,conf]
            # Multi-class:  (N, 5+nc) -> [x,y,w,h,obj, class_probs...]
            num_attrs = output.shape[1]
            boxes = []
            scores = []

            # If logits look unbounded, apply sigmoid to confidences and class probs
            if num_attrs == 5:
                xywh = output[:, :4]
                conf = output[:, 4]
                if conf.max() > 1.0 or conf.min() < 0.0:
                    conf = self.sigmoid(conf)
                sel = conf >= self.conf_threshold
                xywh = xywh[sel]
                conf = conf[sel]
                for (x, y, w, h), c in zip(xywh, conf):
                    x1 = x - w / 2
                    y1 = y - h / 2
                    x2 = x + w / 2
                    y2 = y + h / 2
                    boxes.append([x1, y1, x2, y2])
                    scores.append(float(c))
                logger.info(f"Decoded {len(boxes)} boxes with scores.")
            else:
                xywh = output[:, :4]
                obj = output[:, 4]
                cls = output[:, 5:]
                # Apply sigmoid if necessary
                if obj.max() > 1.0 or obj.min() < 0.0:
                    obj = self.sigmoid(obj)
                    cls = self.sigmoid(cls)
                cls_id = np.argmax(cls, axis=1)
                cls_score = cls[np.arange(cls.shape[0]), cls_id]
                conf = obj * cls_score
                sel = conf >= self.conf_threshold
                xywh = xywh[sel]
                conf = conf[sel]
                for (x, y, w, h), c in zip(xywh, conf):
                    x1 = x - w / 2
                    y1 = y - h / 2
                    x2 = x + w / 2
                    y2 = y + h / 2
                    boxes.append([x1, y1, x2, y2])
                    scores.append(float(c))
            logger.info(f"Decoded {len(boxes)} boxes with scores.")
            return np.array(boxes, dtype=np.float32), np.array(scores, dtype=np.float32)
        
        except Exception as e:
            logger.error(f"Error in decoding output: {e}")
            raise e


    def scale_back(self, boxes, gain, pad):
        try:
            if len(boxes) == 0:
                return boxes
            # Remove padding, then divide by gain
            boxes[:, [0, 2]] -= pad[0]
            boxes[:, [1, 3]] -= pad[1]
            boxes /= gain
            logger.info(f"Scaled back {len(boxes)} boxes")
            return boxes
        
        except Exception as e:
            logger.error(f"Error in scaling back boxes: {e}")
            raise e
        

    def yolo_predict(self, image_bgr):
        img, gain, pad = self.preprocess(image_bgr)
        ort_inputs = {self.input_name: img.astype(np.float32)}
        outputs = self.yolo_session.run(None, ort_inputs)
        out = outputs[0]
        boxes, scores = self.decode(out)
        boxes = self.scale_back(boxes, gain, pad)

        # Clip to image size
        h, w = image_bgr.shape[:2]
        if len(boxes) > 0:
            boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, w - 1)
            boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, h - 1)

        # NMS
        keep = self.nms(boxes, scores, iou_thres=self.iou_threshold)
        boxes = boxes[keep].astype(int).tolist()
        scores = [float(scores[i]) for i in keep]
        logger.info(f"YOLO predictions: {len(boxes)} boxes detected.")
        return boxes, scores
    

    def process_yolo_results(self, results, image):
        try:
            boxes, scores = results
            if len(boxes) == 0:
                return None

            best_box = None
            best_score = 0.0
            for box, score in zip(boxes, scores):
                if score > best_score:
                    best_score = score
                    best_box = box

            detection = image[best_box[1]:best_box[3], best_box[0]:best_box[2]]
            logger.info(f"Processed YOLO results, best detected box score: {best_score}")
            return detection

        except Exception as e:
            logger.error(f"Error in processing YOLO results: {e}")
            return None
        

    def preprocess_image(self, img: UploadFile):
        """
        Preprocess meter display image for better OCR results
        """    
        try:
            # 1. Resize image to make it bigger for better OCR
            scale_factor = 10  # Adjust this value as needed (2x, 3x, 4x etc.)
            height, width = img.shape[:2]
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 2. Convert to grayscale for processing
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            logger.info(f"Preprocessed image successfully, image shape: {img.shape}")
            return img

        except Exception as e:
            logger.error(f"Error in preprocessing image: {e}")
            return None
        

    def scan(self, image_bytes):
        try:
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img_rgb = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            results = self.yolo_predict(img_rgb)
            cropped_detection = self.process_yolo_results(results,img_rgb)
            if cropped_detection is None:
                logger.error("No valid detection found in the image.")
                return None

            processed_detection = self.preprocess_image(cropped_detection)

            output = self.ocr_model(processed_detection)
            if hasattr(output, "txts"):
                raw_text = "".join(output.txts) if isinstance(output.txts, (list, tuple)) else str(output.txts)
                logger.info(f"OCR output (txts): {output.txts}")

            elif isinstance(output, (list, tuple)):
                parts = []
                for item in output:
                    if isinstance(item, dict) and "rec_text" in item:
                        parts.append(str(item["rec_text"]))
                    elif isinstance(item, (list, tuple)) and len(item) >= 2:
                        # Common RapidOCR item format: [box, text, score]
                        parts.append(str(item[1]))
                    else:
                        parts.append(str(item))
                raw_text = "".join(parts)
                
            else:
                raw_text = str(output)

            # Option A: keep all digits
            digits = re.sub(r"\D+", "", raw_text)
            # Option B (if you prefer the longest numeric run):
            # groups = re.findall(r"\d+", raw_text)
            # digits = max(groups, key=len) if groups else ""

            ocr_result = [{"rec_text": digits}]
            logger.info(f"scanning was successful with reading: {ocr_result}")
            return ocr_result

        except Exception as e:
            logger.error(f"Error occurred while scanning reading: {e}")
            raise e


    async def scan_reading(self, request: Request, session: AsyncSession, reading: Optional[UploadFile] = None):
        await FileValidator.validate_file(
                file=reading,
                **FileValidationConfigs.IMAGES,
                require_file=True
            )
        meter_id = request.path_params.get('meter_id')
        accept_reading = request.query_params.get('accept_reading', False)

        try:
            meter_id = UUID(meter_id)
        except (TypeError, ValueError):
            raise ValidationError({
                "field": "Meter ID",
                "error": "Invalid or missing meter ID."
            })

        try:
            token = request.state.user
            image_bytes = await reading.read()

            if accept_reading:
                current_reading = request.query_params.get('current_reading')
                if not current_reading:
                    raise ValidationError({
                        "field": "current_reading",
                        "error": "Current reading is required when accepting reading."
                    })
                reading_data = {
                    'meter_id': meter_id,
                    'current_reading': float(current_reading),
                    'created_by': token.get('user_id'),
                    'updated_by': token.get('user_id'),
                }
                scanned_reading = await self.readings_queries.create_reading(
                    session=session,
                    reading_data=reading_data,
                    image_bytes=BytesIO(image_bytes)
                )
                return success_response(
                    message="Reading scanned successfully.",
                    data=scanned_reading
                )

            else:
                ocr_result = await asyncio.to_thread(self.scan, image_bytes)
                if not ocr_result:
                    return success_response(
                        message="No valid reading detected in the image.",
                        data=None
                    )

                reading_data = {
                    'meter_id': meter_id,
                    'current_reading': float(ocr_result[0]['rec_text']),
                    'created_by': token.get('user_id'),
                    'updated_by': token.get('user_id'),
                }

                return success_response(
                    message="Are you sure you want to accept this reading?",
                    data={
                        "current_reading": float(ocr_result[0]['rec_text']),
                    }
                )
        
        except (
            ValidationError,
            DuplicateReadingDateException,
            InvalidReadingValueException,
            ReadingFrequencyException,
            MeterNotFoundError,
            InvalidReadingValueException,
            FixedMeterCannotHaveUsageReadingsError,
            MeterInactiveError
            ):
            raise

        except Exception as e:
            logger.error(f"Error occurred while scanning reading: {e}")
            raise InternalServerError(message="An error occurred while scanning reading.")
    



        

    # def visualize(self, image_bgr, boxes, scores):
    #     vis = image_bgr.copy()
    #     for (x1, y1, x2, y2), s in zip(boxes, scores):
    #         cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #         cv2.putText(vis, f"meter_display {s:.2f}", (x1, max(0, y1 - 8)),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    #     plt.figure(figsize=(10, 8))
    #     plt.imshow(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
    #     plt.axis('off')
    #     plt.title('YOLO ONNX detections')
    #     plt.show()
 
# if __name__ == "__main__":
#     model_path = r"D:\GCP\meters-readings-detection\inference\best.onnx"
#     yolo = ScanningService(model_path)

#     img_path = r"D:\GCP\meters-readings-detection\meter_data\meter_data\images\train\meter_reading_20250731_141822_aug_brightness_contrast_1_20250801_143136.jpg"
#     img = cv2.imread(img_path)

#     boxes, scores = yolo.predict(img)
#     if boxes:
#         print(f"Detections: {len(boxes)}")
#         for i, (b, s) in enumerate(zip(boxes, scores), 1):
#             print(f"{i}: {b}  conf={s:.2f}")
#         yolo.visualize(img, boxes, scores)
#     else:
#         print("No detections")



