import cv2
import numpy as np
import matplotlib.pyplot as plt


def vis(img, boxes, scores, cls_ids, conf=0.5, class_names=None):
    for i in range(len(boxes)):
        box = boxes[i]
        cls_id = int(cls_ids[i])
        score = scores[i]
        if score < conf:
            continue
        x0 = int(box[0])
        y0 = int(box[1])
        x1 = int(box[2])
        y1 = int(box[3])

        color = (_COLORS[cls_id] * 255).astype(np.uint8).tolist()
        text = '{}:{:.1f}%'.format(class_names[cls_id], score * 100)
        txt_color = (0, 0, 0) if np.mean(_COLORS[cls_id]) > 0.5 else (255, 255, 255)
        font = cv2.FONT_HERSHEY_SIMPLEX

        txt_size = cv2.getTextSize(text, font, 0.4, 1)[0]
        cv2.rectangle(img, (x0, y0), (x1, y1), color, 2)

        txt_bk_color = (_COLORS[cls_id] * 255 * 0.7).astype(np.uint8).tolist()
        cv2.rectangle(
            img,
            (x0, y0 + 1),
            (x0 + txt_size[0] + 1, y0 + int(1.5 * txt_size[1])),
            txt_bk_color,
            -1
        )
        cv2.putText(img, text, (x0, y0 + txt_size[1]), font, 0.4, txt_color, thickness=1)

    return img


