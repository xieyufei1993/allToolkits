# -*- coding:utf-8 -*-
import os
import sys
import json
import time
import random
from lxml import etree
import  gen_imagesets
import image_helper
import xml_helper
import labelxJson_helper
import utils
import cv2


def process_labelx_jsonFile_Fun(json_file_absolutePath=None, tempSaveDir=None, vocpath=None,renamePrefix=None):
    # 下载 对应的image,保存下载的图片到 vocpath+'/JPEGImages'
    image_helper.downloadImage_By_urllist(labelxjson=json_file_absolutePath, tempSaveDir=tempSaveDir, vocpath=vocpath)
    # 将 labelx 标注的数据 转换 pascal voc xml 文件
    # 对待下载失败的图片，添加处理方式
    xml_helper.convertLabelxJsonListToXmlFile(
        jsonlistFile=json_file_absolutePath, datasetBasePath=vocpath)
    # rename imame and xml file
    filePrefix = renamePrefix
    if not filePrefix: # 没有设置 rename prefix 的情况下
        filePrefix  = "Terror-detect-"+utils.getTimeFlag(flag=1) # 没有设置前缀，那么自动生成前缀
    res, resInfo = gen_imagesets.renamePascalImageDataSet(
        vocpath=vocpath, filePrefix=filePrefix)
    if not res:
        print(resInfo)
        resInfo = "rename pascal image error"
        return (False, resInfo)
    # 这个是生成 pascal voc 格式的数据集 xml  jpg txt
    gen_imagesets.gen_imagesets(vocpath=vocpath)
    pass


def covertLabelxMulFilsToVoc_Fun(labelxPath=None, vocResultPath=None, renamePrefix=None):
    """
        将指定目录下的所有打标过的json 文件转换成 pascal xml 格式数据
    """
    inputDir = labelxPath
    tempSaveDir = labelxPath+"-xmlNeedTempFileDir"
    vocpath = vocResultPath
    if not os.path.exists(tempSaveDir):
        os.makedirs(tempSaveDir)
    if not os.path.exists(vocpath):
        os.makedirs(vocpath)
    # 1 : mergeAllJsonListFileToOneFile 将多个jsonlist 合并成一个，并按照url 去重
    finalOneFile = labelxJson_helper.mergeAllJsonListFileToOneFile(
        inputDir=inputDir, tempSaveDir=tempSaveDir)
    # 2 : 根据整合生成的一个总文件，开始下载图片，生成 xml 文件
    process_labelx_jsonFile_Fun(
        json_file_absolutePath=finalOneFile, tempSaveDir=tempSaveDir, vocpath=vocpath, renamePrefix=renamePrefix)
    pass

