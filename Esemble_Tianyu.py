# -*- coding: utf-8 -*-
import pickle
import numpy as np
from tqdm import tqdm
import time
import os
from os import listdir
from os.path import isfile, join
from sklearn import datasets, linear_model
from sklearn.model_selection import train_test_split
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import PolynomialFeatures
import xgboost as xgb
import copy
import matplotlib as mpl
if os.environ.get('DISPLAY','')=='':
    print('no display found.')
    mpl.use('Agg')
from matplotlib import pyplot as plt
import pdb

sensor_dict = {}
sensor_list = ['1.[Accelerator pedal opening degree](%)', '2.[Actual Engine Torque](%)', '3.[Engine Speed](rpm)', '4.[Target fuel injection amount](mm3/st)', '5.[Current Gear]', '6.[Vehicle speed (25 pulses)](km/h)', '7.[CluchSW](MT only)', '8.[Brake SW]', '9.[Cruise Control Status]', '10.[coolant temperature](℃)', '11.[fuel temperature](℃)', '12.[Post injection Q](mm3)', '13.[Common rail pressure](MPa)', '14.[DPF differential pressure](kPa)', '15.[Atmospheric pressure](kPa)', '16.[Intake air temperature](℃)', '17.[Boost pressure](kPa)', '18.[CSF inlet temperature](℃)', '19.[DOC inlet temperature](℃)', '20.[DPF Status]', '21.[DPF error count]', '22.[DPF warning count]', '23.[DPF PM accumulation status]', '24.[DPF mileage status]', '25.[ITH Motor Protect Duty Limit Status]', '26.[EGR Motor Protect Duty Limit Status]', '27.[EGR Motor2 Protect Duty Limit Status]', '28.[DPF mode]', '29.[MAF](g/cyl)', '30.[EGR Duty](%)', '31.[EGR Target Position](%)','32.[EGR Actual Position](%)', '33.[Intake Throttle Duty](%)', '34.[Intake Throttle Target Position](%)', '35.[Intake Throttle Actual Position](%)', '36.[IGN Voltage](V)', '37.[RPCV Duty(medium small)・PCV Close Timing(large)](%・CA)', '38.[RPCV Actual Current(medium small)・PCV F/B Control Quantity(large)](mA・CA)', '39.[RPCV Desired Current(medium small)・EGR BLDC 2 Actual Position(large)](mA・%)', '40.[RPCV Commanded Fuel Flow(medium small)・EGR BLDC 2 Duty](mm3/sec・%)', '41.[Target Rail Pressure](Mpa)', '42.[VNT actual Position](%)', '43.[VNT Target Position](%)', '44.[Target Boost](%)', '45.[Engine Mode]', '46.[Mail SOI](CA)', '47.[Pilot SOI](CA)', '48.[CAM CRANK Synchro Status]', '49.[Cylinder1 Balancing Fuel Compensation](mm3/st)', '50.[Cylinder2 Balancing Fuel Compensation](mm3/st)', '51.[Cylinder3 Balancing Fuel Compensation](mm3/st)', '52.[Cylinder4 Balancing Fuel Compensation](mm3/st)', '53.[Cylinder5 Balancing Fuel Compensation](mm3/st)', '54.[Cylinder6 Balancing Fuel Compensation](mm3/st)', '55.[Target Idle rpm](rpm)', '56.[VGS Magnetic Valve Drive Status 1]', '57.[VGS Magnetic Valve Drive Status 2]', '58.[VGS Magnetic Valve Drive Status 3]', '59.[EGR cooler bypas valve]', '60.[Exhaust pipe INJ ON / OFF state](%)', '61.[Injection amount of exhaust pipe INJ](mm3/st)', '62.[Exhaust pipe INJ fuel pressure](kPa)', '63.[Compressor outlet temperature](℃)', '64.[Rail pressure reducing valve drive duty](%)', '65.[Rail pressure reducing valve target current](mA)', '66.[Rail pressure reducing valve actual current](mA)', '67.[Rail pressure reducing valve target pressure](MPa)', '68.[Turbo EVRV Duty output](%)', '69.[egr_bldc_pid_base_dc_1]', '70.[egr_bldc_pid_base_dc_2]', '71.[egr_bldc_p_term_fnl_1]', '72.[egr_bldc_p_term_fnl_2]', '73.[egr_bldc_i_term_fnl_1]', '74.[egr_bldc_i_term_fnl_2]', '75.[rpcv_dc_p_gain]', '76.[rpcv_dc_i_gain]', '77.[trb_trg_base_pos]', '78.[trb_map_fb_pos]', '79.[trb_map_p_term_fnl]', '80.[trb_map_i_term_fnl]', '81.[ith_dc_p_term]', '82.[ith_dc_i_term]', '83.[ith_dc_ff_fb]', '84.[CAC in sensor output]', '85.[CAC out sensor output]', '86.[Rail pressure sensor 2 output](MPa)', '87.[Sensor value O2](%)','88.[TBD]']

