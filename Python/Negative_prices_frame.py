# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 14:31:19 2024

@author: Radke
"""

__name__ = 'Excess_frame'

import warnings
warnings.simplefilter("ignore", UserWarning)

#import gdxpds



import time
import pickle
import pandas as pd

#import gams
from gams import GamsWorkspace
from gams import transfer as gt


from Excess_weeks_data import prepare_parameters
from Excess_weeks_data import prepare_data

tic = time.time()

result_path = '../Results/result.gdx'
ws = GamsWorkspace(system_directory="C://GAMS/45", working_directory='../Container')

result_frame = pd.DataFrame()
result_df = pd.DataFrame()
result_data = {}





scenario=[1,2,3,4]

## 52. week is one day longer so 192 hours
for s in [1,2,3,4]: #scenario: 
    print('Starting scenario',s)
    
    prepare_parameters(scenario=s)
    
    result_data[s]={}
    
    result_data[s]['SOC'] = pd.DataFrame()
    result_data[s]['RUN'] = pd.DataFrame()
    result_data[s]['Variables'] = pd.DataFrame()
    result_data[s]['Marginal'] = pd.DataFrame()
    result_data[s]['Start_Up'] = pd.DataFrame()
    
    for w in range(1,53,1): 
        if w < 52:
            start_hour=(w-1)*168+1
            prepare_data(start=start_hour,duration=168,scenario=s)
        else:
            start_hour=(w-1)*168+1
            prepare_data(start=start_hour,duration=192,scenario=s)
    
        
        
        
        print('Starting week',w,'in Scenario:',s)
        
        job_general=ws.add_job_from_file(file_name ='../Negative_prices.gms')
        job_general.run()
        
           
        result = gt.Container(result_path, system_directory="C://GAMS/45",)
        
            
          
        result_data[s]['SOC'] = pd.concat([result_data[s]['SOC'], result.data['SOC'].records.pivot(index='t', columns='s', values='level')])
        result_data[s]['RUN'] = pd.concat([result_data[s]['RUN'], result.data['RUN'].records.pivot(index='t', columns='c', values='level')])
        
        df = pd.DataFrame(index=result.data['t'].records['t'])
        df['demand'] = result.data['dem'].records.set_index('t')
        df['load_shift'] = result.data['load_shift'].records.set_index('t')[['level']]
        df['export'] = result.data['export'].records.set_index('t')
        df['CURT'] = result.data['CURT'].records.set_index('t')[['level']]
        df['Solar_FIT'] = (result.data['af'].records.pivot(index='t', columns='r', values='value')[['Solar']] * result.data['cap_solar_inflex'].records.loc[0,'value']).fillna(0)
        df['Wind_FIT'] = (result.data['af'].records.pivot(index='t', columns='r', values='value')[['Wind_on']] * result.data['cap_wind_on_inflex'].records.loc[0,'value']).fillna(0)
        
        df = df.merge(result.data['GEN'].records.pivot(index='t', columns='c', values='level'), left_index = True, right_index=True)
        df = df.merge(result.data['RES'].records.pivot(index='t', columns='r', values='level'), left_index = True, right_index=True)
        df = df.merge(result.data['STORAGE'].records.pivot(index='t', columns='s', values='level'), left_index = True, right_index=True)
        
           
        df = df.round(2)
        
        
        
        result_data[s]['Variables'] = pd.concat([result_data[s]['Variables'], df])
        
        #result_data[w]['Cost'] = result.data['COST'].records.loc[0,'level']
        result_data[s]['Start_Up'] = pd.concat([result_data[s]['Start_Up'], result.data['START_UP'].records.pivot(index='t', columns='c', values='level')])
        
        df = result.data['res_equality'].records[['uni','marginal']].set_index('uni')
        df.index.names = ['t']
        df['marginal'] = -df['marginal'].round(2)
        
        result_data[s]['Marginal'] = pd.concat([result_data[s]['Marginal'], df])
        
        result_data[s]['Sets'] = {}
        for i in ['t','c','r','s']:
            result_data[s]['Sets'][i] = result.data[i].records[i]
        
        print('Week',w,'finished')
        
    
  
    result_data[s]['SOC'].index = result_data[s]['SOC'].index.astype('int')
    result_data[s]['RUN'].index = result_data[s]['RUN'].index.astype('int')
    result_data[s]['Variables'].index = result_data[s]['Variables'].index.astype('int')
    result_data[s]['Marginal'].index = result_data[s]['Marginal'].index.astype('int')
    
    result_data[s]['SOC'] = result_data[s]['SOC'].sort_index()
    result_data[s]['RUN'] = result_data[s]['RUN'].sort_index()
    result_data[s]['Variables'] = result_data[s]['Variables'].sort_index()
    result_data[s]['Marginal'] = result_data[s]['Marginal'].sort_index()
    
    print('Scenario',s,'finished')

  
with open('C:/Users/HP_Radke/Documents/Shared_Data/Results/eem25/weeks/results.pickle', 'wb') as handle:
    pickle.dump(result_data, handle, protocol=pickle.HIGHEST_PROTOCOL)   
    
    

print('Job finished')
print(round((time.time() - tic)/60, 2) , ' min elapsed', sep='')