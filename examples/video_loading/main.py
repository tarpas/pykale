import os
import sys
# No need if pykale is installed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kale.loaddata.videos import  VideoFrameDataset
from kale.prepdata.video_transform import ImglistToTensor
from torchvision import transforms
import torch
import matplotlib.pyplot as plt
from torchvision.datasets.utils import download_file_from_google_drive, extract_archive

"""
Viewer, ignore this function for now and look at "main" below.
"""
def download_dummy_dataset():
    # Full File URL: https://drive.google.com/file/d/1aIcmhaHZ9yflqwQZOSmW7ho6FDqVVAyp/view
    gdrive_file_id = '1aIcmhaHZ9yflqwQZOSmW7ho6FDqVVAyp'
    output_directory = os.path.join(os.getcwd())
    output_file_name = 'demo_dataset.zip'

    print("Downloading Dummy Dataset")
    download_file_from_google_drive(gdrive_file_id, output_directory, output_file_name)

    if os.path.exists(os.path.join(os.getcwd(), 'demo_dataset')):
        print("Skipping Download and Extraction")
        return

    print("Extracting Dummy Dataset")
    zip_file = os.path.join(os.getcwd(), 'demo_dataset.zip')
    extract_archive(zip_file)

if __name__ == '__main__':
    """
    This demo uses the dummy dataset inside of the folder "demo_dataset".
    It is structured just like a real dataset would need to be structured.
    """
    download_dummy_dataset()

    videos_root = os.path.join(os.getcwd(), 'demo_dataset')
    annotation_file = os.path.join(videos_root, 'annotations.txt')

    """ DEMO 1 WITHOUT IMAGE TRANSFORMS """
    dataset = VideoFrameDataset(
        root_path=videos_root,
        annotationfile_path=annotation_file,
        num_segments=5,
        frames_per_segment=1,
        imagefile_template='img_{:05d}.jpg',
        transform=None,
        random_shift=True,
        test_mode=False
    )

    sample = dataset[0]
    frames = sample[0]  # list of PIL images
    label = sample[1]   # integer label

    for image in frames:
        plt.imshow(image)
        plt.title(label)
        plt.show()
        plt.pause(1)


    """ DEMO 2 WITH TRANSFORMS """
    # As of torchvision 0.8.0, torchvision transforms support batches of images
    # of size (BATCH x CHANNELS x HEIGHT x WIDTH) and apply deterministic or random
    # transformations on the batch identically on all images of the batch. Any torchvision
    # transform for image augmentation can thus also be used  for video augmentation.
    preprocess = transforms.Compose([
        ImglistToTensor(),  # list of PIL images to (FRAMES x CHANNELS x HEIGHT x WIDTH) tensor
        transforms.Resize(299),  # resize smaller edge of frames to 299
        transforms.CenterCrop(299),  # center crop frames to square 299x299
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    dataset = VideoFrameDataset(
        root_path=videos_root,
        annotationfile_path=annotation_file,
        num_segments=5,
        frames_per_segment=1,
        imagefile_template='img_{:05d}.jpg',
        transform=preprocess,
        random_shift=True,
        test_mode=False
    )

    sample = dataset[1]
    # tensor of shape (NUM_SEGMENTS*FRAMES_PER_SEGMENT) x CHANNELS x HEIGHT x WIDTH
    frame_tensor = sample[0]
    print('Video Tensor Size:', frame_tensor.size())
    # integer label
    label = sample[1]

    
    """
    Denormalize is just for visualization purposes, to undo the transforms applied
    to the list of frames of a video.
    """
    def denormalize(video_tensor):
        """
        Undoes mean/standard deviation normalization, zero to one scaling,
        and channel rearrangement for a batch of images.
        args:
            video_tensor: a (FRAMES x CHANNELS x HEIGHT x WIDTH) tensor
        """
        inverse_normalize = transforms.Normalize(
            mean=[-0.485 / 0.229, -0.456 / 0.224, -0.406 / 0.225],
            std=[1 / 0.229, 1 / 0.224, 1 / 0.225]
        )
        return (inverse_normalize(video_tensor) * 255.).type(torch.uint8).permute(0, 2, 3, 1).numpy()


    frame_tensor = denormalize(frame_tensor)
    for image in frame_tensor:
        plt.imshow(image)
        plt.title(label)
        plt.show()
        plt.pause(1)


    """ DEMO 2 CONTINUED: DATALOADER """
    dataloader = torch.utils.data.DataLoader(
        dataset=dataset,
        batch_size=2,
        shuffle=True,
        num_workers=8,
        pin_memory=True
    )

    for epoch in range(10):
        for video_batch, labels in dataloader:
            """
            Insert Training Code Here
            """
            print("Video Batch Tensor Size:", video_batch.size())
            print("Labels Size:", labels.size())
            break
        break