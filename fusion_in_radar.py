from Fusion.init.args_init import make_parser, args_analysis
from Fusion.yolox.predictor import Predictor
from Fusion.radar.radar import Radar
from Fusion.utils.convert import calculate_depth, convert_to_world
from Fusion.utils.visualize import draw_distance
from Fusion.fusion_in_radar.fusion import process_fusion
from Fusion.save.save import Saver
from YOLOX.yolox.data.datasets import COCO_CLASSES
import matplotlib.pyplot as plt
import cv2
import time
import os
import numpy as np
from loguru import logger


def process_camera(predictor, frame):
    img_outputs, img_info = predictor.inference(frame)
    img_result, bboxes, cls, scores = predictor.visual(img_outputs[0], img_info, predictor.confthre)
    camera_frame, camera_class, camera_scores = [], [], []
    if len(bboxes) > 0:
        for index in range(len(bboxes)):

            score = scores[index]
            if score < predictor.confthre:
                continue

            cls_id = int(cls[index])
            class_name = COCO_CLASSES[cls_id]

            left = int(bboxes[index, 0])
            top = int(bboxes[index, 1])
            right = int(bboxes[index, 2])
            bottom = int(bboxes[index, 3])

            # get camera
            rect_roi = [left, top, right, bottom]
            camera_xyz, distance = calculate_depth(rect_roi)

            # get world
            camera_xyz_in_world = convert_to_world(camera_xyz)

            # append
            camera_frame.append([camera_xyz_in_world[0, 0],
                                 camera_xyz_in_world[0, 1],
                                 camera_xyz_in_world[0, 2]])
            camera_scores.append(score)
            camera_class.append(class_name)

            # draw
            draw_distance(img_result, left, top, right, bottom, distance)

    return img_result, np.array(camera_frame), np.array(camera_scores), np.array(camera_class)


def process_radar(read_data, time_factor, cnt):
    radar_cnt = int(cnt / time_factor)
    radar_frame = read_data[radar_cnt]
    return radar_frame


def get_time_factor(radar_len, video_len):
    logger.info(f"radar_len: {radar_len}")
    logger.info(f"video_len: {video_len}")
    if radar_len == 0 or video_len == 0:
        return 0
    factor = (video_len + 1) / radar_len
    return factor


def fusion_in_radar(predictor, radar, vis_folder, args):
    # cap
    current_time = time.localtime()
    cap = cv2.VideoCapture(args.path)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)  # float
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float
    fps = cap.get(cv2.CAP_PROP_FPS)

    # save mp4
    save_folder = os.path.join(
        vis_folder, time.strftime("fusion_in_radar/%Y_%m_%d_%H_%M_%S", current_time)
    )
    os.makedirs(save_folder, exist_ok=True)
    save_path = os.path.join(save_folder, args.path.split("/")[-1])
    logger.info(f"video save_path is {save_path}")

    # VideoWriter
    vid_writer = cv2.VideoWriter(
        save_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (int(width), int(height))
    )

    # we or euclidean_distance or ...(0,1...)
    mode = 0

    # save_init
    saver = Saver(current_time, mode)

    # radar
    read_data = radar.read_data()

    # time_factor
    time_factor = get_time_factor(len(read_data), cap.get(7))
    if time_factor == 0:
        logger.info("camera_data or radar_data is empty!")

    # start
    cnt = -1
    plt.ion()
    while True:
        cnt += 1
        ret_val, frame = cap.read()
        if ret_val:
            img_result, camera_frame, camera_scores, camera_class = process_camera(predictor, frame)

            radar_frame = process_radar(read_data, time_factor, cnt)

            fusion_frame, fusion_class = process_fusion(
                camera_frame, camera_scores, camera_class, radar_frame, mode)

            saver.fusion_save(fusion_frame, fusion_class, cnt)

            cv2.imshow("Fusion", img_result)
            if args.save_result:
                vid_writer.write(img_result)
            ch = cv2.waitKey(1)
            if ch == 27 or ch == ord("q") or ch == ord("Q"):
                break
        else:
            logger.info("Processing done!")
            break
    cap.release()
    cv2.destroyAllWindows()
    saver.fusion_csv_f.close()


if __name__ == '__main__':
    args = make_parser().parse_args()
    model, exp, decoder, vis_folder = args_analysis(args)
    predictor = Predictor(model, exp, COCO_CLASSES, decoder, args.device)
    radar = Radar(args.radar_data_path)
    fusion_in_radar(predictor, radar, vis_folder, args)
