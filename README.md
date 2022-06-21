# CAM-VAM-dataset
This dataset contains the CAM and VAM traces collected at the University of Modena and Reggio Emilia

Each folder consists of files starting with "CAM_*" and "VAM_*", corresponding to files containing the
actual CAM/VAM traces generated at run-time, or with "LOG_*", corresponding to files containing the GPS traces
used then to generate CAM or VAM in a post-processing phase.

Every "LOG_*" can be parsed with the python3 script, available in the repository as well, named "GenerateCAMVAMtraces.py".
The script converts a GPS LOG file in the corresponding CAM or VAM equivalent trace, tuning the thresholds value properly
for the triggers conditions.
