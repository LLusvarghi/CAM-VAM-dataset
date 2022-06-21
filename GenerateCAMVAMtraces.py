from __future__ import division
import numpy as np
import sys, os, getopt, time, math, csv
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt


def SaveCAMTrace(filePath, CAMtrace):
   with open(filePath,'w') as DSTfile:
     DSTfile.write('seq_num,timestamp,TgenCAM,latitude,longitude,heading,velocity,size,trig_vel,trig_head,trig_distance,trig_timeout\r\n')
     for row in CAMtrace:
#       print (row)
       DSTfile.write(str(row[0]) + ',' + str(row[1]) + ',' + str(row[2]) + ',' + str(row[3]) + ',' + str(row[4]) + ',' + str(row[5]) + ',' \
       + str(row[6]) + ',' + str(row[7]) + ',' + str(row[8]) + ',' + str(row[9]) + ',' + str(row[10]) + ',' + str(row[11]) + '\r\n')


def SaveCoordinates(filePath, latitude, longitude):
   with open(filePath,'w') as DSTfile:
     DSTfile.write('latitude,longitude\r\n')
     for lat, lon in zip(latitude,longitude):
       DSTfile.write(str(lat) + ',' + str(lon) + '\r\n')


def CheckIfNan (IN):
   if math.isnan(IN):
     IN = 0

   return IN


def CAMtrigger (Triggers):
   Label = ''
#   print (Triggers)
   if Triggers[3] == 1:
#     print ('Timeout')
     Label = 'T'
   elif Triggers[0:3].count(1) > 1: 
#     print ('Mixed')
     Label = 'M'
   else: 
     if Triggers[0] == 1:
#       print ('Distance')
       Label = 'D'
     if Triggers[1] == 1:
#       print ('Heading')
       Label = 'H'
     if Triggers[2] == 1:
#       print ('Velocity')
       Label = 'V'

   return Label
   

def haversine(lon1, lat1, lon2, lat2):
   """
   Calculate the great circle distance in kilometers between two points 
   on the earth (specified in decimal degrees)
   """
   # convert decimal degrees to radians 
   lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

   # haversine formula 
   dlon = lon2 - lon1 
   dlat = lat2 - lat1 
   a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
   c = 2 * math.asin(math.sqrt(a)) 
   r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
   return c * r


def main():
   heading_threshold = 4.0
   distance_threshold = 4.0 
   velocity_threshold = 0.5
   deltaSpeed_threshold = 1
   speed_threshold = 3
   try:
      opts, args = getopt.getopt(sys.argv[1:],"h",["help","heading=","velocity=","distance=","speedTh=","dSpeedTh="])
   except getopt.GetoptError as err:
      print (str(err))
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print ('no options')
         sys.exit()
      elif opt == '--heading':
         heading_threshold = float(arg)
      elif opt == '--velocity':
         velocity_threshold = float(arg)
      elif opt == '--distance':
         distance_threshold = float(arg)
      elif opt == '--speedTh':
         speed_threshold = float(arg)
      elif opt == '--dSpeedTh':
         deltaSpeed_threshold = float(arg)
      else:
         assert False, "unhandled option"

   matplotlib.rcParams['mathtext.fontset'] = 'stix'
   matplotlib.rcParams['font.family'] = 'STIXGeneral'

   Tgen_type = {}
   for i in range(50):
     Tgen_type[int((i+1)*100)] = {'V':0, 'H':0, 'D':0, 'T':0, 'M':0}

   print ('Heading threshold is {}°'.format(heading_threshold))
   print ('Velocity threshold is {} m/s'.format(velocity_threshold))
   print ('Distance threshold is {} m'.format(distance_threshold))

   
   timeout = 5000
#   heading_threshold = 4  
#   distance_threshold = 4 
#   velocity_threshold = 0.5
   
   dirPath = os.getcwd()

   dirPath = os.path.join(dirPath,'LLCAMScript')
