import glob
import os
import cv2
import random

import numpy as np

from sklearn.model_selection import train_test_split
from matplotlib import pyplot as plt



def parse_json(data):
    array_annotations_v = []
    array_annotations_w = []
    array = []
    data_parse = data.split('}')[:-1]

    for number, d in enumerate(data_parse):
        v = d.split('"v": ')[1]
        d_parse = d.split(', "v":')[0]
        w = d_parse.split(('"w": '))[1]
        array_annotations_v.append(float(v))
        array_annotations_w.append(float(w))
        array.append((float(v), float(w)))
    return array


def get_images(list_images, type_image, image_shape):
    array_imgs = []
    for name in list_images:
        img = cv2.imread(name)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if type_image == 'crop':
            img = img[240:480, 0:640]
        img = cv2.resize(img, (image_shape[0], image_shape[1]))
        array_imgs.append(img)

    return array_imgs


def flip_images(images, array_annotations):
    flipped_images = []
    flipped_annotations = []
    for i, image in enumerate(images):
        flipped_images.append(cv2.flip(image, 1))
        flipped_annotations.append((array_annotations[i][0], -array_annotations[i][1]))
    
    images += flipped_images
    array_annotations += flipped_annotations
    return images, array_annotations


def normalize_annotations(array_annotations):
    array_annotations_v = []
    array_annotations_w = []
    for annotation in array_annotations:
        array_annotations_v.append(annotation[0])
        array_annotations_w.append(annotation[1])
        
    # START NORMALIZE DATA
    array_annotations_v = np.stack(array_annotations_v, axis=0)
    array_annotations_v = array_annotations_v.reshape(-1, 1)

    array_annotations_w = np.stack(array_annotations_w, axis=0)
    array_annotations_w = array_annotations_w.reshape(-1, 1)

    normalized_X = normalize(array_annotations_v)
    normalized_Y = normalize(array_annotations_w)

    normalized_annotations = []
    for i in range(0, len(normalized_X)):
        normalized_annotations.append([normalized_X.item(i), normalized_Y.item(i)])

    return normalized_annotations


def normalize(x):
    x = np.asarray(x)
    return (x - x.min()) / (np.ptp(x))


def separate_sequences(array_imgs, array_annotations):
    separated_array_imgs = []
    separated_array_annotations = []
    
    # SEPARATE DATASET INTO SEQUENCES TO FIT BATCH SIZES
    '''
    Complete dataset:

    3744-3745
    5066-5067
    9720-9721
    10387-10388
    10695-10696
    11283-11284
    11354-11355
    11492-11493
    11980-11981
    12618-12619
    13231-13232
    14107-14108
    15790-15791
    16732-16762
    16795-16796
    16796-17341
    Curves dataset:
    (17341+...)
    3156-3157

    Cut: 
    1. 0-3700 *
    2. 3745-5045 *
    3. 5067-9717 *
    4. 9721-10371 *
    5. 10388-10688 *
    6. 10696-11246 *
    7. 11284-11334 *
    8. 11355-11455 *
    9. 11493-11943 *
    10. 11981-12581 *
    11. 12619-13219 *
    12. 13232-14082 *
    13. 14108-15758 *
    14. 15791-16691 *
    15. 16796-17296 *
    16. 17341-20491 *
    17. 20498-22598 *
    Repeated cuts:
    1. 22609-26309 *
    2. 26354-27654 *
    3. 27676-32326 *
    4. 32330-32960 *
    5. 32997-33297 *
    6. 33305-33855 *
    7. 33893-33943 *
    8. 33964-34064 *
    9. 34102-34552 *
    10. 34590-35190 *
    11. 35228-35828 *
    12. 35841-36691 *
    13. 36717-38367 *
    14. 38400-39300 *
    15. 39405-39905 *
    16. 39950-43100 *
    17. 43107-45207 *
    '''

    sequences_frames = [[0, 3700], [3745, 5045], [5067, 9717], [9721, 10371], [10388, 10688], [10696, 11246], [11284, 11334], [11355, 11455], [11493, 11943],
                       [11981, 12581], [12619, 13219], [13232, 14082], [14108, 15758], [15791, 17291], [17341, 20491], [20498, 22598], [22609, 26309], 
                       [26354, 27654], [27676, 32326], [32330, 32930], [32997, 33297], [33305, 33855], [33893, 33943], [33964, 34064], [34102, 34552], 
                       [34590, 35190], [35228, 35828], [35841, 36691], [36717, 38367], [38400, 39300], [39405, 39905], [39950, 43100], [43107, 45157]]
    
    
    for sequence_frames in sequences_frames:
        array_imgs_sequence = []
        array_anns_sequence = []
        for i in range(sequence_frames[0], sequence_frames[1]):
            array_imgs_sequence.append(array_imgs[i])
            array_anns_sequence.append(array_annotations[i])
            
        separated_array_imgs.append(array_imgs_sequence)
        separated_array_annotations.append(array_anns_sequence)

    return separated_array_imgs, separated_array_annotations
    
    
