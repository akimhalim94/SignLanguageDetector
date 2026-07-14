"""
overlay_drawing.py
Draws hand bounding boxes + keypoint skeletons and face bounding boxes
onto an RGB frame, using the normalized coordinates produced by
LandmarkDetector. Kept separate from detection logic so the visuals can
be restyled without touching any MediaPipe code.
"""

import cv2

import config


def _denormalize_box(box, width, height, pad_frac=0.04):
    xmin, ymin, xmax, ymax = box
    pad_x = (xmax - xmin) * pad_frac
    pad_y = (ymax - ymin) * pad_frac

    px_xmin = int(max(0.0, xmin - pad_x) * width)
    px_ymin = int(max(0.0, ymin - pad_y) * height)
    px_xmax = int(min(1.0, xmax + pad_x) * width)
    px_ymax = int(min(1.0, ymax + pad_y) * height)
    return px_xmin, px_ymin, px_xmax, px_ymax


def draw_detections(frame_rgb, detections, draw_hands=True, draw_face=True):
    height, width = frame_rgb.shape[:2]

    if draw_face:
        for face in detections.get("faces", []):
            x1, y1, x2, y2 = _denormalize_box(face["box"], width, height, pad_frac=0.08)
            cv2.rectangle(
                frame_rgb, (x1, y1), (x2, y2), config.COLOR_FACE_BOX_BGR, 2
            )
            _draw_label(frame_rgb, "Face", x1, y1, config.COLOR_FACE_BOX_BGR)

    if draw_hands:
        connections = detections.get("hand_connections")
        for hand in detections.get("hands", []):
            x1, y1, x2, y2 = _denormalize_box(hand["box"], width, height)
            cv2.rectangle(
                frame_rgb, (x1, y1), (x2, y2), config.COLOR_HAND_BOX_BGR, 2
            )
            label = hand.get("label") or "Hand"
            _draw_label(frame_rgb, label, x1, y1, config.COLOR_HAND_BOX_BGR)

            points_px = [(int(px * width), int(py * height)) for px, py in hand["points"]]

            if connections:
                for start_idx, end_idx in connections:
                    if start_idx < len(points_px) and end_idx < len(points_px):
                        cv2.line(
                            frame_rgb,
                            points_px[start_idx],
                            points_px[end_idx],
                            config.COLOR_HAND_LINE_BGR,
                            1,
                            lineType=cv2.LINE_AA,
                        )

            for (px, py) in points_px:
                cv2.circle(
                    frame_rgb, (px, py), 3, config.COLOR_HAND_POINT_BGR, -1,
                    lineType=cv2.LINE_AA,
                )

    return frame_rgb


def _draw_label(frame_rgb, text, x, y, color_bgr):
    """Small filled label tag above a bounding box's top-left corner."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    tag_y2 = max(y, text_h + 8)
    tag_y1 = tag_y2 - text_h - 8
    cv2.rectangle(frame_rgb, (x, tag_y1), (x + text_w + 10, tag_y2), color_bgr, -1)
    cv2.putText(
        frame_rgb,
        text,
        (x + 5, tag_y2 - 5),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
        lineType=cv2.LINE_AA,
    )