#   dirPath = os.path.join(dirPath,'Bicycle_Tracker_Data')
#   print (dirPath) 

   filesList = os.listdir(dirPath)

   filesList_tmp = []
   for fileName in filesList:
     if len(fileName.split(".")) > 1:
       if fileName.split(".")[1] == 'txt':
         filesList_tmp.append(fileName)

   filesList = filesList_tmp

  # print (filesList)

   TgenValues = []

   Mixed_Heading = 0
   totalNumPoints = 0
   print ('Directory path',dirPath)
   for fileName in filesList:
     print ('Opening',fileName)
     data = pd.read_csv(dirPath + '/' + fileName)
     filtered_data = tuple(zip(data['latitude'], data['longitude'], data['heading'], data['velocity'], data['seq_num'],data['timestamp'],data['size'],data['deltaspeed']))
     print ('File length:',len(filtered_data))
     totalNumPoints += len(filtered_data)

     seq_num = 0
     CAMtrace = []

     lat_heading = []
     lon_heading = []
     lat_distance = []
     lon_distance = []
     lat_velocity = []
     lon_velocity = []
     lat_mixed = []
     lon_mixed = []
     lat_timeout = []
     lon_timeout = []

     ref_lat = CheckIfNan(filtered_data[0][0])
     ref_lon = CheckIfNan(filtered_data[0][1])
     ref_heading = CheckIfNan(filtered_data[0][2])
     ref_velocity = CheckIfNan(filtered_data[0][3])
     ref_index =  CheckIfNan(filtered_data[0][4])


     for row_index in range(1,len(filtered_data)):
#       print ('Reference',ref_lat,ref_lon,ref_heading,ref_velocity,ref_index)
#       print ('Current',filtered_data[row_index])
       #print ('Lat: {}, Lon: {}, heading: {}, speed: {}, delta speed: {}'.format(filtered_data[row_index][0],filtered_data[row_index][1],filtered_data[row_index][2],filtered_data[row_index][3],filtered_data[row_index][7]))

       current_lat = CheckIfNan(filtered_data[row_index][0])
       current_lon = CheckIfNan(filtered_data[row_index][1])
       current_heading = CheckIfNan(filtered_data[row_index][2])
       current_speed = CheckIfNan(filtered_data[row_index][3])
       current_deltaSpeed = round(CheckIfNan(filtered_data[row_index][7]),5)


       distance = haversine(current_lon,current_lat,ref_lon,ref_lat)*1000

       delta_heading = abs(current_heading - ref_heading)
       if delta_heading > 180:
         delta_heading = 360 - delta_heading

       delta_velocity = abs(current_speed - ref_velocity)

       delta_index = CheckIfNan(filtered_data[row_index][4])-ref_index

#    --------------------------- Algorithm implementation (FENOMMENNOOOOOO) ------------------------
#                        _____________________________________
#                       |                  |                  |
#                       |    Quadrant I    |    Quadrant II   |
#                       |                  |                  |
#       speed_threshold |-------------------------------------|
#                       |                  |                  |
#                       |   Quadrant III   |    Quadrant IV   |
#                       |__________________|__________________|                
#                                          |
#                                deltaSpeed_threshold

       if current_speed > speed_threshold and current_deltaSpeed <= deltaSpeed_threshold: # Quadrant I: good conditions (do nothing)
         #print ('Quadrant I')
         min_num_samples = 1 # default value
         heading_threshold = 4.0 # default value
         distance_threshold = 4.0 # default value
         velocity_threshold = 0.5 # default value
       elif current_speed >= speed_threshold and current_deltaSpeed > deltaSpeed_threshold: # Quadrant II: decrease sampling frequency
         #print ('Quadrant II')
         min_num_samples = 2
         heading_threshold = 4.0 # default value
         distance_threshold = 4.0 # default value
         velocity_threshold = 0.5 # default value
       elif current_speed <= speed_threshold and current_deltaSpeed <= deltaSpeed_threshold: # Quadrant III: increase thresholds
         #print ('Quadrant III')
         min_num_samples = 1 # default value
         heading_threshold = 4.0 * 2
         distance_threshold = 4.0 * 2
         velocity_threshold = 0.5 *2 
       else: # Quadrant IV: decrease sampling frequency and increase thresholds
         #print ('Quadrant IV')
         min_num_samples = 2
         heading_threshold = 4.0 * 2
         distance_threshold = 4.0 * 2
         velocity_threshold = 0.5 *2 
#    -----------------------------------------------------------------------------------------------

       #print('  Triggers,',distance,delta_heading,delta_velocity,delta_index)
       #print('Thresholds,',distance_threshold,heading_threshold,velocity_threshold,min_num_samples)

       if (distance > distance_threshold or delta_heading > heading_threshold or delta_velocity > velocity_threshold) and delta_index >= min_num_samples:
#         print('CAM')
#         input()
#       if distance > distance_threshold:
         TgenCAM = int((delta_index)*100)
         TgenValues.append(TgenCAM)
#         print ('Trigger CAM!',TgenCAM)
         distance_trigger = False
         heading_trigger = False
         velocity_trigger = False
         timeout_trigger = False
 
         if distance > distance_threshold:
           distance_trigger = True
         if delta_heading > heading_threshold:
           heading_trigger = True
           lat_heading.append(current_lat)
           lon_heading.append(current_lon)
         if delta_velocity > velocity_threshold:
           velocity_trigger = True

         CAMtrace.append( (seq_num,filtered_data[row_index][5],TgenCAM,current_lat,current_lon,current_heading, \
         current_speed,filtered_data[row_index][6],int(velocity_trigger),int(heading_trigger),int(distance_trigger),int(timeout_trigger)))
#         print (CAMtrace)
#         input()
         seq_num += 1

         Triggers = [distance_trigger,heading_trigger,velocity_trigger,timeout_trigger]         
         TriggerLabel = CAMtrigger(Triggers)

         if TriggerLabel == 'M' and Triggers[1]:  # Count the number of mixed triggers with heading component
           Mixed_Heading += 1   
#           print (Triggers)
         #   print (Tgen_type)
         Tgen_type[TgenCAM][TriggerLabel] += 1
         #   print (Tgen_type)
         #   input()  

         if TriggerLabel == 'D':
           lat_distance.append(filtered_data[row_index][0])
           lon_distance.append(filtered_data[row_index][1])
         elif TriggerLabel == 'H':
           lat_heading.append(filtered_data[row_index][0])
           lon_heading.append(filtered_data[row_index][1])
         elif TriggerLabel == 'V':
           lat_velocity.append(filtered_data[row_index][0])
           lon_velocity.append(filtered_data[row_index][1])
         elif TriggerLabel == 'M':
           lat_mixed.append(filtered_data[row_index][0])
           lon_mixed.append(filtered_data[row_index][1])         

         ref_lat = current_lat
         ref_lon = current_lon
         ref_heading = current_heading
         ref_velocity = current_speed
         ref_index = filtered_data[row_index][4]

       elif delta_index == 50: # timeout after 5000ms if there is no triggering condition
#         print('CAM')
#         input()
         TgenCAM = int((delta_index)*100)
         TgenValues.append(TgenCAM)
#         print ('Timeout CAM!',TgenCAM)

         distance_trigger = False
         heading_trigger = False
         velocity_trigger = False
         timeout_trigger = True

         CAMtrace.append( (seq_num,filtered_data[row_index][5],TgenCAM,filtered_data[row_index][0],filtered_data[row_index][1],filtered_data[row_index][2], \
         filtered_data[row_index][3],filtered_data[row_index][6],int(velocity_trigger),int(heading_trigger),int(distance_trigger),int(timeout_trigger)))
#         print (CAMtrace)
         seq_num += 1

         Triggers = [distance_trigger,heading_trigger,velocity_trigger,timeout_trigger]         
         TriggerLabel = CAMtrigger(Triggers)
         Tgen_type[TgenCAM][TriggerLabel] += 1
 
         lat_timeout.append(filtered_data[row_index][0])
         lon_timeout.append(filtered_data[row_index][1])  

         ref_lat = current_lat
         ref_lon = current_lon
         ref_heading = current_heading
         ref_velocity = current_speed
         ref_index = filtered_data[row_index][4]

     outputPath = os.path.join(dirPath,'GPStraces',fileName.split('.')[0] + '_' + str(heading_threshold) + '_CAMtrace.csv')      
     SaveCAMTrace(outputPath,CAMtrace)

     outputPath = os.path.join(dirPath,'GPStraces',fileName.split('.')[0] + '_' + str(heading_threshold) + '_' + str(velocity_threshold) + '_heading.csv')
     SaveCoordinates(outputPath, lat_heading, lon_heading)
     outputPath = os.path.join(dirPath,'GPStraces',fileName.split('.')[0] + '_' + str(heading_threshold) + '_' + str(velocity_threshold) + '_velocity.csv')
     SaveCoordinates(outputPath, lat_velocity, lon_velocity)
