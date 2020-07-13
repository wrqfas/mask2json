'''
@lanhuage: python
@Descripttion: 
@version: beta
@Author: xiaoshuyui
@Date: 2020-06-12 09:44:19
@LastEditors: xiaoshuyui
@LastEditTime: 2020-07-13 14:23:49
'''
import cv2
import numpy as np
import skimage.io as io
import yaml
import copy
from .getShape import *
from .img2base64 import imgEncode
import os,json
from . import rmQ
import warnings
from .img2xml.processor_multiObj  import img2xml_multiobj

def readYmal(filepath,labeledImg=None):
    if os.path.exists(filepath):
        f = open(filepath)
        y = yaml.load(f)
        f.close()
        # print(y)
        tmp = y['label_names']
        objs = zip(tmp.keys(),tmp.values())
        return sorted(objs)
    elif labeledImg  is not  None:
        """
        should make sure your label is correct!!!

        untested!!!
        """
        labeledImg = np.array(labeledImg,dtype=np.uint8)

        labeledImg[labeledImg>127] = 255
        labeledImg[labeledImg!=255] = 0
        # labeledImg = labeledImg/255

        # _, labels = cv2.connectedComponents(labeledImg)
        _, labels, stats, centroids = cv2.connectedComponentsWithStats(labeledImg)

        labels = np.max(labels)
        labels = [x for x in range(1,labels)]
  



        # labels = labeledImg.ravel()[np.flatnonzero(labeledImg)]

        classes = []
        for i in range(0,len(labels)):
            classes.append("class{}".format(i))
        
        return zip(classes,labels)
    else:
        raise FileExistsError('file not found')



def getMultiObjs_voc(oriImgPath,labelPath,savePath):
    # pass
    labelImg = io.imread(labelPath)
    fileName = labelPath.split(os.sep)[-1]
    imgShape = labelImg.shape
    imgHeight = imgShape[0]
    imgWidth = imgShape[1]
    imgPath = oriImgPath
    warnings.WarningMessage("auto detecting class numbers")
    if len(imgShape) == 3:
        labelImg = labelImg[:,:,0]
    labelImg[labelImg>0] = 255
    # if classFile!='' and os.path.exists(classFile):
    #     with open(classFile,'r') as f:
    #         objs = list(f.readlines())
    # else:
    #     warnings.WarningMessage("auto detected class numbers")
    _,labels,stats,centroids = cv2.connectedComponentsWithStats(labelImg)

    statsShape = stats.shape
    objs = []
    for i in range(1,statsShape[0]):
        st = stats[i,:]

        width = st[2]
        height = st[3]

        xmin = st[0]
        ymin = st[1]
        
        xmax = xmin+width
        ymax = ymin+height

        ob = {}
        ob['name'] = 'class{}'.format(i)
        ob['difficult'] = 0
        # ob['name'] = 'weld'

        bndbox = {}

        bndbox['xmin'] = xmin
        bndbox['ymin'] = ymin
        bndbox['xmax'] = xmax
        bndbox['ymax'] = ymax

        ob['bndbox'] = bndbox
        objs.append(ob)
    saveXmlPath = savePath+os.sep + fileName + '.xml' 
    img2xml_multiobj(saveXmlPath,saveXmlPath,"TEST",fileName,imgPath,imgWidth,imgHeight,objs)



        

    

    



        




