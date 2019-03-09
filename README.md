# GNSS data evaluate

## Instruction
This program can autorun or be maunally executed. GNSS data evaluation include position and orbit.

## Requirement
**python3** and **numpy**, **matplotlib**, **pandas**, **basemap**   

Note：  
1. windows install **Anaconda** by recommending, it will install **numpy**, **matplotlib**, **pandas**  
2. **basemap** should be installed manually, use command `conda install basemap`

## Autorun
1. Firstly, configure **autorun.ini**  
2. change directory to **GNSSEvaluate**, execute `python main.py`  

## Manual
1. Firstly, configure **manul.ini**  
2. change directory to **GNSSEvaluate**, execute `python main.py args`  
		Args:   
					 -A: execute all module  
					 -R: zdpos report  
					 --ENU: plot ENU  
					 --HV: plot horizontal and vertical errors  
					 --HVM: plot mean of horizontal and vertical errors  
					 --SAT: plot satellite number  
					 --IODE: plot satellite iode  
					 --ORBITC: plot orbit and clock errors  
