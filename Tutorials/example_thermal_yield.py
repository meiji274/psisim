from psisim import telescope,instrument,observation,spectrum,universe,plots
import numpy as np
import matplotlib.pylab as plt

import time

tmt = telescope.TMT()
psi_red = instrument.PSI_Red()
psi_red.set_observing_mode(3600,2,'M',10, np.linspace(4.2,4.8,3)) #60s, 40 exposures,z-band, R of 10

exosims_config_filename = "forBruceandDimitri_EXOCAT1.json" #Some filename here
uni = universe.ExoSims_Universe(exosims_config_filename)
uni.simulate_EXOSIMS_Universe()

planet_table = uni.planets
planet_table = planet_table[np.where(planet_table['PlanetMass'] > 10)]
n_planets = len(planet_table)

planet_types = []
planet_spectra = []
planet_ages = []

n_planets_now = 100
rand_planets = np.random.randint(0, n_planets, n_planets_now)

########### Model spectrum wavelength choice #############
# We're going to generate a model spectrum at a resolution twice the 
# requested resolution
intermediate_R = psi_red.current_R*2
#Choose the model wavelength range to be just a little bigger than 
#the observation wavelengths
model_wv_low = 0.9*np.min(psi_red.current_wvs) 
model_wv_high = 1.1*np.max(psi_red.current_wvs)

#Figure out a good wavelength spacing for the model
wv_c = 0.5*(model_wv_low+model_wv_high) #Central wavelength of the model
dwv_c = wv_c/intermediate_R #The delta_lambda at the central wavelength
#The number of wavelengths to generate. Divide by two for nyquist in the d_wv. 
#Multiply the final number by 2 just to be safe.
n_model_wv = int((model_wv_high-model_wv_low)/(dwv_c/2))*2
#Generate the model wavelenths
model_wvs = np.linspace(model_wv_low, model_wv_high, n_model_wv) #Choose some wavelengths

print("\n Starting to generate planet spectra")
for planet in planet_table[rand_planets]:
    #INSERT PLANET SELECTION RULES HERE
    planet_type = "Gas"
    planet_types.append(planet_type)

    age = np.random.random() * 5e9 # between 0 and 5 Gyr
    planet_ages.append(age)

    time1 = time.time()
	#Generate the spectrum and downsample to intermediate resolution
    atmospheric_parameters = age, 'M', True
    planet_spectrum = spectrum.simulate_spectrum(planet, model_wvs, intermediate_R, atmospheric_parameters, package='bex-cooling')
    planet_spectra.append(planet_spectrum)
    
    time2 = time.time()
    print('Spectrum took {0:.3f} s'.format((time2-time1)))

print("Done generating planet spectra")
print("\n Starting to simulate observations")

post_processing_gain=10
sim_F_lambda, sim_F_lambda_errs,sim_F_lambda_stellar, noise_components = observation.simulate_observation_set(tmt, psi_red,
	planet_table[rand_planets], planet_spectra, model_wvs, intermediate_R, inject_noise=False,
	post_processing_gain=post_processing_gain,return_noise_components=True)

speckle_noises = np.array([s[0] for s in noise_components])
photon_noises = np.array([s[3] for s in noise_components])

flux_ratios = sim_F_lambda/sim_F_lambda_stellar
detection_limits = sim_F_lambda_errs/sim_F_lambda_stellar
snrs = sim_F_lambda/sim_F_lambda_errs

detected = psi_red.detect_planets(planet_table[rand_planets],snrs,tmt)

#Choose which wavelength you want to plot the detections at:
wv_index = 1
fig, ax = plots.plot_detected_planet_contrasts(planet_table[rand_planets],wv_index,
	detected,flux_ratios,psi_red,tmt,ymin=1e-13,alt_data=5*detection_limits,alt_label=r"5-$\sigma$ Detection Limits", show=False)

#The user can now adjust the plot as they see fit. 
#e.g. Annotate the plot
ax.text(4e-2,1e-5,"Planets detected: {}".format(len(np.where(detected[:,wv_index])[0])),color='k')
ax.text(4e-2,0.5e-5,"Planets not detected: {}".format(len(np.where(~detected[:,wv_index])[0])),color='k')
ax.text(4e-2,0.25e-5,"Post-processing gain: {}".format(post_processing_gain),color='k')



plt.show()

import pdb; pdb.set_trace()