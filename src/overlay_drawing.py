"""
overlay_drawing.py
Draw cleaner hand and face overlays on the camera frame.
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


def _draw_corner_box(frame, x1, y1, x2, y2, color, thickness=3):
    """
    Draw corner lines instead of one heavy rectangle.
    This gives the camera overlay a cleaner appearance.
    """
    width = max(x2 - x1, 1)
    height = max(y2 - y1, 1)
    corner = max(min(width, height) // 5, 16)

    # Top-left
    cv2.line(frame, (x1, y1), (x1 + corner, y1), color, thickness, cv2.LINE_AA)
    cv2.line(frame, (x1, y1), (x1, y1 + corner), color, thickness, cv2.LINE_AA)

    # Top-right
    cv2.line(frame, (x2, y1), (x2 - corner, y1), color, thickness, cv2.LINE_AA)
    cv2.line(frame, (x2, y1), (x2, y1 + corner), color, thickness, cv2.LINE_AA)

    # Bottom-left
    cv2.line(frame, (x1, y2), (x1 + corner, y2), color, thickness, cv2.LINE_AA)
    cv2.line(frame, (x1, y2), (x1, y2 - corner), color, thickness, cv2.LINE_AA)

    # Bottom-right
    cv2.line(frame, (x2, y2), (x2 - corner, y2), color, thickness, cv2.LINE_AA)
    cv2.line(frame, (x2, y2), (x2, y2 - corner), color, thickness, cv2.LINE_AA)


def draw_detections(
    frame_rgb,
    detections,
    draw_hands=True,
    draw_face=False,
):
    height, width = frame_rgb.shape[:2]

    if draw_face:
        for face in detections.get("faces", []):
            x1, y1, x2, y2 = _denormalize_box(
                face["box"],
                width,
                height,
                pad_frac=0.08,
            )
            _draw_corner_box(
                frame_rgb,
                x1,
                y1,
                x2,
                y2,
                config.COLOR_FACE_BOX_BGR,
                thickness=2,
            )
            _draw_label(
                frame_rgb,
                "Face",
                x1,
                y1,
                config.COLOR_FACE_BOX_BGR,
            )

    if draw_hands:
        connections = detections.get("hand_connections")

        for hand in detections.get("hands", []):
            x1, y1, x2, y2 = _denormalize_box(
                hand["box"],
                width,
                height,
            )

            _draw_corner_box(
                frame_rgb,
                x1,
                y1,
                x2,
                y2,
                config.COLOR_HAND_BOX_BGR,
                thickness=3,
            )

            label = hand.get("label") or "Hand detected"
            _draw_label(
                frame_rgb,
                label,
                x1,
                y1,
                config.COLOR_HAND_BOX_BGR,
            )

            points_px = [
                (int(px * width), int(py * height))
                for px, py in hand["points"]
            ]

            if connections:
                for start_index, end_index in connections:
                    if (
                        start_index < len(points_px)
                        and end_index < len(points_px)
                    ):
                        cv2.line(
                            frame_rgb,
                            points_px[start_index],
                            points_px[end_index],
                            config.COLOR_HAND_LINE_BGR,
                            2,
                            lineType=cv2.LINE_AA,
                        )

            for point_x, point_y in points_px:
                cv2.circle(
                    frame_rgb,
                    (point_x, point_y),
                    3,
                    config.COLOR_HAND_POINT_BGR,
                    -1,
                    lineType=cv2.LINE_AA,
                )

    return frame_rgb


def _draw_label(frame_rgb, text, x, y, color_bgr):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.52
    thickness = 1

    (text_width, text_height), _baseline = cv2.getTextSize(
        text,
        font,
        font_scale,
        thickness,
    )

    tag_height = text_height + 12
    tag_width = text_width + 18

    tag_y2 = max(y, tag_height)
    tag_y1 = tag_y2 - tag_height

    cv2.rectangle(
        frame_rgb,
        (x, tag_y1),
        (x + tag_width, tag_y2),
        color_bgr,
        -1,
    )

    cv2.putText(
        frame_rgb,
        text,
        (x + 9, tag_y2 - 7),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
        lineType=cv2.LINE_AA,
    )
