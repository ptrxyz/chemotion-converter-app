DATA_TYPES = (
    'INFRARED SPECTRUM',
    'RAMAN SPECTRUM',
    'INFRARED PEAK TABLE',
    'INFRARED INTERFEROGRAM',
    'INFRARED TRANSFERED SPECTRUM',
    'NMR FID',
    'NMR SPECTRUM',
    'NMR PEAK TABLE',
    'NMP PEAK ASSIGNMENTS',
    'MASS SPECTRUM',
    'CONTINUOUS MASS SPECTRUM',
    'THERMOGRAVIMETRIC ANALYSIS',
    'TENSIOMETRY',
    'UV-VIS',
    'HPLC UV-VIS',
    'GEL PERMEATION CHROMATOGRAPHY',
    'CIRCULAR DICHROISM SPECTROSCOPY',
    'CYCLIC VOLTAMMETRY',
    'X-RAY DIFFRACTION',
    'AIF' # Must be extened
    'SINGLE CRYSTAL X-RAY DIFFRACTION',
    'SORPTION-DESORPTION MEASUREMENT',
    'SIZE EXCLUSION CHROMATOGRAPHY',
)

DATA_CLASSES = (
    'XYPOINTS',
    'XYDATA',
    'PEAK TABLE',
    'NTUPLES',
)

XUNITS = (
    'p/p0', # Normalaized dimension
    'kPa',
    '%',
    '1/CM',
    '2Theta',
    'DEGREES CELSIUS',
    'G/MOL',
    'HZ',
    'KILOGRAM',
    'MICROMETERS',
    'MILIMETERS',
    'MILLILITERS',
    'MINUTES',
    'm/z',
    'MOLECULAR MASS / DA',
    'NANOMETERS',
    'SECONDS',
    'Voltage vs Ref',
    'wavelength (nm)'
)

YUNITS = (
    'ml/g',
    'mmol/g',
    'ABSORBANCE',
    'Ampere',
    'ARBITRARY UNITS',
    'COUNTS',
    'DERIVATIVE WEIGHT',
    'Intensity',
    'KUBELKA-MUNK',
    'mAU',
    'N/M2',
    'Newton',
    'REFLECTANCE',
    'SIGNAL',
    'TRANSMITTANCE',
    'WEIGHT',
    'ellipticity (deg cm2/dmol)',
    'Molar Extinction (cm2/mmol) '
)

OPTIONS = {
    'DATA TYPE': DATA_TYPES,
    'DATA CLASS': DATA_CLASSES,
    'XUNITS': XUNITS,
    'YUNITS': YUNITS,
}