def split_dataset(array_x, array_y):
    images_train, images_validation, annotations_train, annotations_validation = train_test_split(array_x, array_y, test_size=0.30, random_state=42, shuffle=False)

    # Adapt the data
    images_train = np.stack(images_train, axis=0)
    annotations_train = np.stack(annotations_train, axis=0)
    images_validation = np.stack(images_validation, axis=0)
    annotations_validation = np.stack(annotations_validation, axis=0)
    
    return images_train, annotations_train, images_validation, annotations_validation
    
def add_extreme_cases(array_imgs, array_annotations):
    '''
    Look for extreme 50 frames sequences inside every big-sequence
    '''
    new_array_imgs = []
    new_array_annotations = []
    for x, big_sequence_anns in enumerate(array_annotations):
        new_big_sequence_imgs = []
        new_big_sequence_anns = []
        for y in range(0, int(len(big_sequence_anns)/50)):
            sequences_imgs = array_imgs[x][y*50:(y*50)+50]
            sequences_anns = array_annotations[x][y*50:(y*50)+50]
            new_big_sequence_imgs+=sequences_imgs
            new_big_sequence_anns+=sequences_anns
            for seq in sequences_anns:
                if seq[1] >= 0.7 or seq[1] <= 0.3:
                    if seq[1] >= 0.8 or seq[1] <= 0.2:
                        for i in range(0,2):
                            new_big_sequence_imgs+=sequences_imgs
                            new_big_sequence_anns+=sequences_anns
                    else:
                        for i in range(0,1):
                            new_big_sequence_imgs+=sequences_imgs
                            new_big_sequence_anns+=sequences_anns
                if seq[0] <= 0.2:
                    for i in range(0,1):
                        new_big_sequence_imgs+=sequences_imgs
                        new_big_sequence_anns+=sequences_anns
        new_array_imgs.append(new_big_sequence_imgs)
        new_array_annotations.append(new_big_sequence_anns)


    shown_array_imgs = []
    shown_array_annotations = []
    random_sort = random.sample(range(0, 33), 33)

    for numb in random_sort:
        shown_array_imgs += new_array_imgs[numb]
        shown_array_annotations += new_array_annotations[numb]

    array_imgs = shown_array_imgs
    array_annotations = shown_array_annotations
    
    return array_imgs, array_annotations

def read_dataset(path_to_data, type_image, image_shape, data_type):
    print('---- Complete ----')
    complete_name_file = path_to_data + '/complete_dataset/data.json'
    complete_file = open(complete_name_file, 'r')
    data_complete = complete_file.read()
    complete_file.close()

    array_annotations_complete = []
    DIR_complete_images = path_to_data + '/complete_dataset/Images/'
    list_images_complete = glob.glob(DIR_complete_images + '*')
    
    images_paths_complete = sorted(list_images_complete, key=lambda x: int(x.split('/')[7].split('.png')[0]))
    array_annotations_complete = parse_json(data_complete)

    images_complete = get_images(images_paths_complete, type_image, image_shape)
    images_complete, array_annotations_complete = flip_images(images_complete, array_annotations_complete)

    array_annotations_complete = normalize_annotations(array_annotations_complete)

    print('---- Curves ----')
    curves_name_file = path_to_data + '/curves_only/data.json'
    file_curves = open(curves_name_file, 'r')
    data_curves = file_curves.read()
    file_curves.close()

    DIR_curves_images = path_to_data + '/curves_only/Images/'
    list_images_curves = glob.glob(DIR_curves_images + '*')
    images_paths_curves = sorted(list_images_curves, key=lambda x: int(x.split('/')[7].split('.png')[0]))
    array_annotations_curves = parse_json(data_curves)

    images_curves = get_images(images_paths_curves, type_image, image_shape)
    images_curves, array_annotations_curves = flip_images(images_curves, array_annotations_curves)

    array_annotations_curves = normalize_annotations(array_annotations_curves)
    
    array_imgs = images_complete + images_curves
    array_annotations = array_annotations_complete + array_annotations_curves
    
    separated_array_imgs, separated_array_annotations = separate_sequences(array_imgs, array_annotations)
    if data_type == 'extreme':
        array_imgs, array_annotations = add_extreme_cases(separated_array_imgs, separated_array_annotations)
    images_train, array_annotations_train, images_val, array_annotations_val = split_dataset(array_imgs, array_annotations)

    return images_train, array_annotations_train, images_val, array_annotations_val