def test():
    """
    do not use cv2.imread to load the label img. there is a bug
    """
    # oriImgPath = 'D:\\testALg\\mask2json\\mask2json\\static\\multi_objs_sameclass.jpg'
    # label_img = io.imread('D:\\testALg\\mask2json\\mask2json\\multi_objs_sameclass_json\\label.png')

    oriImgPath = 'D:\\testALg\\mask2json\\mask2json\\static\\multi_objs.jpg'
    label_img = io.imread('D:\\testALg\\mask2json\\mask2json\\multi_objs_json\\label.png')

    labelShape = label_img.shape
    
    labels = readYmal('D:\\testALg\\mask2json\\mask2json\\multi_objs_json\\info.yaml')
    shapes = []
    obj = dict()
    obj['version'] = '4.2.9'
    obj['flags'] = {}
    for la in labels:
        if la[1]>0:
            # img = label_img[label_img == i[1]]
            img = copy.deepcopy(label_img)
            
            img[img == la[1]] = 255
            img[img!=255] = 0

            region = process(img.astype(np.uint8)) 

            """
            this if...else... is unnecessary if using getShape.getMultiRegion 
            """
            if isinstance(region,np.ndarray):
                points = []
                for i in range(0,region.shape[0]):
                    # print(region[i][0])
                    points.append(region[i][0].tolist())
                shape = dict()
                shape['label'] = la[0]
                shape['points'] = points
                shape['group_id'] = 'null'
                shape['shape_type']='polygon'
                shape['flags']={}
                shapes.append(shape)

            elif isinstance(region,list):
                for subregion in region:
                    points = []
                    for i in range(0,subregion.shape[0]):
                        # print(region[i][0])
                        points.append(subregion[i][0].tolist())
                    shape = dict()
                    shape['label'] = la[0]
                    shape['points'] = points
                    shape['group_id'] = 'null'
                    shape['shape_type']='polygon'
                    shape['flags']={}
                    shapes.append(shape)


    
    obj['shapes'] = shapes
    obj['imagePath'] = oriImgPath.split(os.sep)[-1]
    obj['imageData'] = str(imgEncode(oriImgPath))

    obj['imageHeight'] = labelShape[0]
    obj['imageWidth'] = labelShape[1]

    j = json.dumps(obj,sort_keys=True, indent=4)

    with open('D:\\testALg\\mask2json\\mask2json\\static\\multi_objs.json','w') as f:
        f.write(j)

    
    rmQ.rm('D:\\testALg\\mask2json\\mask2json\\static\\multi_objs.json')


def getMultiShapes(oriImgPath,labelPath,savePath,labelYamlPath=''):
    """
    oriImgPath : for change img to base64  \n
    labelPath : after fcn/unet or other machine learning objects outlining , the generated label img
                or labelme labeled imgs(after json files converted to mask files)  \n
    savePath : json file save path  \n
    labelYamlPath : after json files converted to mask files. if doesn't have this file,should have a labeled img.
                    but the classes should change by yourself(labelme 4.2.9 has a bug,when change the label there will be an error.
                    )   \n

    """
    label_img = io.imread(labelPath)

    if np.max(label_img)>127:
        print('too many classes! \n maybe binary?')
        label_img[label_img>127] = 255
        label_img[label_img!=255] = 0
        label_img = label_img/255

    labelShape = label_img.shape
    
    labels = readYmal(labelYamlPath,label_img)
    shapes = []
    obj = dict()
    obj['version'] = '4.2.9'
    obj['flags'] = {}
    for la in labels:
        if la[1]>0:
            # img = label_img[label_img == i[1]]
            img = copy.deepcopy(label_img)
            
            img[img == la[1]] = 255
            img[img!=255] = 0

            region = process(img.astype(np.uint8))
           
            if isinstance(region,np.ndarray):
                points = []
                for i in range(0,region.shape[0]):
                    # print(region[i][0])
                    points.append(region[i][0].tolist())
                shape = dict()
                shape['label'] = la[0]
                shape['points'] = points
                shape['group_id'] = 'null'
                shape['shape_type']='polygon'
                shape['flags']={}
                shapes.append(shape)

            elif isinstance(region,list):
                for subregion in region:
                    points = []
                    for i in range(0,subregion.shape[0]):
                        # print(region[i][0])
                        points.append(subregion[i][0].tolist())
                    shape = dict()
                    shape['label'] = la[0]
                    shape['points'] = points
                    shape['group_id'] = 'null'
                    shape['shape_type']='polygon'
                    shape['flags']={}
                    shapes.append(shape)
    
    obj['shapes'] = shapes
    obj['imagePath'] = oriImgPath.split(os.sep)[-1]
    obj['imageData'] = str(imgEncode(oriImgPath))

    obj['imageHeight'] = labelShape[0]
    obj['imageWidth'] = labelShape[1]

    j = json.dumps(obj,sort_keys=True, indent=4)
    saveJsonPath = savePath+os.sep + obj['imagePath'][:-4] + '.json'
    with open(saveJsonPath,'w') as f:
        f.write(j)

    
    rmQ.rm(saveJsonPath)

    



            
            


if __name__ == "__main__":
    test()