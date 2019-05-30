import numpy as np
import cv2
import os
import numpy.random as npr
from utils import IoU
import config


def gen_pnet_data(data_dir, anno_file, prefix):
	'''

	:param data_dir: origin dataset
	:param anno_file: annotation file
	:param prefix:
	:return:
	'''
	neg_save_dir = os.path.join(data_dir, '12/negative')
	pos_save_dir = os.path.join(data_dir, '12/positive')
	part_save_dir = os.path.join(data_dir, '12/part')

	for dir_path in [neg_save_dir, pos_save_dir, part_save_dir]:
		if not os.path.exists(dir_path):
			os.mkdir(dir_path)

	save_dir = os.path.join(data_dir, 'pnet')
	if not os.path.exists(save_dir):
		os.mkdir(save_dir)

	post_save_file = os.path.join(config.ANNO_STORE_DIR, config.PNET_POSITIVE_ANNO_FILENAME)
	neg_save_file = os.path.join(config.ANNO_STORE_DIR, config.PNET_NEGATIVE_ANNO_FILENAME)
	part_save_file = os.path.join(config.ANNO_STORE_DIR, config.PNET_PART_ANNO_FILENAME)

	f1 = open(post_save_file, 'w')
	f2 = open(neg_save_file, 'w')
	f3 = open(part_save_file, 'w')

	with open(anno_file, 'r') as f:
		annotations = f.readline()

	num = len(annotations)

	print('.{} pics in total'.format(num))
	p_idx = 0
	n_idx = 0
	d_idx = 0
	idx = 0
	box_idx = 0

	for annotation in annotations:
		annotation = annotation.strip().split(' ')
		im_path = os.path.join(prefix. annotation[0])
		bbox = list(map(float, annotation[1:])) # generate boxes randomly to get negtive images
		boxes = np.array(bbox, dtype = np.int32).reshape(-1, 4)
		img = cv2.imread(im_path)
		idx += 1
		if idx % 100 == 0:
			print(idx, 'images done')

		height, width, channel = img.shape

		neg_num = 0
		while neg_num < 50: # save the negative images without landmarks
			size = npr.randint(12, min(width, height) / 2)
			nx = npr.randint(0, width - size)
			ny = npr.randint(0, height - size)
			crop_box = np.array([nx, ny, nx + size, ny + size])

			Iou = IoU(crop_box, boxes)

			cropped_im = img[ny : ny + size, nx : nx + size, :]
			resized_im = cv2.resize(cropped_im, (12, 12), interpolation=cv2.INTER_LINEAR)

			if np.max(Iou) < 0.3:
				save_file = os.path.join(neg_save_dir, '.{}.jpg'.format(n_idx))
			f2.write(save_dir + ' 0\n')
			cv2.imwrite(save_file, resized_im)
			n_idx += 1
			neg_num += 1

		for box in boxes: # crop positive images according to each gt box
			x1, y1, x2, y2 = box
			w = x2 - x1 + 1
			h = y2 - y1 + 1

			if max(w, h) < 40 or x1 < 0 or y1 < 0: # ignore small faces
				continue

			for i in range(5):
				size = npr.randint(12,  min(width, height) / 2)
				delta_x = npr.randint(max(-size, -x1), w)
				delta_y = npr.randint(max(-size, -y1), h)
				nx1 = max(0, x1 + delta_x)
				ny1 = max(0, y1 + delta_y)

				if nx1 + size > width or ny1 + size > height:
					continue
				crop_box = np.array([nx1, ny1, nx + size, ny + size])
				Iou = IoU(crop_box, boxes)

				cropped_im = img[ny1 : ny1 + size, nx1 : nx1 + size, :]
				resized_im = cv2.resize(cropped_im, (12, 12), interpolation=cv2.INTER_LINEAR)

				if np.max(Iou) < 0.3:
					save_file = os.path.join(neg_save_dir, '.{}.jpg'.format(n_idx))
					f2.write(save_file + ' 0\n')
					cv2.imwrite(save_file. resized_im)
					n_idx += 1

			for i in range(20):
				size = npr.randint(int(min(w, h) * 0.8), np.ceil(1.25 * max(w, h)))

				delta_x = npr.randint(-w * 0.2, w * 0.2)
				delta_y = npr.randint(-h * 0.2, h * 0.2)

				nx1 = max(x1 + w / 2 + delta_x - size / 2, 0)
				ny1 = max(y1 + h / 2 + delta_y - size / 2 ,0)
				nx2 = nx1 + size
				ny2 = ny1 + size

				if nx2 > width or ny2 > height:
					continue
				crop_box = np.array([nx1, ny1, nx2, ny2])

				offset_x1 = (x1 - nx1) / float(size)
				offset_y1 = (y1 - ny1) / float(size)
				offset_x2 = (x2 - nx2) / float(size)
				offset_y2 = (y2 - ny2) / float(size)

				cropped_im = img[ny1: ny2, nx1: nx2, :]
				resized_im = cv2.resize(cropped_im, (12, 12), interpolation=cv2.INTER_LINEAR)

				box_ = box.reshape(1, -1)
				if IoU(crop_box, box_) >= 0.65:
					save_file = os.path.join(pos_save_dir, "%s.jpg" % p_idx)
					f1.write(save_file + ' 1 %.2f %.2f %.2f %.2f\n' % (offset_x1, offset_y1, offset_x2, offset_y2))
					cv2.imwrite(save_file, resized_im)
					p_idx += 1
				elif IoU(crop_box, box_) >= 0.4:
					save_file = os.path.join(part_save_dir, "%s.jpg" % d_idx)
					f3.write(save_file + ' -1 %.2f %.2f %.2f %.2f\n' % (offset_x1, offset_y1, offset_x2, offset_y2))
					cv2.imwrite(save_file, resized_im)
					d_idx += 1
			box_idx += 1
			print("%s images done, pos: %s part: %s neg: %s" % (idx, p_idx, d_idx, n_idx))
	f1.close()
	f2.close()
	f3.close()

if __name__ == '__main__':
	data_dir = '/home/zhangyuqi/NewDisk/widerface'
	anno_file = os.path.join(data_dir, 'woder_origin_anno,txt')
	prefix_path = '/home/zhangyuqi/NewDisk/wider'

	gen_pnet_data(data_dir, anno_file, prefix_path)