def mergePascalDataset(littlePath=None, finalPath=None):
    if not os.path.exists(finalPath):
        os.makedirs(finalPath)
    if not os.path.exists(os.path.join(finalPath, 'JPEGImages')):
        os.makedirs(os.path.join(finalPath, 'JPEGImages'))
    if not os.path.exists(os.path.join(finalPath, 'Annotations')):
        os.makedirs(os.path.join(finalPath, 'Annotations'))
    if not os.path.exists(os.path.join(finalPath, 'ImageSets', 'Main')):
        os.makedirs(os.path.join(finalPath, 'ImageSets', 'Main'))
    # merge image and merge xml
    littlePath_image = os.path.join(littlePath, 'JPEGImages')
    finalPath_image = os.path.join(finalPath, 'JPEGImages')
    littlePath_image_count = utils.getFileCountInDir(littlePath_image)[0]
    littlePath_xml = os.path.join(littlePath, 'Annotations')
    finalPath_xml = os.path.join(finalPath, 'Annotations')
    littlePath_xml_count = utils.getFileCountInDir(littlePath_xml)[0]
    if littlePath_image_count != littlePath_xml_count:
        print("ERROR : %s JPEGImages-nums unequals Annotations-nums" %(littlePath))
        return "error"
    # cmdStr_cp_image = "cp %s/* %s" % (littlePath_image, finalPath_image)
    cmdStr_cp_image = "for i in `ls %s`;do cp \"%s/\"$i %s;done;" % (
        littlePath_image, littlePath_image, finalPath_image)
    # cmdStr_cp_xml = "cp %s/* %s" % (littlePath_xml, finalPath_xml)
    cmdStr_cp_xml = "for i in `ls %s`;do cp \"%s/\"$i %s;done;" % (
        littlePath_xml, littlePath_xml, finalPath_xml)
    res = os.system(cmdStr_cp_image)
    if res != 0:
        print("ERROR : %s" % (cmdStr_cp_image))
        return "error"
    else:
        print("SUCCESS : %s" % (cmdStr_cp_image))
    res = os.system(cmdStr_cp_xml)
    if res != 0:
        print("ERROR : %s" % (cmdStr_cp_xml))
        return "error"
    else:
        print("SUCCESS : %s" % (cmdStr_cp_xml))
    # merge txt file
    littlePath_main = os.path.join(littlePath, 'ImageSets', 'Main')
    finalPath_main = os.path.join(finalPath, 'ImageSets', 'Main')
    textFile_list = utils.getFileCountInDir(dirPath=littlePath_main)[1]
    for i in textFile_list:
        little_file = os.path.join(littlePath_main,i)
        final_file = os.path.join(finalPath_main, i)
        cmdStr = "cat %s >> %s" % (little_file, final_file)
        res = os.system(cmdStr)
        if res != 0:
            print("ERROR : %s" % (cmdStr))
            return 'error'
    # recode log
    record_log_file = os.path.join(finalPath,'update_log.log')
    with open(record_log_file,'a') as f:
        f.write("update info : %s add dataset ::: %s\n" % (getTimeFlag(), littlePath.split('/')[-1]))
        littlePath_readme = os.path.join(littlePath, 'readme.txt')
        littlePath_readme_dict = json.load(open(littlePath_readme,'r'))
        f.write(json.dumps(littlePath_readme_dict)+'\n')
    little_readme_file = os.path.join(littlePath, 'readme.txt')
    little_readme_file_dict = json.load(open(little_readme_file, 'r'))
    final_readme_file = os.path.join(finalPath, 'readme.txt')
    if not os.path.exists(final_readme_file):
        cmdStr = "cp %s %s" % (little_readme_file, final_readme_file)
        res = os.system(cmdStr)
        if res != 0:
            return 'error'
    else:
        final_readme_file_dict = json.load(open(final_readme_file, 'r'))
        final_imageInfo_dict = final_readme_file_dict['imageInfo']
        little_imageInfo_dict = little_readme_file_dict['imageInfo']
        for key in final_imageInfo_dict.keys():
            if key == "date":
                final_imageInfo_dict[key] = getTimeFlag()
            if key == "dataInfo":
                for i in little_imageInfo_dict[key]:
                    final_imageInfo_dict[key].append(i)
            if key == "author":
                final_imageInfo_dict[key] = 'Ben'
            elif key in ['total_num', 'trainval_num', 'test_num']:
                final_imageInfo_dict[key] = final_imageInfo_dict[key] + \
                    little_imageInfo_dict[key]
        final_bboxInfo_dict = final_readme_file_dict['bboxInfo']
        little_bboxInfo_dict = little_readme_file_dict['bboxInfo']
        for i_key in final_bboxInfo_dict.keys():
            if isinstance(final_bboxInfo_dict[i_key],dict):
                for i_i_key in final_bboxInfo_dict[i_key].keys():
                    if isinstance(final_bboxInfo_dict[i_key][i_i_key],int):
                        if i_i_key in little_bboxInfo_dict[i_key]:
                            final_bboxInfo_dict[i_key][i_i_key] += little_bboxInfo_dict[i_key][i_i_key]
                        else:
                            final_bboxInfo_dict[i_key][i_i_key] += 0
        # add bbox in little dataset and not in final dataset
        for i_key in little_bboxInfo_dict.keys():
            if isinstance(little_bboxInfo_dict[i_key], dict):
                for i_i_key in little_bboxInfo_dict[i_key].keys():
                    if isinstance(little_bboxInfo_dict[i_key][i_i_key], int):
                        if i_i_key not in final_bboxInfo_dict[i_key]:
                            final_bboxInfo_dict[i_key][i_i_key] = little_bboxInfo_dict[i_key][i_i_key]
        with open(final_readme_file,'w') as f:
            json.dump(final_readme_file_dict, f, indent=4)
    pass