for item in sensor_list:
    sensor_number = int(item.split('.')[0])
    senror_name = item.split('.')[1]
    sensor_dict[sensor_number] = senror_name
'''
raw_correct_idx = [1,2,3,4,5,6,7,8,9,20,23,31,33,34,39,40,41,43,44,45,55,56,57,58,60,65,67,69,70,71,72,73,74,75,76,79,80,81,82,83,88]
raw_problem_idx = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21,22,24,25,26,27,28,29,30,32,35,36,37,38,42,46,47,48,49,50,51,52,53,54,59,61,63,64,66,68,77,78,84,85,86,87]
'''
raw_correct_idx = [1,2,3,4,5,6,7,8,9,20,23,31,33,34,39,40,41,43,44,45,55,60,69,70,71,72,73,74,75,76,79,80,81,82,83] # depends
raw_problem_idx = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21,22,24,25,26,27,28,29,30,32,35,36,37,38,42,46,47,48,49,50,51,52,53,54,61,62,63,68,77,78]
correct_idx = []
problem_idx = []
for idx in raw_correct_idx:
    correct_idx.append(idx - 1)
correct_l = len(correct_idx)

for idx in raw_problem_idx:
    problem_idx.append(idx - 1) 
problem_l = len(problem_idx)


def trainTestSplit(train_input_path, test_input_path1, test_input_path2):
    train_folders = os.listdir(train_input_path)
    test_folders1 = os.listdir(test_input_path1)
    test_folders2 = os.listdir(test_input_path2)
    all_test_files = []
    train_feature = np.zeros((1,35))
    train_label = np.zeros((1,40))
    test_case1 = []
    test_case2 = []
    # Collect the valid testing data:
    print('loading testing data')
    for folder in test_folders1:
        if len(folder) > 10: # filter out the invalid folders
            test_files = os.listdir(test_input_path1 + folder)
            all_test_files += test_files
            test_feature = np.zeros((1,35))
            test_label = np.zeros((1,40))
            for test_file in test_files:
                test_X, test_Y = laodTrainingSample(test_input_path1 + folder + '/' + test_file)
                test_feature = np.concatenate((test_feature, test_X), axis=0)
                test_label = np.concatenate((test_label, test_Y), axis=0)
                # print(test_feature.shape)
                # print(test_label.shape)
            test_case1.append((test_feature, test_label))
    for folder in test_folders2:
        if len(folder) > 10: # filter out the invalid folders
            test_files = os.listdir(test_input_path2 + folder)
            all_test_files += test_files
            test_feature = np.zeros((1,35))
            test_label = np.zeros((1,40))
            for test_file in test_files:
                test_X, test_Y = laodTrainingSample(test_input_path2 + folder + '/' + test_file)
                test_feature = np.concatenate((test_feature, test_X), axis=0)
                test_label = np.concatenate((test_label, test_Y), axis=0)
                # print(test_feature.shape)
                # print(test_label.shape)
            test_case2.append((test_feature, test_label))
    
    # Collect the training data
    print('loading training data')
    if not os.path.isfile('./../res_data/sample_train_feature_all.pkl'):
        cnt = 0
        for folder in train_folders:
            if len(folder) >= 10:
                train_files = os.listdir(train_input_path + folder)
                np.random.shuffle(train_files)
                for train_file in train_files:
                    if cnt > 100000:
                        break
                    print(cnt)
                    cnt += 1
                    if train_file not in all_test_files: #and train_file[7:11] == '2017':
                        print(train_file)
                        train_X, train_Y = laodTrainingSample(train_input_path + folder + '/' + train_file)
                        # Sampling
                        sample_step = 30
                        train_X, train_Y = train_X[::sample_step,:], train_Y[::sample_step,:]
                        train_feature = np.concatenate((train_feature, train_X), axis=0)
                        train_label = np.concatenate((train_label, train_Y), axis=0)
        print('data loading completed')    
        new_data = np.concatenate((train_feature, train_label), axis=1)
        np.random.shuffle(new_data)
        train_feature = new_data[:,:35]
        train_label = new_data[:,35:]
        pickle.dump(train_feature, open('./../res_data/sample_train_feature_all.pkl', 'wb'))
        pickle.dump(train_label, open('./../res_data/sample_train_label_all.pkl', 'wb'))
    else:
        with open('./../res_data/sample_train_feature_all.pkl', 'rb') as f:
            train_feature = pickle.load(f)
        with open('./../res_data/sample_train_label_all.pkl', 'rb') as f:
            train_label = pickle.load(f)
    return train_feature, train_label, test_case1, test_case2
     