def draw_distance(im, left, top, right, bottom, distance):
    # 绘制bbox下沿中心坐标
    y = int(bottom)
    x = (left + right) // 2
    cv2.circle(im, (x, y), 4, (255, 178, 50), thickness=-1)

    # 绘制竖直线
    # cv2.line(im, (990, 295), (550, 1080), (0, 0, 255), thickness=1)
    # cv2.line(im, (960, 0), (960, 1080), (0, 0, 255), thickness=1)

    # 绘制distance
    cv2.putText(im, distance + 'm', (left, bottom + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)


def draw_in_radar(camera_frame, camera_class, radar_frame, fusion_frame, fusion_class, roi):
    xmax = 40
    xmin = -40
    ymax = 200
    ymin = 0
    factor = (ymax - ymin) / (xmax - xmin)
    plt.cla()
    plt.xlabel('x')
    plt.ylabel('z')
    plt.xlim(xmax=xmax, xmin=xmin)
    plt.ylim(ymax=ymax, ymin=ymin)
    plt.title('Fusion In Radar Coordinate', fontsize='large', fontweight='bold', verticalalignment='center')
    colors0 = '#DC143C'
    colors1 = '#00CED1'
    colors2 = '#800000'
    colors3 = '#000000'
    area = np.pi * 4 ** 2  # 点面积

    draw_roi(roi, colors3)

    if len(radar_frame) > 0:
        plt.scatter(radar_frame[:, 0], radar_frame[:, 2], s=area, c=colors0, alpha=0.4, label='radar')
    if len(camera_frame) > 0:
        draw_rectangle(camera_frame, camera_class, factor, colors1, 'camera')
    if len(fusion_frame) > 0:
        draw_rectangle(fusion_frame, fusion_class, factor, colors2, 'fusion')

    plt.legend()
    plt.pause(0.01)


def draw_roi(roi, color):
    x0, z0 = roi[0], roi[1]
    x1, z1 = roi[2], roi[3]
    left_down_x = x0
    left_down_z = z1
    width = x1 - x0
    height = z0 - z1
    plt.gca().add_patch(plt.Rectangle(xy=(left_down_x, left_down_z),
                                      width=width,
                                      height=height,
                                      edgecolor=color,
                                      fill=False, linewidth=1, linestyle='--'))


def draw_rectangle(frame, classes, factor, color, label):
    for index in range(len(frame)):
        x = frame[index, 0]
        z = frame[index, 2]
        class_name = classes[index]

        if class_name in _CLASS_SIZE:
            width = _CLASS_SIZE.get(class_name)[0]
            height = _CLASS_SIZE.get(class_name)[1]
            left_down_x = x - width / 2
            left_down_z = z - height / 2
            if z < 60:
                width, height = height, width
            if index == 0:
                plt.gca().add_patch(plt.Rectangle(xy=(left_down_x, left_down_z),
                                                  width=width,
                                                  height=height * factor,
                                                  edgecolor=color,
                                                  fill=False, linewidth=1, label=label))
            else:
                plt.gca().add_patch(plt.Rectangle(xy=(left_down_x, left_down_z),
                                                  width=width,
                                                  height=height * factor,
                                                  edgecolor=color,
                                                  fill=False, linewidth=1))


_CLASS_SIZE = {
    'car': [2, 4],
    'truck': [3, 6],
    'bus': [4, 10],
    'people': [1, 1.5],
    'motorcycle': [1, 1.5]
}

_COLORS = np.array(
    [
        0.000, 0.447, 0.741,
        0.850, 0.325, 0.098,
        0.929, 0.694, 0.125,
        0.494, 0.184, 0.556,
        0.466, 0.674, 0.188,
        0.301, 0.745, 0.933,
        0.635, 0.078, 0.184,
        0.300, 0.300, 0.300,
        0.600, 0.600, 0.600,
        1.000, 0.000, 0.000,
        1.000, 0.500, 0.000,
        0.749, 0.749, 0.000,
        0.000, 1.000, 0.000,
        0.000, 0.000, 1.000,
        0.667, 0.000, 1.000,
        0.333, 0.333, 0.000,
        0.333, 0.667, 0.000,
        0.333, 1.000, 0.000,
        0.667, 0.333, 0.000,
        0.667, 0.667, 0.000,
        0.667, 1.000, 0.000,
        1.000, 0.333, 0.000,
        1.000, 0.667, 0.000,
        1.000, 1.000, 0.000,
        0.000, 0.333, 0.500,
        0.000, 0.667, 0.500,
        0.000, 1.000, 0.500,
        0.333, 0.000, 0.500,
        0.333, 0.333, 0.500,
        0.333, 0.667, 0.500,
        0.333, 1.000, 0.500,
        0.667, 0.000, 0.500,
        0.667, 0.333, 0.500,
        0.667, 0.667, 0.500,
        0.667, 1.000, 0.500,
        1.000, 0.000, 0.500,
        1.000, 0.333, 0.500,
        1.000, 0.667, 0.500,
        1.000, 1.000, 0.500,
        0.000, 0.333, 1.000,
        0.000, 0.667, 1.000,
        0.000, 1.000, 1.000,
        0.333, 0.000, 1.000,
        0.333, 0.333, 1.000,
        0.333, 0.667, 1.000,
        0.333, 1.000, 1.000,
        0.667, 0.000, 1.000,
        0.667, 0.333, 1.000,
        0.667, 0.667, 1.000,
        0.667, 1.000, 1.000,
        1.000, 0.000, 1.000,
        1.000, 0.333, 1.000,
        1.000, 0.667, 1.000,
        0.333, 0.000, 0.000,
        0.500, 0.000, 0.000,
        0.667, 0.000, 0.000,
        0.833, 0.000, 0.000,
        1.000, 0.000, 0.000,
        0.000, 0.167, 0.000,
        0.000, 0.333, 0.000,
        0.000, 0.500, 0.000,
        0.000, 0.667, 0.000,
        0.000, 0.833, 0.000,
        0.000, 1.000, 0.000,
        0.000, 0.000, 0.167,
        0.000, 0.000, 0.333,
        0.000, 0.000, 0.500,
        0.000, 0.000, 0.667,
        0.000, 0.000, 0.833,
        0.000, 0.000, 1.000,
        0.000, 0.000, 0.000,
        0.143, 0.143, 0.143,
        0.286, 0.286, 0.286,
        0.429, 0.429, 0.429,
        0.571, 0.571, 0.571,
        0.714, 0.714, 0.714,
        0.857, 0.857, 0.857,
        0.000, 0.447, 0.741,
        0.314, 0.717, 0.741,
        0.50, 0.5, 0
    ]
).astype(np.float32).reshape(-1, 3)
