from numpy.core.shape_base import stack
from torch.utils.data.dataset import Dataset
from torchvision import transforms
from PIL import Image
from utils.processing import *

class DeepPilotDataset(Dataset):
    def __init__(self, path_to_data, transforms=None, preprocessing=None, mode='train'):

        self.data_path = path_to_data

        self.images = []
        self.labels = []
        type_image = []

        if preprocessing is not None:
            if 'nocrop' in preprocessing:
                pass
            else:
                type_image.append('cropped')
            
            if 'extreme' in preprocessing:
                data_type = 'extreme'
            else:
                data_type = None

            if 'stacked' in preprocessing:
                type_image.append('stacked')
        else:
            type_image = ['cropped']
            data_type = None

        for path in path_to_data:
            datatset = getTrainSource(path, type_image)
            self.images += datatset.images
            self.labels += datatset.speed

        self.labels, self.images = preprocess_data(self.labels, self.images, data_type)

        self.transforms = transforms

        self.image_shape = self.images[0].shape
        self.num_labels = np.array(self.labels[0]).shape[0]

        self.count = len(self.images)
        
    def __getitem__(self, index):

        img = self.images[index]
        label = np.array(self.labels[index])
        data = Image.fromarray(img)

        if self.transforms is not None:
            data = self.transforms(data)

        return (data, label)

    def __len__(self):
        return self.count