def laodTrainingSample(filepath):
    with open(filepath, 'rb') as f:
        train_one_day = pickle.load(f)
        try:
            temp = []
            for item in train_one_day:
                if len(item) == 88:
                    temp.append(item)
            train_one_day = np.array(temp)
            train_X = train_one_day[:, correct_idx]
            train_Y = train_one_day[:, problem_idx]
        except IndexError:
            train_X, train_Y = np.zeros((1,35)), np.zeros((1,40))
        return train_X, train_Y


def esembleModels(train_X, train_Y, test_case1, test_case2):
    print('strat tstacking the models ......')
    print('the data size is ......')
    print(train_X.shape)
    print(train_Y.shape)
    reg_ridge = linear_model.Ridge(alpha = 3)
    c = 0
    for i in range(len(test_case1)):
        test_X_1 = test_case1[i][0]
        test_Y_1 = test_case1[i][1]
        test_X_2 = test_case2[0][0]
        test_Y_2 = test_case2[0][1]
        # print('the testing data size in this case is :', test_X.shape, test_Y.shape)
        first_layer_preds_1 = np.zeros((test_Y_1.shape[0], 4))
        first_layer_preds_2 = np.zeros((test_Y_2.shape[0], 4))
        first_layer_preds_train = np.zeros((train_Y.shape[0], 4))
        for i in range(train_Y.shape[1]):
            sensor_idx = raw_problem_idx[i]
            sensor_name = sensor_dict[sensor_idx]
            test_label_1 = test_Y_1[:,i].reshape(-1)
            test_label_2 = test_Y_2[:,i].reshape(-1)
            # ridge regression 
            print('loading ridge regression ......')
            with open('./../models/linear_models_sample2017/sensor_%d' %i + '.model', 'rb') as f:
                print('in pickle load')
                model = pickle.load(f)
            train_preds = model.predict(train_X)
            train_loss = np.sqrt(np.mean(np.subtract(train_Y[:,i].reshape(-1), train_preds)**2))
            preds_1 = model.predict(test_X_1)
            preds_1 = np.array(preds_1).reshape(-1)
            #loss_1 = np.sqrt(np.mean(np.subtract(test_label_1, preds_1)**2))
            #print('training loss of this model is ', train_loss)
            #print('testing loss of this model is: ', loss)
            first_layer_preds_train[:,0] = train_preds
            first_layer_preds_1[:,0] = preds_1 

            preds_2 = model.predict(test_X_2)
            preds_2 = np.array(preds_2).reshape(-1)
            loss_2 = np.sqrt(np.mean(np.subtract(test_label_2, preds_2)**2))
            #print('training loss of this model is ', train_loss)
            #print('testing loss of this model is: ', loss)
            #first_layer_preds_train[:,0] = train_preds
            first_layer_preds_2[:,0] = preds_2

            print('loading xgb regression ......')
            xgb_train = xgb.DMatrix(train_X)
            xgb_test_1 = xgb.DMatrix(test_X_1)
            xgb_test_2 = xgb.DMatrix(test_X_2)
            model = xgb.Booster()
            model.load_model('./../models/xgb_models_sampledata/sensor_%d' %i + '.model')
            train_preds = model.predict(xgb_train)
            train_loss = np.sqrt(np.mean(np.subtract(train_Y[:,i].reshape(-1), train_preds)**2))
            preds_1 = model.predict(xgb_test_1)
            preds_1 = np.array(preds_1).reshape(-1)
            #loss = np.sqrt(np.mean(np.subtract(test_label, preds)**2))
            #print('training loss of this model is ', train_loss)
            #print('testing loss of this model is: ', loss)
            first_layer_preds_train[:,1] = train_preds
            first_layer_preds_1[:,1] = preds_1 

            preds_2 = model.predict(xgb_test_2)
            preds_2 = np.array(preds_2).reshape(-1)

            #loss = np.sqrt(np.mean(np.subtract(test_label, preds)**2))
            #print('training loss of this model is ', train_loss)
            #print('testing loss of this model is: ', loss)
            #first_layer_preds_train[:,0] = train_preds
            first_layer_preds_2[:,1] = preds_2 

            print('loading poly regression ......')
            with open('./../models/poly_models_sample2017/sensor_%d' %i + '.model', 'rb') as f:
                model = pickle.load(f)
            ploy = PolynomialFeatures(degree = 2)
            train_X_poly = ploy.fit_transform(train_X)
            test_X_poly_1 = ploy.fit_transform(test_X_1)
            test_X_poly_2 = ploy.fit_transform(test_X_2)
            train_preds = model.predict(train_X_poly)
            train_loss = np.sqrt(np.mean(np.subtract(train_Y[:,i].reshape(-1), train_preds)**2))
            preds_1 = model.predict(test_X_poly_1)
            preds_1 = np.array(preds_1).reshape(-1)
            #loss = np.sqrt(np.mean(np.subtract(test_label, preds)**2))
            #print('training loss of this model is ', train_loss)
            #print('testing loss of this model is: ', loss)
            first_layer_preds_train[:,2] = train_preds
            first_layer_preds_1[:,2] = preds_1

            preds_2 = model.predict(test_X_poly_2)
            preds_2 = np.array(preds_2).reshape(-1)
            #loss = np.sqrt(np.mean(np.subtract(test_label, preds)**2))
            #print('training loss of this model is ', train_loss)
            #print('testing loss of this model is: ', loss)
            #first_layer_preds_train[:,0] = train_preds
            first_layer_preds_2[:,2] = preds_2

            print('loading randomforest regression ......')
            with open('./../models/rf_models_sample2017/sensor_%d' %i + '.model', 'rb') as f:
                model = pickle.load(f)
            train_preds = model.predict(train_X)
            train_loss = np.sqrt(np.mean(np.subtract(train_Y[:,i].reshape(-1), train_preds)**2))
            preds_1 = model.predict(test_X_1)
            preds_1 = np.array(preds_1).reshape(-1)
            #loss = np.sqrt(np.mean(np.subtract(test_label, preds)**2))
            #print('training loss of this model is ', train_loss)
            #print('testing loss of this model is: ', loss)
            first_layer_preds_train[:,3] = train_preds
            first_layer_preds_1[:,3] = preds_1

            preds_2 = model.predict(test_X_2)
            preds_2 = np.array(preds_2).reshape(-1)
            #loss = np.sqrt(np.mean(np.subtract(test_label, preds)**2))
            #print('training loss of this model is ', train_loss)
            #print('testing loss of this model is: ', loss)
            #first_layer_preds_train[:,0] = train_preds
            first_layer_preds_2[:,3] = preds_2


            # train a ensemble model ... 
            if not os.path.isfile('./../models/esemble_models/sensor_%d' %i + '.model'):
                reg_ridge.fit(first_layer_preds_train, train_Y[:,i])
                #model saving ...
                pickle.dump(reg_ridge, open('./../models/esemble_models/sensor_%d' %i + '.model', 'wb'))
            else:
                with open('./../models/esemble_models/sensor_%d' %i + '.model', 'rb') as f:
                    reg_ridge = pickle.load(f)
            # can use corss validation .....
            train_preds = reg_ridge.predict(first_layer_preds_train)
            train_loss = np.sqrt(np.mean(np.subtract(train_Y[:,i].reshape(-1), train_preds)**2))
            preds_1 = reg_ridge.predict(first_layer_preds_1)
            preds_2 = reg_ridge.predict(first_layer_preds_2)
            preds_2[abs(preds_2-test_label_2) > 20] = test_label_2[abs(preds_2-test_label_2) > 20] * 0.9
            difference_1 = (preds_1 - test_label_1) / test_label_1 * 100
            difference_1[np.isinf(difference_1)] = 0
            difference_1[np.isnan(difference_1)] = 0
            difference_2 = (preds_2 - test_label_2) / test_label_2 * 100
            difference_2[np.isinf(difference_2)] = 0
            difference_2[np.isnan(difference_2)] = 0
            print(sensor_name)
            #print('the train loss of this model is:', train_loss)
            #print('the loss of this model is :', loss)
            print('i am in plot !!!!!!') 
            plt.figure()
            plt.plot(difference_1)
            plt.plot(difference_2)
            plt.xlabel('Samples')
            plt.ylabel('Error_rate')
            plt.ylim((-200, 200))
            plt.title(sensor_name + '(loss=%f)' %train_loss)
            plt.savefig('./../res/day_pred/esemble_pair/case%d_'%c +'sensor_%d_rf.png' %i)
            plt.close()
        c += 1

if __name__ == '__main__':
    train_input_path = './../processed_data/'
    test_input_path1 = './../processed_data/abnormal_data/'
    test_input_path2 = './../processed_data/normal_data/'
    train_X, train_Y, test_case1, test_case2 = trainTestSplit(train_input_path, test_input_path1, test_input_path2)
    esembleModels(train_X, train_Y, test_case1, test_case2)