#     outputPath = os.path.join(dirPath,'GPStraces',fileName.split('.')[0] + '_' + str(heading_threshold) + '_' + str(velocity_threshold) + '_mixed.csv')
#     SaveCoordinates(outputPath, lat_mixed, lon_mixed)
     outputPath = os.path.join(dirPath,'GPStraces',fileName.split('.')[0] + '_' + str(heading_threshold) + '_' + str(velocity_threshold) + '_distance.csv')
     SaveCoordinates(outputPath, lat_distance, lon_distance)
     outputPath = os.path.join(dirPath,'GPStraces',fileName.split('.')[0] + '_' + str(heading_threshold) + '_' + str(velocity_threshold) + '_timeout.csv')
     SaveCoordinates(outputPath, lat_timeout, lon_timeout)

      
   heading_sum = 0
   distance_sum = 0
   velocity_sum = 0
   mixed_sum = 0
   timeout_sum = 0
   for key in Tgen_type:
     for sub_key in Tgen_type[key]:
       if sub_key == 'H':
         heading_sum += Tgen_type[key][sub_key]
       if sub_key == 'D':
         distance_sum += Tgen_type[key][sub_key]
       if sub_key == 'V':
         velocity_sum += Tgen_type[key][sub_key]
       if sub_key == 'M':
         mixed_sum += Tgen_type[key][sub_key]
       if sub_key == 'T':
         timeout_sum += Tgen_type[key][sub_key]

   pieChartValues = [velocity_sum, heading_sum, distance_sum, timeout_sum, mixed_sum]
   pieChartLabels = ['Velocity', 'Heading', 'Distance', 'Timeout', 'Mixed']
   textprops = {"fontsize":20} # Font size of text in pie chart
   plt.figure()
   plt.pie(pieChartValues, labels=pieChartLabels, autopct='%1.1f%%', shadow=True, startangle=90, textprops=textprops)

   dstFilePath = os.path.join(dirPath,'GPStraces','PlotsData','PieChart_' + str(heading_threshold) + '_' + str(velocity_threshold) + '.csv')
   with open(dstFilePath, 'w') as OUTfile:
     OUTfile.write('Trigger type,Counter\r\n')
     for label, value in zip(pieChartLabels, pieChartValues):
       OUTfile.write(str(label) + ',' + str(value) + '\r\n')

   # Normalize Tgen_type data
   X_len = 50
   labels = []
   total_sum = 0
   for key in Tgen_type:
     key_sum = 0
     labels.append(key)
     for sub_key in Tgen_type[key]:
       key_sum += Tgen_type[key][sub_key]
     total_sum += key_sum

#   print (Tgen_type)
   for key in Tgen_type:
     key_sum = 0
     for sub_key in Tgen_type[key]:
       key_sum += Tgen_type[key][sub_key]
     pct_value = key_sum / total_sum
#     print (pct_value)
     for sub_key in Tgen_type[key]:
       if key_sum > 0:
         Tgen_type[key][sub_key] /= key_sum
         Tgen_type[key][sub_key] *= pct_value
       else:
         Tgen_type[key][sub_key] = 0
#     print ('---- ', Tgen_type[key])

   sumSamples = 0
   #labels = []
   Y_velocity = []
   Y_heading = []
   Y_distance = []
   Y_mixed = []
   Y_timeout = []
   for key in Tgen_type:
     for sub_key in Tgen_type[key]:
       if sub_key == 'V':
         Y_velocity.append(Tgen_type[key][sub_key])
       elif sub_key == 'H':
         Y_heading.append(Tgen_type[key][sub_key])
       elif sub_key == 'D':
         Y_distance.append(Tgen_type[key][sub_key])
       elif sub_key == 'M':
         Y_mixed.append(Tgen_type[key][sub_key])
       elif sub_key == 'T':
         Y_timeout.append(Tgen_type[key][sub_key])
   
   Y_velocity = np.array(Y_velocity)
   Y_heading = np.array(Y_heading)
   Y_distance = np.array(Y_distance)
   Y_timeout = np.array(Y_timeout)
   Y_mixed = np.array(Y_mixed)

   plt.figure()
   plt.bar(np.arange(1,X_len+1), Y_velocity, label = 'Velocity')
   plt.bar(np.arange(1,X_len+1), Y_heading, bottom=Y_velocity, label = 'Heading')
   plt.bar(np.arange(1,X_len+1), Y_distance, bottom=Y_velocity+Y_heading, label = 'Distance')
   plt.bar(np.arange(1,X_len+1), Y_timeout, bottom=Y_velocity+Y_heading+Y_distance, label = 'Timeout')
   plt.bar(np.arange(1,X_len+1), Y_mixed, bottom=Y_velocity+Y_heading+Y_distance+Y_timeout, label = 'Mixed')
 
   plt.ylim(0,1.01)
   plt.yticks(fontsize=24)
   plt.xticks(np.arange(1,X_len+1),labels,rotation=90,fontsize=16)
   plt.xlabel("$T_{GenCAM}$ [ms]",fontsize=24)
   plt.ylabel("$P(T_{GenCAM}=x)$",fontsize=24)
   plt.legend(fontsize=24)

   dstFilePath = os.path.join(dirPath,'GPStraces','PlotsData','PMF_' + str(heading_threshold) + '_' + str(velocity_threshold) + '.csv')
   with open(dstFilePath, 'w') as OUTfile:
     OUTfile.write('TgenCAM,Velocity,Heading,Distance,Timeout,Mixed\r\n')
     for X, Y_vel, Y_head, Y_dist, Y_time, Y_mix in zip(np.arange(1,X_len+1), Y_velocity, Y_heading, Y_distance, Y_timeout, Y_mixed):
       OUTfile.write(str(int(X*100)) + ',' + str(round(Y_vel,4)) + ',' + str(round(Y_head,4)) + ',' + str(round(Y_dist,4)) + ',' + str(round(Y_time,4)) + ',' + str(round(Y_mix,4)) + '\r\n')


   # Plot a VAM/CAM trace   
