

$eolcom #
$onText


$offText



*#####################     Declaring Sets   #################################
Sets
        t           times (hours)
        c           conventional generators
        r           dispatchable renewable generators
        s           storage technologies PHP and battery
         
;




*#####################     Declaring Parameters   #############################
Parameters
        vc_c(c)     variable cost for conventional generators in € per MWh
        vc_r(r)     variable cost for dispatchable renewables in € per MWh
        sc(c)       start up costs in € per MW
         
        dem(t)      latent demand in hour t in MWh
        export(t)   Net exports
        load_shift_max  maximum for load shifting
        anc_run     Ancillary services  must-run
        
        
        cap_s(s)    storage capacity of technoloy s in full-load hours
        power_s(s)  max storage power of s in MW
        n(s)        efficiency of technoloy s
        
        
        
        must_run(c) must-run capacity in MW
        ramp(c)     maximum ramp in % of installed capacity
        cap_c(c)    installed capacity of conventionals
        cap_r(r)    installed capacity of dispatchable renewables
        min_run(c)  minimum partial_load
        plc(c)      partial load cost factor
        
        af(t,r)     availability factor for renewables
        
         
         
         
         
         
;

Scalars
        cap_solar_inflex       installed capacity of un-dispatchable solar plants
        cap_wind_on_inflex
;


*#######################  Upload from data.gdx ##############################



*3.Read the elements
$gdxin ../Data/parameters.gdx # ../
$Load c, r, s
$Load vc_c, vc_r, sc, cap_s, power_s, n, must_run, ramp, cap_c, cap_r, cap_solar_inflex, cap_wind_on_inflex, load_shift_max, anc_run, min_run, plc
$gdxin

$gdxin ../Data/data.gdx # ../
$Load t 
$Load dem, af, export
$gdxin



*Display data to see that everything is uploaded correctly
#Display must_run;



#$stop
*#####################     Declaring Variables   #############################

Variable
        COST        total cost of supply
        LOAD_SHIFT(t) shifted load from hour t
        STORAGE(t,s) power flow into storages in hour t
;

Positive Variables
        
        
        GEN(t,c)    conventional generation in hour t
        RES(t,r)    generation from dispatchable renewables in hour t
        CURT(t)     curtailment in hour t
        
        LOAD_STORAGE(t)
        
        START_UP(t,c) started conventional capacity in hour t
        RUN(t,c)    running conventional capacity in hour t
        SOC(t,s)    state-of-charge of storage technology s
        
        
                    
;



       

*#####################     Declaring Equations   #############################
Equations
        TC          Total costs
        
        res_equality quality of demand and supply
        
        
        res_shift1   load shifting
        res_shift2
        res_shift3
        res_shift4
        res_shift5
        
        res_inst
        res_must_run
        res_anc
        res_start_up
        res_run
        
        res_ramp1
        res_ramp2
        res_min_run
        
        res_inst_ren
        
        res_soc
        res_power1
        res_power2
        res_storage
        



;


## Total cost

TC..                COST =E= sum(t, CURT(t)*(500) 
                                  +  sum(c, GEN(t,c)*vc_c(c) + START_UP(t,c)*sc(c) + vc_c(c)*plc(c)*(RUN(t,c)-GEN(t,c)) ) # *(1+plc(c)*(1-(GEN(t,c)+1)/(RUN(t,c)+1)))
                                  +  sum(r, RES(t,r)*vc_r(r))
                                )
                                
;

## Equality of demand and supply

res_equality(t)..   dem(t) + sum(s, STORAGE(t,s)) + CURT(t) + LOAD_SHIFT(t)   =e= # + export(t) 
                    sum(c, GEN(t,c)) + sum(r, RES(t,r))  + cap_solar_inflex*af(t,'Solar') *0.95 + cap_wind_on_inflex*af(t,'Wind_on')*0.95                         
;


## Load shifting

res_shift1..        sum(t, LOAD_SHIFT(t)) =e= 0
;

res_shift2(t)..     LOAD_SHIFT(t) =l= load_shift_max
;

res_shift3(t)..     LOAD_SHIFT(t) =g= -load_shift_max
;

res_shift4(t)..     LOAD_STORAGE(t) - LOAD_STORAGE(t-1) =e= LOAD_SHIFT(t)
;

res_shift5(t)..     LOAD_STORAGE(t) =l= load_shift_max *3
;

## Conventional generators

res_inst(t,c)..     RUN(t,c) =l= cap_c(c)
;

res_must_run(t,c).. GEN(t,c) =g= must_run(c)
;

res_anc(t)..        sum(c, GEN(t,c)) =g= anc_run
;

res_start_up(t,c).. START_UP(t,c) =g= RUN(t,c) - RUN(t-1,c)
;

res_run(t,c)..      GEN(t,c) =l= RUN(t,c)
;


res_ramp1(t,c)..    (GEN(t-1,c) - GEN(t,c)) =l= ramp(c)*RUN(t,c)
;

res_ramp2(t,c)..    (GEN(t,c) - GEN(t-1,c)) =l= ramp(c)*RUN(t,c)
;

res_min_run(t,c)..  GEN(t,c) =g= min_run(c) * RUN(t,c)
;

## Dispatchable renewable generators

res_inst_ren(t,r).. RES(t,r) =l= cap_r(r)*af(t,r)*0.95
;

## Storage

res_soc(t,s)..      SOC(t,s) =l= 1
;

res_power1(t,s)..   STORAGE(t,s) =l= power_s(s)
;

res_power2(t,s)..   STORAGE(t,s) =g= -power_s(s)
;

res_storage(t,s)..  (SOC(t,s) - SOC(t-1,s))*power_s(s)*cap_s(s) =e= STORAGE(t,s)*n(s)
;


#$stop

#########################    Solving the stochastic model    ##############################
model dispatch
/  all/
;
#option solver = CPLEX #IPOPT #PathNLP
#;

solve dispatch using LP minimzing COST
;




#########################    Write result data    ##############################

$onEps

*2. Put the data in a .gdx file
execute_unload '../Results/result.gdx' # ../
;
$offEps