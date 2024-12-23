import sys
import os
from os import listdir
from os.path import isfile, join

import random
import math

import cv2

import albumentations as A
from matplotlib import pyplot as plt
import json

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

def get_points(image_dict):
    points = []
    labels = []

    for i in range(len(image_dict['regions'])):
        for j in range(len(image_dict['regions'][i]['shape_attributes']['all_points_x'])):
            curr = (image_dict['regions'][i]['shape_attributes']['all_points_x'][j],
                    image_dict['regions'][i]['shape_attributes']['all_points_y'][j])
            points.append(curr)
            labels.append(str(i))

    return points, labels

def get_lists(keypoints):
    all_points_x = []
    all_points_y = []

    for x, y in keypoints:
        all_points_x.append(x)
        all_points_y.append(y)
    return all_points_x, all_points_y

def fix_keypoints(img, keypoints_, labels_):
    keypoints = []
    labels = []
    flags = []
    h, w, _ = img.shape
    curr = []
    img_polygon = Polygon([ (0, 0), (0, h), (w, h), (w, 0) ])

    i = 0
    for point, label in zip(keypoints_, labels_):
        i += 1
        point = (int(point[0]), int(point[1]))
        curr.append(point)

        if i == len(labels_) or labels_[i] != label:
            curr_polygon = Polygon(curr)
            curr = []
            flags.append(img_polygon.contains(curr_polygon))
            intersection = img_polygon.intersection(curr_polygon)
            l = list(intersection.exterior.coords)[1:]
            for p in l:
                keypoints.append((int(p[0]), int(p[1])))
                labels.append(label)

    return keypoints, labels, flags

def get_regions(initial_regions, keypoints, labels, flags):
    fl_index = 0
    regions = []
    curr_x, curr_y = [], []
    for i in range(len(labels)):
        curr_x.append(keypoints[i][0])
        curr_y.append(keypoints[i][1])
        if i + 1 == len(labels) or labels[i + 1] != labels[i]:
            curr_dict = dict(initial_regions[int(labels[i])])
            old_len = len(curr_dict['shape_attributes']['all_points_x'])
            curr_dict['shape_attributes']['all_points_x'] = curr_x
            curr_dict['shape_attributes']['all_points_y'] = curr_y
            if not flags[fl_index]:
                curr_dict['region_attributes']['code integrity'] = 'invalid'
            regions.append(curr_dict)
            curr_x, curr_y = [], []
            fl_index += 1

    return regions

def dist(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

def max_diagonal(polygon_list):
    max_diagonal_length = 0

    for i in range(len(polygon_list)):
        for j in range(i+1, len(polygon_list)):
            x1, y1 = polygon_list[i]
            x2, y2 = polygon_list[j]
            diagonal_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if diagonal_length > max_diagonal_length:
                max_diagonal_length = diagonal_length

    return max_diagonal_length

def augment(image_path, full_data, output_folder):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_name = image_path.split('/')[-1].split('.')[0]

    min_edge = 1e4

    for full_name, file_data_ in full_data['_via_img_metadata'].items():
        file_data = dict(file_data_)
        if image_name in full_name:
            keypoints, labels = get_points(file_data)
            i = 0
            curr = []
            for point, label in zip(keypoints, labels):
                curr.append(point)
                i += 1
                if i == len(labels) or label != labels[i]:
                    min_edge = min(min_edge, max_diagonal(curr))
                    curr = []
            break

    blur_limit = math.floor(min_edge * 0.05)
    low_limit = blur_limit // 2

    if blur_limit % 2 == 0:
        blur_limit -= 1

    if low_limit % 2 == 0:
        low_limit -= 1

    transform = A.Compose([
        A.Perspective(p=0.7, scale=(0.1, 0.3)),
        A.GaussianBlur(p=0.5, blur_limit=(low_limit, blur_limit)),
        A.RandomBrightnessContrast(p=0.5, brightness_limit=(-0.3, 0.3), contrast_limit=(-0.2, 0.2)),
        A.ISONoise(p=0.3, intensity=(0.1, 0.5)),
        A.GaussNoise(p=0.3, std_range=(0.1, 0.4)),
    ], keypoint_params=A.KeypointParams(format='xy', label_fields=['class_labels'], remove_invisible=False))

    for full_name, file_data_ in full_data['_via_img_metadata'].items():
        file_data = dict(file_data_)
        if image_name in full_name:
            keypoints, labels = get_points(file_data)

            transformed = transform(image=image, keypoints=keypoints, class_labels=labels)
            transformed_image = transformed['image']

            transformed_keypoints, transformed_labels, flags = fix_keypoints(transformed_image, transformed['keypoints'], transformed['class_labels'])

            file_data['regions'] = get_regions(file_data['regions'], transformed_keypoints, transformed_labels, flags)

            transformed_image_name = image_name.split('.')[-1] + '_' + str(random.randint(1, 10 ** 5)) + '.jpg'
            file_data['filename'] = transformed_image_name

            plt.imsave('/'.join([output_folder, transformed_image_name]), transformed_image)
            return file_data
        

def write_results(initial_data, image_markups_list, output_file_name):
    image_markups_dict = {}
    id_list = []

    for image_markup in image_markups_list:
        curr_file_name = image_markup['filename']
        curr_id = curr_file_name + str(image_markup['size'])
        id_list.append(curr_id)
        image_markups_dict[curr_id] = image_markup
    
    res_data = dict(initial_data)
    res_data['_via_img_metadata'] = image_markups_dict
    res_data['_via_image_id_list'] = id_list

    with open(output_file_name, "w") as f:
        json.dump(res_data, f)


def main(image_folder_path, markup_path, replication_factor):
    files_list = [f for f in listdir(image_folder_path) if isfile(join(image_folder_path, f))]
    output_folder = 'augmented_images'

    with open(markup_path, 'r') as f:
        markup_data = json.load(f)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    augmented_image_markups_list = []

    for image_name in files_list:
        path_to_image = "/".join([image_folder_path, image_name])

        for _ in range(int(replication_factor)):
            augmented_image_markup = augment(path_to_image, markup_data, output_folder)
            augmented_image_markups_list.append(augmented_image_markup)

    write_results(markup_data, augmented_image_markups_list, 'augmented_markup.json')

if __name__ == '__main__':
    argv = sys.argv
    main(argv[1], argv[2], argv[3])