def getTimeFlag():
    return time.strftime("%Y-%m-%d-%H-%M-%s", time.localtime())

# 根据 图片 和 xml 文件 生成 Main 目录下的 trainval.txt  test.txt
def gen_imageset_Fun(vocPath=None):
    gen_imagesets.gen_imagesets(vocpath=vocPath)
    pass

# 统计数据集中的bbox的信息
def statisticBboxInfo_Fun(vocPath=None):
    mainDir = os.path.join(vocPath, 'ImageSets/Main')
    if not os.path.exists(mainDir):
        print("ImageSets/Main  not exist , so first create")
        gen_imageset_Fun(vocPath=vocPath)
    xmlPath = os.path.join(vocPath, 'Annotations')
    trainval_file = os.path.join(vocPath, 'ImageSets/Main', 'trainval.txt')
    trainval_file_res_dict = gen_imagesets.statisticBboxInfo(
        imagelistFile=trainval_file, xmlFileBasePath=xmlPath, printFlag=True)
    test_file = os.path.join(vocPath, 'ImageSets/Main', 'test.txt')
    test_file_res_dict = gen_imagesets.statisticBboxInfo(
        imagelistFile=test_file, xmlFileBasePath=xmlPath, printFlag=True)
    # write the statistic bbox info to file
    statisLogFile = os.path.join(vocPath,'statistic-bbox-log.log')
    with open(statisLogFile,'a') as f:
        f.write('*'*10+getTimeFlag()+'*'*10+'\n')
        keys = trainval_file_res_dict.keys() if len(trainval_file_res_dict.keys()) > len(
            test_file_res_dict.keys()) else test_file_res_dict.keys()
        for i in sorted(keys):
            count = 0
            if i in trainval_file_res_dict.keys():
                count += trainval_file_res_dict.get(i)
            if i in test_file_res_dict.keys():
                count += test_file_res_dict.get(i)
            line = "%s\t%d\n" % (i.ljust(30,' '),count)
            f.write(line)
    pass


def drawImageWithBbox(absoluteImagePath=None, absoluteXmlFilePath=None, savePath=None):
    print("absoluteImagePath is %s ;\tabsoluteXmlFilePath is %s" %
          (absoluteImagePath, absoluteXmlFilePath))
    print("savePath : %s" % (savePath))
    tree = etree.parse(absoluteXmlFilePath)
    rooTElement = tree.getroot()
    object_list = []
    for child in rooTElement:
        if child.tag == "filename":
            if child.text != absoluteImagePath.split('/')[-1]:
                print("%s != %s" % (child.text, absoluteImagePath))
        elif child.tag == "object":
            one_object_dict = {}
            one_object_dict['name'] = child.xpath('name')[0].text
            one_object_dict['xmin'] = child.xpath(
                'bndbox')[0].xpath('xmin')[0].text
            one_object_dict['ymin'] = child.xpath(
                'bndbox')[0].xpath('ymin')[0].text
            one_object_dict['xmax'] = child.xpath(
                'bndbox')[0].xpath('xmax')[0].text
            one_object_dict['ymax'] = child.xpath(
                'bndbox')[0].xpath('ymax')[0].text
            object_list.append(one_object_dict)
            pass
        pass
    color_black = (0, 0, 0)
    im = cv2.imread(absoluteImagePath)
    for object in object_list:
        color = (random.randint(0, 256), random.randint(
            0, 256), random.randint(0, 256))
        cv2.rectangle(im, (int(object.get('xmin')), int(object.get('ymin'))), (int(
            object.get('xmax')), int(object.get('ymax'))), color=color, thickness=1)
        cv2.putText(im, '%s' % (object.get('name')), (int(object.get('xmin')), int(object.get(
            'ymin')) + 10), color=color_black, fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=0.5)
    cv2.imwrite(savePath, im)
    pass
    pass

