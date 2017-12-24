#!/usr/bin/env python
import os
import sys
import argparse
import yaml

import matplotlib.pyplot as plt
import numpy as np
import cv2

import plot_utils as plu


class DatasetHandler():
    """
    The DatasetHandler provides basic methods to translate the different dataset ground truth data into
    one common format which can be used to train the TL model.

    The Bosch statistics and read all labels scripcs are inspired by the original Bosch GitHub repository:

        https://github.com/bosch-ros-pkg/bstld

    Usage: DatasetHandler.py [-h] [--bosch_label_file YAML_file] [-s] [-sp] [-si]

        -h                    Print help
        --bosch_label_file    Path to Bosch dataset label YAML file.
        -s, --statistics      Show dataset statistics line, mnumber images, image size, histograms.
        -sp, --safe_plots     If set, safe all plots as PNG files in the actual directory. In combination with -s
        -si, --show_images    Show all dataset images with colored labels.
    """

    bosch_label_dict_valid = False           # True if Bosch dataset has been read.
    bosch_label_dict = {}                    # dictionary with Bosch label data
    bosch_label_statistics = {}              # dictionary of type <TL class> : <number of labeled TL class>
    bosch_number_images = 0                  # number of images in Bosch dataset
    bosch_number_labeled_traffic_lights = 0  # number of traffic light in the Bosch dataset
    bosch_image_shape = (0, 0, 0)            # image shape [height, width, channels] of bosch dataset

    def read_all_bosch_labels(self, input_yaml, riib=False):
        """
        Gets all labels from the Bosch Small Traffic Light Dataset listed in the label file.

        Image Formats:
          - RIIB 12 bit (red-clear-clear-blue), size = 1280x736
          - RGB 8bit (red-green-blue), size = 1280x720, Reconstructed color images.

        The RGB images are provided for debugging and can also be used for training. However, the RGB conversion
        process has some drawbacks. Some of the converted images may contain artifacts and the color distribution
        may seem unusual.

        :param input_yaml: Path to yaml file.
        :param riib:       If True, change path to labeled pictures.

        :return: images:   Labels for traffic lights. None in case the input file couldn't be found.
        """
        if not os.path.exists(input_yaml):
            return None

        images = yaml.load(open(input_yaml, 'rb').read())
        self.bosch_number_images = len(images)

        for i in range(self.bosch_number_images):
            images[i]['path'] = os.path.abspath(os.path.join(os.path.dirname(input_yaml), images[i]['path']))

            if riib:
                images[i]['path'] = images[i]['path'].replace('.png', '.pgm')
                images[i]['path'] = images[i]['path'].replace('rgb/train', 'riib/train')
                images[i]['path'] = images[i]['path'].replace('rgb/test', 'riib/test')

                for box in images[i]['boxes']:
                    box['y_max'] = box['y_max'] + 8
                    box['y_min'] = box['y_min'] + 8

            # generate label statistics
            self.bosch_number_labeled_traffic_lights += len(images[i]['boxes'])

            for box in images[i]['boxes']:
                if box['label'] not in self.bosch_label_statistics.keys():
                    self.bosch_label_statistics[box['label']] = 1
                else:
                    self.bosch_label_statistics[box['label']] = self.bosch_label_statistics[box['label']] + 1

        self.bosch_label_dict = images

        # determine image size
        image = cv2.imread(self.bosch_label_dict[0]['path'])
        self.bosch_image_shape = image.shape
        self.bosch_label_dict_valid = True

        return images

    def print_bosch_statistics(self):
        """ Plots basic dataset statistics like number of images, labes, etc. """

        if not self.bosch_label_dict_valid:
            print('ERROR: No valid dataset dictionary. Read Bosch dataset before.')
            return

        print()
        print(' Bosch Small Traffic Light Dataset')
        print('--------------------------------------------------')
        print('Number images:        {}'.format(self.bosch_number_images))
        print('Number traffic light: {}'.format(self.bosch_number_labeled_traffic_lights))
        print('Image shape:          {}x{}x{}'.format(self.bosch_image_shape[1],
                                                      self.bosch_image_shape[0],
                                                      self.bosch_image_shape[2]))

    def plot_bosch_label_histogram(self, safe_figure=False):
        """ Plots a histogram over all Bosch labels which have been read by the `read_all_bosch_labels()` method.

        :param safe_figure:  If true safe figure as png file.
        """

        if not self.bosch_label_dict_valid:
            print('ERROR: No valid dataset dictionary. Read Bosch dataset before.')
            return

        x = np.arange(len(self.bosch_label_statistics))
        label_names = np.array([], dtype=np.str)
        label_hist = np.array([])
        colors = []

        print()
        print(' Label Class Distribution')
        print('--------------------------------------------------')

        for key in sorted(self.bosch_label_statistics.keys()):
            print('{:18s} = {}'.format(key, self.bosch_label_statistics[key]))
            label_names = np.append(label_names, key)
            label_hist = np.append(label_hist, self.bosch_label_statistics[key])

            # set bar color depending on label class
            if str(key).lower().find('red') >= 0:
                colors.append(plu.COLOR_RED)
            elif str(key).lower().find('yellow') >= 0:
                colors.append(plu.COLOR_YELLOW)
            elif str(key).lower().find('green') >= 0:
                colors.append(plu.COLOR_GREEN)
            else:
                colors.append(plu.COLOR_GREY)

        # plot label histogram
        fig, ax = plt.subplots()
        fig.subplots_adjust(left=0.27, right=0.97, bottom=0.1, top=0.9)
        rect = plt.barh(x, label_hist, color=colors)
        plu.autolabel_barh(rect, ax)
        plt.yticks(x, label_names)
        plt.title('Label Distribution in Bosch Small Traffic Light Dataset')
        plt.ylabel('label class')
        plt.xlabel('number of labels per class')
        ax.set_axisbelow(True)
        #ax.minorticks_on()
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='grey')
        #ax.grid(which='minor', linestyle=':', linewidth='0.5', color='grey')

        if safe_figure:
            plt.savefig('bosch_label_histogram.png')

        plt.show(block=False)

    def plot_bosch_label_heatmap(self, safe_figure=False):
        """ Plots a heatmap over all Bosch label positions.

        :param safe_figure: If true safe figure as png file.
        """

        if not self.bosch_label_dict_valid:
            print('ERROR: No valid dataset dictionary. Read Bosch dataset before.')
            return

        heatmap_red = np.zeros((self.bosch_image_shape[0], self.bosch_image_shape[1]), dtype=np.float)
        heatmap_yellow = np.zeros((self.bosch_image_shape[0], self.bosch_image_shape[1]), dtype=np.float)
        heatmap_green = np.zeros((self.bosch_image_shape[0], self.bosch_image_shape[1]), dtype=np.float)
        heatmap_off = np.zeros((self.bosch_image_shape[0], self.bosch_image_shape[1]), dtype=np.float)

        for i in range(self.bosch_number_images):
            for box in self.bosch_label_dict[i]['boxes']:
                # set bar color depending on label class
                if box['label'].lower().find('red') >= 0 and len(box['label']) == len('red'):
                    heatmap_red[int(round(box['y_min'])):int(round(box['y_max'])), int(round(box['x_min'])):int(round(box['x_max']))] += 1
                elif box['label'].lower().find('yellow') >= 0 and len(box['label']) == len('yellow'):
                    heatmap_yellow[int(round(box['y_min'])):int(round(box['y_max'])), int(round(box['x_min'])):int(round(box['x_max']))] += 1
                elif box['label'].lower().find('green') >= 0 and len(box['label']) == len('green'):
                    heatmap_green[int(round(box['y_min'])):int(round(box['y_max'])), int(round(box['x_min'])):int(round(box['x_max']))] += 1
                elif box['label'].lower().find('off') >= 0 and len(box['label']) == len('off'):
                    heatmap_off[int(round(box['y_min'])):int(round(box['y_max'])), int(round(box['x_min'])):int(round(box['x_max']))] += 1

        heatmap_all = heatmap_red + heatmap_yellow + heatmap_green + heatmap_off

        # plot label histogram
        fig, ax = plt.subplots()
        fig.subplots_adjust(left=0.1, right=0.97, bottom=0.1, top=0.9)
        fig.suptitle('Label Heatmap of Bosch Small Traffic Light Dataset')
        ax.imshow(heatmap_all, cmap='jet', interpolation='nearest')
        ax.set_title('Red, Green, Red, Off TL')

        if safe_figure:
            plt.savefig('bosch_label_heatmap_all.png')

        fig, axarr = plt.subplots(2, 2)
        fig.subplots_adjust(left=0.1, right=0.97, bottom=0.1, top=0.9)
        fig.suptitle('Label Heatmap of Bosch Small Traffic Light Dataset')

        axarr[0, 0].imshow(heatmap_red, cmap='Reds', interpolation='nearest')
        axarr[0, 0].set_title('Red TL')

        axarr[0, 1].imshow(heatmap_yellow, cmap='Oranges', interpolation='nearest')
        axarr[0, 1].set_title('Yellow TL')

        axarr[1, 0].imshow(heatmap_green, cmap='Greens', interpolation='nearest')
        axarr[1, 0].set_title('Green TL')

        axarr[1, 1].imshow(heatmap_off, cmap='Greys', interpolation='nearest')
        axarr[1, 1].set_title('Off TL')

        if safe_figure:
            plt.savefig('bosch_label_heatmap_red_yellow_green_off.png')

        plt.show(block=False)

    def show_bosch_labeled_images(self, output_folder=None):
        """
        Shows all images with colored labeled traffic lights.

        :param output_folder: If None, do not save picture. Else enter path to folder
        """
        images = self.bosch_label_dict

        if output_folder is not None:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

        for i, image_dict in enumerate(images):
            image = cv2.imread(image_dict['path'])
            if image is None:
                raise IOError('Could not open image path', image_dict['path'])

            for box in image_dict['boxes']:
                color = (100, 100, 100)

                if box['label'].lower().find('red') >= 0:
                    color = (0, 0, 255)
                elif box['label'].lower().find('yellow') >= 0:
                    color = (0, 255, 255)
                elif box['label'].lower().find('green') >= 0:
                    color = (0, 255, 0)

                cv2.rectangle(image,
                              (int(round(box['x_min'])), int(round(box['y_min']))),
                              (int(round(box['x_max'])), int(round(box['y_max']))),
                              color)

            cv2.imshow('labeled_image', image)
            cv2.waitKey(200)

            if output_folder is not None:
                cv2.imwrite(os.path.join(output_folder, str(i).zfill(10) + '_'
                                         + os.path.basename(image_dict['path'])), image)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dataset handler provides statistics and label transformation.')

    parser.add_argument(
        '--bosch_label_file',
        help='Path to the Bosch label YAML file.',
        dest='bosch_label_file',
        metavar='YAML_file'
    )

    parser.add_argument(
        '-s', '--statistics',
        help='Show dataset statistics like label distribution.',
        action='store_true',
        default=False,
        dest='statistics'
    )

    parser.add_argument(
        '-sp', '--safe_plots',
        help='Safe plots as PNG files.',
        action='store_true',
        default=False,
        dest='safe_plots'
    )

    parser.add_argument(
        '-si', '--show_images',
        help='Show all labeled images in the dataset.',
        action='store_true',
        default=False,
        dest='show_images'
    )

    args = parser.parse_args()

    if len(sys.argv) < 4:
        # no arguments found
        parser.print_usage()
        parser.exit(-1)

    safe_plots = False

    if args.bosch_label_file:
        print('Loading Bosch dataset...', end='', flush=True)
        dataset_handler = DatasetHandler()

        if dataset_handler.read_all_bosch_labels(args.bosch_label_file) == None:
            print('')
            print('ERROR: Input YAML file "{}" not found.'.format(args.bosch_label_file))
            exit(-1)
        else:
            print('done')

        if args.statistics:
            # print/plot dataset statistics
            dataset_handler.print_bosch_statistics()
            dataset_handler.plot_bosch_label_histogram(safe_figure=args.safe_plots)
            dataset_handler.plot_bosch_label_heatmap(safe_figure=args.safe_plots)
            plt.show()
        elif args.show_images:
            # show all images with colored labels
            print('Exit with CTRL+C')
            dataset_handler.show_bosch_labeled_images()
