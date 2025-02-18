# -*- coding: utf-8 -*-
"""
Created on Fri Dec 22 09:12:07 2023

@author: Radke
"""

__name__ = 'Excess_weeks_data'

import numpy as np
import pandas as pd


import os
os.environ["GAMS_DIR"] = "C:/GAMS/45"


import gams
from gams import GamsWorkspace

import warnings
warnings.simplefilter("ignore", UserWarning)






def prepare_parameters(path='../Data/Data.xlsx',scenario=1):
    ws = GamsWorkspace(system_directory="C://GAMS/45", working_directory='../Container')
    
    df = pd.read_excel(path, sheet_name=f'Parameters_{scenario}', skiprows=1, nrows=5, index_col=0)
    conv = df.index.to_list()
    variable_costs_conv = df['vc_c'].to_dict()
    start_up_costs = df['sc'].to_dict()
    cap_conv = df['cap_c'].to_dict()
    must_run_cap = df['must_run'].to_dict()
    ramp_share = df['ramp'].to_dict()
    partial = df['min_part'].to_dict()
    partial_cost = df['plc'].to_dict()
    
    df = pd.read_excel(path, sheet_name=f'Parameters_{scenario}', skiprows=9, nrows=2, index_col=0)
    storage = df.index.to_list()
    power_storage = df['power_s'].to_dict()
    cap_storage = df['cap_s'].to_dict()
    n_storage = df['n'].to_dict()


    df = pd.read_excel(path, sheet_name=f'Parameters_{scenario}', skiprows=15, nrows=6, index_col=0)
    renewables = df.index.to_list()
    vc_renewables = df['vc_r'].to_dict()
    cap_renewables = df['cap_r'].to_dict()    
    
    df = pd.read_excel(path, sheet_name=f'Parameters_{scenario}', skiprows=25, index_col=0)
    cap_solar_undis = df.loc['cap_solar_inflex','Value']
    cap_wind_undis = df.loc['cap_wind_on_inflex','Value']
    shift_max = df.loc['max_load_shift','Value']
    anc_min = df.loc['ancillary_must_run','Value']
    
    db = ws.add_database()
    
    c = db.add_set('c', 1, 'Conventionals')
    for i in conv:
        c.add_record(i)
        
    r = db.add_set('r',1,'Dispatchable renewables')
    for i in renewables:
        r.add_record(i)
        
    s = db.add_set('s',1,'Storages')
    for i in storage:
        s.add_record(i)
        
    vc_c = db.add_parameter_dc('vc_c', [c], 'Variable costs conventionals')
    for i in conv:
        vc_c.add_record(i).value = variable_costs_conv[i]
        
    sc = db.add_parameter_dc('sc', [c], 'Start-up costs conventionals')
    for i in conv:
        sc.add_record(i).value = start_up_costs[i]
        
    must_run = db.add_parameter_dc('must_run', [c], 'Must-run conventionals')
    for i in conv:
        must_run.add_record(i).value = must_run_cap[i]
        
    ramp = db.add_parameter_dc('ramp', [c], 'Ramp-up conventionals')
    for i in conv:
        ramp.add_record(i).value = ramp_share[i]
        
    min_run = db.add_parameter_dc('min_run', [c], 'Minimum partial load')
    for i in conv:
        min_run.add_record(i).value = partial[i]
        
    plc = db.add_parameter_dc('plc', [c], 'Partial load cost factor')
    for i in conv:
        plc.add_record(i).value = partial_cost[i]
        
    cap_c = db.add_parameter_dc('cap_c', [c], 'Inst. capacity conventionals')
    for i in conv:
        cap_c.add_record(i).value = cap_conv[i]
        
    cap_r = db.add_parameter_dc('cap_r', [r], 'Inst. capacity dispatchable renewables')
    for i in renewables:
        cap_r.add_record(i).value = cap_renewables[i]
        
    vc_r = db.add_parameter_dc('vc_r', [r], 'Variable costs dispatchable renewables')
    for i in renewables:
        vc_r.add_record(i).value = vc_renewables[i]
        
    cap_s = db.add_parameter_dc('cap_s', [s], 'Storage capacity')
    for i in storage:
        cap_s.add_record(i).value = cap_storage[i]
        
    power_s = db.add_parameter_dc('power_s', [s], 'Storage power')
    for i in storage:
        power_s.add_record(i).value = power_storage[i]
        
    n = db.add_parameter_dc('n', [s], 'Storage efficiency')
    for i in storage:
        n.add_record(i).value = n_storage[i]
        
    cap_solar_inflex = db.add_parameter('cap_solar_inflex', 0, 'Inflexible solar capacity').add_record().value = int(cap_solar_undis)
    cap_wind_on_inflex = db.add_parameter('cap_wind_on_inflex', 0, 'Inflexible solar capacity').add_record().value = int(cap_wind_undis)
    load_shift_max = db.add_parameter('load_shift_max', 0, 'Max shiftable load').add_record().value = int(shift_max)
    anc_run = db.add_parameter('anc_run', 0, 'Ancillary services must-run').add_record().value = int(anc_min)
    
    db.export("../Data/parameters.gdx")
    
    print('Parameter initialised')



def prepare_data(start=4345, duration=168, path='../Data/Data.xlsx', scenario=1):
    ws = GamsWorkspace(system_directory="C://GAMS/45", working_directory='../Container')
    
    df = pd.read_excel(path, sheet_name=f'Parameters_{scenario}', skiprows=15, nrows=6, index_col=0)
    renewables = df.index.to_list()
    
    df = pd.read_excel(path, sheet_name=f'Parameters_{scenario}', skiprows=1, nrows=5, index_col=0)
    conv = df.index.to_list()
    
    df = pd.read_excel(path, sheet_name=f'Parameters_{scenario}', skiprows=9, nrows=2, index_col=0)
    storage = df.index.to_list()
    
    df = pd.read_excel(path, sheet_name=f'Parameters_{scenario}', skiprows=25, index_col=0)
    total_demand = df.loc['total demand','Value']*1_000_000
    
    
    df = pd.read_excel(path, sheet_name='Hours_2', index_col=0)
    
    ### select a time slice of data
    time_slice = df.loc[start:start+duration-1]
    
    hours = time_slice.index.to_list()
    demand = (time_slice['dem']*total_demand).round(2).to_dict()
    exp = time_slice.Export.to_dict()
    af_s = time_slice[renewables]
    
    db = ws.add_database()
    
    t = db.add_set('t', 1, 'Hours')
    for i in hours:
        t.add_record(str(i))
              
    r = db.add_set('r',1,'Dispatchable renewables')
    for i in renewables:
        r.add_record(i)
        
    s = db.add_set('s',1,'Storages')
    for i in storage:
        s.add_record(i)
        
    c = db.add_set('c', 1, 'Conventionals')
    for i in conv:
        c.add_record(i)
    
    dem = db.add_parameter_dc('dem', [t], 'Latent demand')
    for i in hours:
        dem.add_record(str(i)).value = demand[i]
        
    export = db.add_parameter_dc('export', [t], 'Net export')
    for i in hours:
        export.add_record(str(i)).value = exp[i]
    
    af = db.add_parameter_dc('af', [t,r], 'Availability renewable energy sources')
    for i in hours:
        for y in renewables:
            af.add_record([str(i),y]).value = af_s.loc[i,y]
            

            
    db.export("../Data/data.gdx")
    print('Data initialised')

    
    
    
   
    




