import xml.etree.ElementTree as ET
from pathlib import Path
import os,sys
import numpy as np
import random
from sklearn.model_selection import train_test_split

def parse_annotation(ann_dir, img_dir, labels=[]):
    all_imgs = []
    gezicht_list = []
    kenteken_list = []
    achtergrond_list = []
    seen_labels = {}
    
    for ann in sorted(os.listdir(ann_dir)):
        if ann.endswith('xml'):
            print(os.path.join(ann_dir,ann))
            img = {'object':[]}
    
            tree = ET.parse(os.path.join(ann_dir,ann))
#            print(tree)
            for elem in tree.iter():
                if 'filename' in elem.tag:
                    img['filename'] = img_dir + elem.text
                if 'width' in elem.tag:
                    img['width'] = int(elem.text)
                if 'height' in elem.tag:
                    img['height'] = int(elem.text)
                if 'object' in elem.tag or 'part' in elem.tag:
                    obj = {}
    
                    for attr in list(elem):
                        if 'name' in attr.tag:
                            obj['name'] = attr.text
                            plaatje = obj['name']
                            print(plaatje.replace('-','_')) 
#labels = ['gezicht', 'kenteken', 'achtergrond']
                            if plaatje == 'gezicht':
                                gezicht_list = np.append(gezicht_list,ann) 
                            if plaatje == 'kenteken':
                                kenteken_list = np.append(kenteken_list,ann) 
                            if plaatje == 'achtergrond':
                               achtergrond_list = np.append(achtergrond_list,ann) 
                            if obj['name'] in seen_labels:
                                seen_labels[obj['name']] += 1
                            else:
                                seen_labels[obj['name']] = 1
    
                            if len(labels) > 0 and obj['name'] not in labels:
                                break
                            else:
                                img['object'] += [obj]
    
                        if 'bndbox' in attr.tag:
                            for dim in list(attr):
                                if 'xmin' in dim.tag:
                                    obj['xmin'] = int(round(float(dim.text)))
                                if 'ymin' in dim.tag:
                                    obj['ymin'] = int(round(float(dim.text)))
                                if 'xmax' in dim.tag:
                                    obj['xmax'] = int(round(float(dim.text)))
                                if 'ymax' in dim.tag:
                                    obj['ymax'] = int(round(float(dim.text)))
    
            if len(img['object']) > 0:
                all_imgs += [img]

    return all_imgs, seen_labels, gezicht_list, kenteken_list, achtergrond_list

#inputpath = Path('images')
annotation_dir = inputpath / 'valid_annot'
image_dir = inputpath / 'valid_img'
labels = ['gezicht', 'kenteken', 'achtergrond']

outputpath = Path('/flashblade/lars_data/2018_Cyclomedia_panoramas/project_folder/YOLO/borden_train_balanced')
train_annot_dir = outputpath / 'annot'
train_img_dir = outputpath / 'img'
test_annot_dir = outputpath / 'valid_annot'
test_img_dir = outputpath / 'valid_img'

all_imgs, seen_labels, gezicht_list, kenteken_list, achtergrond_list = parse_annotation(str(annotation_dir),str(image_dir),labels)

#print(all_imgs)
print(seen_labels)
sys.exit()

print('gezicht', len(gezicht_list), 'achtergrond', len(achtergrond_list), 'kenteken', len(kenteken_list))

def length(x):
    return len(x)

variable_list = ['gezicht_list', 'achtergrond_list', 'kenteken_list']

# Split the lists in test and train
split = 0.2
split = 0.2
gezicht_train, gezicht_test = train_test_split(gezicht_list, test_size=split,random_state=42)
kenteken_train, kenteken_test = train_test_split(kenteken_list, test_size=split,random_state=42)
achtergrond_train, achtergrond_test = train_test_split(achtergrond_list, test_size=split,random_state=42)

# Remove signs from the set that also occur in the train set
all_train = np.concatenate((gezicht_train, kenteken_train, achtergrond_train))

var_list = [gezicht_test, kenteken_test, achtergrond_test]
def remove_train_from_test(test,train):
    keep = []
    for i in np.arange(len(test)):
        if test[i] in train:
            pass
        else:
            keep = np.append(keep,test[i])
    return keep
gezicht_test, kenteken_test, achtergrond_test = (remove_train_from_test(var,all_train) for var in var_list)

all_test = np.concatenate((gezicht_test, kenteken_test, achtergrond_test))

# Check if there are any duplicates remaining
i=0
for file in all_test:
    if file in all_train:
        print(file)
        i = i+1
print(i)

### Train
# Find longest dataset
max_length = max(len(gezicht_train),len(kenteken_train),len(achtergrond_train))
print(max_length)

# Add random signs to the datasets to get them to equal length
var_list = [gezicht_train, kenteken_train, achtergrond_train]

def add_random_files(var,max_length):
    print(len(var),'before')
    nr_to_add = max_length - len(var)
    to_add = []
    for i in np.arange(nr_to_add):
        print(i)
        to_add = np.append(to_add,random.choice(var))
    var = np.append(var,to_add)
    print(var,len(var),'after')
    return var


gezicht_train, kenteken_train, achtergrond_train = (add_random_files(var,max_length) for var in var_list)
var_list = [gezicht_train, kenteken_train, achtergrond_train]

print(gezicht_train)
min_length = min(len(gezicht_train),len(kenteken_train),len(achtergrond_train))
print(min_length)

for var in var_list:
    for file in var:
        print(file)
        if os.path.isfile(str(train_img_dir / file.replace('xml','jpg'))) == False:
            command = 'ln %s %s' %(str(image_dir / file.replace('xml','jpg')), str(train_img_dir / file.replace('xml','jpg')))
            os.system(command)
        prefix = 0
        i=False
        while i == False:
            filename = str(prefix) + '_' + file
            if os.path.isfile(str(train_annot_dir / filename)):
                prefix = prefix+1
            else:
                command = 'ln %s %s' %(str(annotation_dir / file), str(train_annot_dir / filename))
                os.system(command)
                i=True
### TEST
# Find longest dataset
max_length = max(len(gezicht_test),len(kenteken_test),len(achtergrond_test))
print(max_lengt

# Add random signs to the datasets to get them to equal length
var_list = [gezicht_test, kenteken_test, achtergrond_test]

def add_random_files(var,max_length):
    print(len(var),'before')
    nr_to_add = max_length - len(var)
    to_add = []
    for i in np.arange(nr_to_add):
        print(i)
        to_add = np.append(to_add,random.choice(var))
    var = np.append(var,to_add)
    print(var,len(var),'after')
    return var


gezicht_test, kenteken_test, achtergrond_test = (add_random_files(var,max_length) for var in var_list)
var_list = [gezicht_test, kenteken_test, achtergrond_test]

print(gezicht_test)
min_length = min(len(gezicht_test),len(kenteken_test),len(achtergrond_test))
print(min_length)

for var in var_list:
    for file in var:
        print(file)
        if os.path.isfile(str(test_img_dir / file.replace('xml','jpg'))) == False:
            command = 'ln %s %s' %(str(image_dir / file.replace('xml','jpg')), str(test_img_dir / file.replace('xml','jpg')))
            os.system(command)
        prefix = 0
        i=False
        while i == False:
            filename = str(prefix) + '_' + file
            if os.path.isfile(str(test_annot_dir / filename)):
                prefix = prefix+1
            else:
                command = 'ln %s %s' %(str(annotation_dir / file), str(test_annot_dir / filename))
                os.system(command)
                i=True