#   plt.figure()
#   plt.grid()
#   plt.plot(range(len(TgenValues)), TgenValues,'-o')
#   plt.xticks(fontsize=20)
#   plt.yticks(np.arange(0,5000,100),fontsize=20)
#   plt.xlabel('Sample index',fontsize=20)
#   plt.ylabel('$T_{\mathit{GenVam}}$ [ms]',rotation=90,fontsize=20)
   
   print ('Average Tgen = {} ms'.format(round(np.mean(TgenValues),2)))
   print ('Total number of GNSS points:',totalNumPoints)

   if(pieChartValues[4] != 0):
    print ('Fraction of heading triggers in mixed triggers:',round(Mixed_Heading/pieChartValues[4],4))

   plt.show()
   
   """
   dirPath  = '/home/luca/Desktop/Motorcycle_Quectel_Data'
   filesList = os.listdir(dirPath)

#   print (filesList)

   filesList_tmp = []
   for fileName in filesList:
     if len(fileName.split(".")) > 1:
       fileType = fileName.split("_")[1]
       if fileName.split(".")[1] == 'txt' and fileType == 'TX':
         filesList_tmp.append(fileName)

   filesList = filesList_tmp

#   print ('')
   print (filesList)


   for fileName in filesList:
     lat_data = []
     lon_data = []
     sample_index = []
     X = []
     Y = []
     last_lat = 100.00000
     last_lon = 100.00000
     print ('Opening',fileName)
     data = pd.read_csv(dirPath + '/' + fileName)
     filtered_data = tuple(zip(data['latitude'], data['longitude'], data['heading'], data['velocity'], data['seq_num']))
     elem_counter = 0
     for elem in filtered_data:
       if elem_counter == 5:
         lat_data.append(elem[0])
         lon_data.append(elem[1])
         X.append(0)
         Y.append(0)
         sample_index.append(elem_counter)
         last_lat = elem[0]
         last_lon = elem[1]

       elif elem_counter > 5:
         numPoints = len(X)
         distance = haversine(last_lon, last_lat, elem[1], elem[0]) * 1000

         diff_lon = last_lon-elem[1]
         diff_lat = last_lat-elem[0]

         last_lat = elem[0]
         last_lon = elem[1]


         lastX = X[numPoints-1]
         lastY = Y[numPoints-1]
  
         if distance < 1000:   
           lat_data.append(elem[0])
           lon_data.append(elem[1])
           X.append(lastX+diff_lon)
           Y.append(lastY+diff_lat)
           sample_index.append(elem_counter)

    #   input()
       elem_counter += 1
     with open('/home/luca/Desktop/GPS_DATA.csv','w') as DSTfile:
       DSTfile.write('latitude,longitude,index\r\n')
       for lat, lon, index in zip(lat_data,lon_data,sample_index):
         DSTfile.write(str(lat) + ',' + str(lon) + ',' + str(index) + '\r\n')

     plt.figure()
     plt.scatter(X,Y)
     plt.show()
   """         

if __name__ == "__main__":
   main()
