import sys
import os
from os import listdir
from os.path import isfile, join

import random

import cv2

import albumentations as A
from matplotlib import pyplot as plt
import json

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

def fix_keypoints(keypoints_):
    keypoints = []
    for point in keypoints_:
        keypoints.append((int(point[0]), int(point[1])))
    return keypoints

def get_regions(initial_regions, keypoints, labels):
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
            if len(curr_x) < old_len:
                curr_dict['region_attributes']['code integrity'] = 'invalid'
            regions.append(curr_dict)
            curr_x, curr_y = [], []

    return regions

def augment(image_path, full_data, output_folder, transform):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_name = image_path.split('/')[-1].split('.')[0]
    
    for full_name, file_data_ in full_data['_via_img_metadata'].items():
        file_data = dict(file_data_)
        if image_name in full_name:
            keypoints, labels = get_points(file_data)

            transformed = transform(image=image, keypoints=keypoints, class_labels=labels)
            transformed_image = transformed['image']
            transformed_keypoints = fix_keypoints(transformed['keypoints'])
            transformed_labels = transformed['class_labels']

            file_data['regions'] = get_regions(file_data['regions'], transformed_keypoints, transformed_labels)

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

    transform = A.Compose([
        A.ISONoise(p=0.5, color_shift=(1, 1), intensity=(0.5, 0.5)),
        A.Perspective(p=0.5, scale=(0.5, 0.5)),
        A.Defocus(p=1, radius=(3, 3)),
        
    ], keypoint_params=A.KeypointParams(format='xy', label_fields=['class_labels']))

    augmented_image_markups_list = []

    for image_name in files_list:
        path_to_image = "/".join([image_folder_path, image_name])

        for _ in range(int(replication_factor)):
            augmented_image_markup = augment(path_to_image, markup_data, output_folder, transform)
            augmented_image_markups_list.append(augmented_image_markup)

    write_results(markup_data, augmented_image_markups_list, 'augmented_markup.json')

if __name__ == '__main__':
    argv = sys.argv
    main(argv[1], argv[2], argv[3])