def drawImageWithBbosFun(vocPath=None):
    xmlFilePath = os.path.join(vocPath, 'Annotations')
    imageFilePath = os.path.join(vocPath, 'JPEGImages')
    drawImageSavePath = vocPath+'-draw'
    if not os.path.exists(drawImageSavePath):
        os.makedirs(drawImageSavePath)
    xmlList = os.listdir(xmlFilePath) # get xml file
    random_xml_list = random.sample(xmlList, len(xmlList)//1000)
    for xml_name in random_xml_list:
        xmlFile = os.path.join(xmlFilePath, xml_name)
        imageFile = os.path.join(imageFilePath, xml_name[:xml_name.rfind('.')]+'.jpg')
        saveImageFile = os.path.join(
            drawImageSavePath, xml_name[:xml_name.rfind('.')]+'.jpg')
        drawImageWithBbox(absoluteImagePath=imageFile,
                          absoluteXmlFilePath=xmlFile, savePath=saveImageFile)
        pass
    pass
    pass

def getAllImageMD5Fun(vocPath=None,deleteFlag=False):
    allImageList = []
    imageBasePath = os.path.join(vocPath, 'JPEGImages')
    for i in sorted(os.listdir(imageBasePath)):
        allImageList.append(os.path.join(imageBasePath,i))
    imageMd5_dict = gen_imagesets.getAllImageMd5(imageList=allImageList)
    md5_result_file = os.path.join(vocPath,'md5_result.json')
    with open(md5_result_file,'w') as f:
        for image_md5 in imageMd5_dict:
            md5_images_list = imageMd5_dict[image_md5]
            line_dict = {}
            line_dict['md5'] = image_md5
            line_dict['count'] = len(md5_images_list)
            line_dict['images'] = md5_images_list
            f.write('%s\n'%(json.dumps(line_dict)))
    deleteFileList = [] # just save iamgeFile ( not include postfix)
    for image_md5 in imageMd5_dict:
        md5_images_list = imageMd5_dict[image_md5]
        if len(md5_images_list) > 1: # 这个 md5 对应的图片有重复的
            if deleteFlag:
                md5_xmls_list = []
                for i_image in md5_images_list:
                    just_image_name = i_image.split('/')[-1].split('.')[0]
                    i_xml = os.path.join(vocPath, 'Annotations',
                                         just_image_name+'.xml')
                    md5_xmls_list.append(i_xml)
                saveIndex , saveXmlFile = xml_helper.getMaxBboxXml(xmlFileList=md5_xmls_list)
                saveJustImageName = saveXmlFile.split('/')[-1].split('.')[0]
                for i_index in range(len(md5_images_list)):
                    imaeg_name = md5_images_list[i_index]
                    xml_name = md5_xmls_list[i_index]
                    if saveJustImageName not in imaeg_name: # delete image and xml file 
                        cmdStr = "rm %s && rm %s"%(imaeg_name,xml_name)
                        res = os.system(cmdStr)
                        if res != 0:
                            print("Error")
                            print(cmdStr)
                            exit()
                        deleteFile = imaeg_name.split('/')[-1].split('.')[0]
                        deleteFileList.append(deleteFile)
    if deleteFlag and len(deleteFileList) > 0:  # 由于删除了文件，需要重新生成 ImageSets/Main
        # gen_imagesets.gen_imagesets(vocpath=vocPath)
        # 保持原来的 trainval test 文件不变，把已经删除的文件，从 trainval test 中去除掉
        gen_imagesets.recreateTrainvalTestFile(vocPath=vocPath)
        
    
def reWriteImageWithCv2(vocPath=None):
    allImageList = []
    imageBasePath = os.path.join(vocPath, 'JPEGImages')
    for i in sorted(os.listdir(imageBasePath)):
        allImageList.append(os.path.join(imageBasePath, i))
    for i in range(len(allImageList)):
        imageNamePath = allImageList[i]
        res = image_helper.cv2ImreadAndWrite(
            oldImageNamePath=imageNamePath, newImageNamePath=imageNamePath)
        if not res : # error
            exit
        if (i+1) % 1000 == 0:
            print("processing : %d"%(i+1))
    print("cv2 imwrite all image success")
    pass
