const MATERIALS = [
  { value: "any", label: "Any material" },
  { value: "aluminum", label: "Aluminum" },
  { value: "steel", label: "Steel" },
  { value: "copper", label: "Copper / Brass" },
  { value: "glass", label: "Glass" },
  { value: "ceramic", label: "Ceramic" },
  { value: "wood", label: "Wood" },
  { value: "mdf", label: "MDF / Particleboard" },
  { value: "paper", label: "Paper / Cardboard" },
  { value: "fabric", label: "Fabric / Canvas" },
  { value: "leather", label: "Leather" },
  { value: "abs", label: "ABS" },
  { value: "pvc", label: "PVC" },
  { value: "cpvc", label: "CPVC" },
  { value: "acrylic", label: "Acrylic / PMMA" },
  { value: "polycarbonate", label: "Polycarbonate" },
  { value: "petg", label: "PETG" },
  { value: "polystyrene", label: "Polystyrene / HIPS" },
  { value: "rubber", label: "Rubber / EPDM" },
  { value: "siliconeRubber", label: "Silicone Rubber" },
  { value: "hdpe", label: "HDPE / Polyethylene" },
  { value: "concrete", label: "Concrete / Masonry" },
  { value: "fr4", label: "FR4 / PCB" },
  { value: "carbonFiber", label: "Carbon Fiber" },
];

const MATERIAL_KEYS = MATERIALS.filter((material) => material.value !== "any").map(
  (material) => material.value,
);

const MATERIAL_LABELS = Object.fromEntries(
  MATERIALS.map((material) => [material.value, material.label]),
);

const VISCOSITY_LABELS = {
  wicking: "Wicking",
  low: "Low",
  medium: "Medium",
  high: "High",
  "very-high": "Very high",
};

const ENVIRONMENT_LABELS = {
  humidity: "humidity",
  fuel: "fuel and oil splash",
  immersion: "immersion",
};

const STRESS_LABELS = {
  shear: "Shear",
  peel: "Peel",
  impact: "Impact",
};

const APPLICATION_OPTIONS = [
  { value: "any", label: "Any application" },
  { value: "structural-bonding", label: "Structural bonding" },
  { value: "instant-bonding", label: "Instant bonding / super glue" },
  { value: "optical-bonding", label: "Optical / clear bonding" },
  { value: "threadlocking", label: "Threadlocking" },
  { value: "retaining", label: "Retaining compounds" },
  { value: "sealing-gasketing", label: "Sealing / gasketing" },
  { value: "potting-thermal", label: "Potting / thermal management" },
  { value: "contact-lamination", label: "Contact / laminating" },
  { value: "construction", label: "Construction / masonry" },
  { value: "spray-mounting", label: "Spray mounting" },
  { value: "hot-melt-assembly", label: "Hot melt assembly" },
  { value: "solvent-welding", label: "Solvent welding" },
  { value: "wood-paper-fabric", label: "Wood / paper / fabric" },
  { value: "plastic-repair", label: "Plastic repair / LSE plastics" },
  { value: "general-repair", label: "General repair" },
];

const APPLICATION_LABELS = Object.fromEntries(
  APPLICATION_OPTIONS.map((option) => [option.value, option.label]),
);

const PAGE_SIZE = 25;
const REFERENCE_PAGE_SIZE = 50;

const PROFILE_APPLICATION_TAGS = {
  toughenedEpoxy: ["structural-bonding"],
  flexibleEpoxy: ["structural-bonding"],
  clearEpoxy: ["structural-bonding"],
  structuralAcrylic: ["structural-bonding"],
  structuralPolyurethane: ["structural-bonding"],
  mmaPlasticWelder: ["plastic-repair", "structural-bonding"],
  thinCA: ["instant-bonding"],
  gelCA: ["instant-bonding"],
  hybridCA: ["instant-bonding", "plastic-repair"],
  uvOptical: ["optical-bonding"],
  uvAcrylate: ["optical-bonding"],
  rtvSilicone: ["sealing-gasketing"],
  siliconeRubberAdhesive: ["sealing-gasketing"],
  polyurethaneSealant: ["sealing-gasketing"],
  msPolymerSealant: ["sealing-gasketing"],
  anaerobicThreadlocker: ["threadlocking"],
  anaerobicRetainer: ["retaining"],
  foamTape: ["structural-bonding"],
  contactCement: ["contact-lamination"],
  pvaWood: ["wood-paper-fabric"],
  hotMelt: ["hot-melt-assembly"],
  sprayAdhesive: ["spray-mounting"],
  thermalEpoxy: ["potting-thermal"],
  solventAcrylic: ["solvent-welding"],
  solventPVC: ["solvent-welding"],
  solventCPVC: ["solvent-welding"],
  solventABSStyrene: ["solvent-welding"],
  solventPolycarbonate: ["solvent-welding"],
  solventMultiPlastic: ["solvent-welding"],
  constructionAdhesive: ["construction"],
  industrialClear: ["general-repair"],
  fabricAdhesive: ["wood-paper-fabric"],
  craftPva: ["wood-paper-fabric"],
};

const CLARITY_RANK = {
  opaque: 0,
  translucent: 1,
  transparent: 2,
  "optically-clear": 3,
};

const buildRatings = (overrides, fallback = 0) =>
  Object.fromEntries(MATERIAL_KEYS.map((key) => [key, overrides[key] ?? fallback]));

const buildEnvironment = (overrides, fallback = 0.45) => ({
  humidity: fallback,
  fuel: fallback,
  immersion: fallback,
  ...overrides,
});

const buildStress = (overrides, fallback = 4) => ({
  shear: fallback,
  peel: fallback,
  impact: fallback,
  ...overrides,
});

const hasOwn = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
const hasCatalogValue = (value) => value !== undefined && value !== null;
const dedupeList = (values) => Array.from(new Set(values.filter(Boolean)));

const OBSERVED_TDS_FIELDS = [
  "viscosityValue",
  "viscosityUnit",
  "viscosityRangeMpaS",
  "viscosityByShearRateMpaS",
  "electricalBehavior",
  "volumeResistivity",
  "volumeResistivityOhmM",
  "surfaceResistivity",
  "surfaceResistivityOhm",
  "surfaceResistanceOhm",
  "surfaceInsulationResistanceOhm",
  "connectionResistance",
  "connectionResistanceOhm",
  "connectionResistanceProfilesOhm",
  "electricalResistanceOhm",
  "coatingResistanceOhm",
  "insulationResistance",
  "insulationResistanceOhm",
  "insulationResistanceProfilesOhm",
  "volumeResistivityOhmCm",
  "volumeResistivityRangeOhmM",
  "volumeResistivityRangeOhmCm",
  "dielectricConstant",
  "dielectricConstantRange",
  "dissipationFactor",
  "dielectricBreakdown",
  "dielectricBreakdownVPerMil",
  "dielectricBreakdownKVPerMm",
  "dielectricBreakdownRangeKVPerMm",
  "vickersHardness",
  "coefficientThermalExpansionPerC",
  "curingSchedules",
  "storageCondition",
  "minimumNozzleDiameterMm",
  "tensileStrength",
  "tensileStrengthPsi",
  "tensileStrengthRangePsi",
  "tensileStrengthMPa",
  "tensileStrengthRangeMPa",
  "tensileModulusMPa",
  "tensileModulusRangeMPa",
  "tanModulusMPa",
  "elongation",
  "elongationPct",
  "elongationRangePct",
  "compressionSetPct",
  "hardnessValue",
  "hardnessRange",
  "hardnessScale",
  "hardnessValueAlt",
  "hardnessScaleAlt",
  "compressiveStrengthMPa",
  "peelStrength",
  "peelStrengthNPerM",
  "peelStrengthNPer25Mm",
  "peelStrengthGPerIn",
  "peelStrengthProfilesNPerM",
  "peelAdhesionProfilesNPer100Mm",
  "loopTackGPerIn",
  "tearStrength",
  "tearStrengthNPerMm",
  "chipBondStrength",
  "chipBondStrengthMPa",
  "fittedBondStrengthMPa",
  "cureDepth",
  "cureDepthMm",
  "depthCurabilityMm",
  "cureRateMmPer24h",
  "cureWavelengthNm",
  "uvFixtureProfiles",
  "uvGapCureProfiles",
  "fullCureFixtureMultiplier",
  "refractiveIndex",
  "refractiveIndexRange",
  "tackFreeTime",
  "tackFreeTimeMinutes",
  "tackFreeTimeRangeMinutes",
  "machinableAfterHours",
  "skinTimeMinutes",
  "airSetTimeMinutes",
  "dryTimeMinutes",
  "recoatTimeMinutes",
  "cureProfiles",
  "mixRatio",
  "mixingTimeSeconds",
  "workableTimeRangeMinutes",
  "thixotropicIndex",
  "gelTimeMinutes",
  "gelTimeRangeMinutes",
  "demoldCureProfiles",
  "mixPouchMixTimeSeconds",
  "setTimeMinutes",
  "setTimeRangeMinutes",
  "serviceCureMinutes",
  "setTimeRangeSeconds",
  "fullStrengthTimeHours",
  "potLifeRangeMinutes",
  "potLifeMonths",
  "potLifeConditions",
  "processingTimeHours",
  "conditioningTimeHours",
  "workingLifeDays",
  "fixtureTimeRangeMinutes",
  "handlingTimeRangeMinutes",
  "handlingTimeMinutes",
  "workingStrengthMinutes",
  "workingStrengthHours",
  "workingStrengthProfiles",
  "timeToStructuralStrengthMinutes",
  "workingTimeMinutes",
  "openAssemblyTimeRangeMinutes",
  "totalAssemblyTimeRangeMinutes",
  "adhesivenessKeepingTimeRangeMinutes",
  "fullCureMinutes",
  "fullCureHours",
  "fullCureProfiles",
  "fullDryThroughHours",
  "fullDryThroughDays",
  "cureIntensityMwCm2",
  "peakIrradianceWCm2",
  "uvProjectionDistanceCm",
  "cureTimeSeconds",
  "curingTemperatureMinC",
  "curingTemperatureMaxC",
  "cureCondition",
  "recommendedCureConditions",
  "setTimeSeconds",
  "setTimeProfilesSeconds",
  "settingTimeMinutes",
  "settingTimeSeconds",
  "standardDryingCondition",
  "dryingProfiles",
  "printProfiles",
  "dryFilmThicknessMicron",
  "bondingPitchMicron",
  "minimumScrewDiameter",
  "minimumNutDiameter",
  "threadProjectionRatePct",
  "heatResistanceC",
  "nonVolatileContentPct",
  "heatingResidualPct",
  "solventContents",
  "byProductGas",
  "lossOnHeatingPct",
  "ph",
  "appearance",
  "coatingFilmColor",
  "saltSprayHours",
  "saltSprayResult",
  "rustDiscolorationTimeMinutes",
  "filmFormingTemperatureMinC",
  "mandrelBendResult",
  "lowTemperatureFilmFormingResult",
  "wetCoatingThicknessMicron",
  "dryingConditions",
  "dryingPropertySeconds",
  "sprayDistanceCm",
  "purgeTimeSeconds",
  "cleaningPerformance",
  "materialInfluence",
  "safetyTestResults",
  "antibacterialResults",
  "dilutionGuidelines",
  "thickFilmCurabilityMm",
  "filmThicknessRangeMicron",
  "productLayerStack",
  "uvDoseKJPerM2",
  "curingLightSource",
  "cureDoseMjCm2",
  "cureDoseProfiles",
  "cureLampProfiles",
  "triggerCureProfiles",
  "graphOnlyProperties",
  "postCureProfiles",
  "transferConditions",
  "laminatingConditions",
  "tackStageWindowMinutes",
  "singleSpreadOpenTimeMinutes",
  "chemicalResistanceChangePct",
  "pressureResistanceMPa",
  "initialPressureResistanceMPa",
  "gasPermeabilityMolMPerM2SPa",
  "recommendedClearanceMm",
  "maximumClearanceMm",
  "cureTimesByTemperatureMinutes",
  "lapShearRangeMPa",
  "lapShearProfilesMPa",
  "compressionShearStrengthRangeMPa",
  "compressionShearStrengthsMPa",
  "lapShearSubstrate",
  "shearStrengthsMPa",
  "blockShearStrengthsMPa",
  "torsionalShearStrengthNm",
  "fittedBondingStrengthsMPa",
  "retainingTorqueNm",
  "fixingTorqueCureRateNm",
  "fixingTorqueBySizeNm",
  "fixingTorqueByMaterialNm",
  "fixingTorqueByTemperatureNm",
  "projectionRateFixingTorqueNm",
  "chemicalResistanceTorqueNm",
  "heatDeteriorationTorqueNm",
  "axialForceByTighteningTorqueKN",
  "sealabilityMPa",
  "blowOutResistanceMPa",
  "tPeelStrengthsKNPerM",
  "thermalShearStrengthsMPa",
  "dieShearStrengthsKgfCm2",
  "dieShearStrengthProfilesN",
  "dieShearStrengthKgf",
  "dieShearStrengthPsi",
  "bendingStrengthMPa",
  "elasticModulusPa",
  "storageModulusMPa",
  "storageModulusProfilesGPa",
  "storageModulusPsi",
  "lossModulusPeakC",
  "lossTangentPeakC",
  "linearShrinkagePct",
  "linearShrinkagePctMax",
  "linearExpansionCoeffPerK",
  "opticalTransmittancePct",
  "decompositionTemperatureC",
  "serviceTemperatureNote",
  "temperatureAt5PctWeightLossC",
  "glassTransitionC",
  "glassTransitionRangeC",
  "heatDistortionC",
  "specificGravity",
  "uvFluorescence",
  "excitationWavelengthNm",
  "uvDetectable",
  "siliconeFree",
  "isocyanateFree",
  "solventFree",
  "halogenFree",
  "lowEmission",
  "lowBleed",
  "applicationSystem",
  "removalAfterTemperatureC",
  "removalAfterMinutes",
  "transmittancePct",
  "internalTransmittancePct",
  "hazePct",
  "colorCielab",
  "waterAbsorptionPct",
  "moisturePermeabilityGm2Day",
  "outgassingPct",
  "weightLossPct",
  "thermalMassChangePct",
  "shrinkagePct",
  "linearShrinkageInPerIn",
  "specificHeatCapacityJPerGC",
  "thermalDiffusivityMm2S",
  "thermalExpansionCoeffPpmC",
  "thermalExpansionCoeffBelowTgPpmC",
  "thermalExpansionCoeffAboveTgPpmC",
  "thermalExpansionCoeffRangesPpmC",
  "thermalConductivityBtuInHrFt2F",
  "thermalConductivityRangeWmK",
  "thermalConductivityBtuFtHrFt2F",
  "thermalConductivityCalPerSecCmC",
  "temperatureTestedMinC",
  "temperatureTestedMaxC",
  "operatingTemperatureRangeC",
  "environmentalAgingShearMPa",
  "environmentalAgingShearRetentionPct",
  "heatAgingShearMPa",
  "heatAgingShearStrengthsMPa",
  "heatAgingProfiles",
  "heatShockProfiles",
  "fluidResistanceProfiles",
  "strengthRetentionProfilesPct",
  "thermalShockShearStrengthsMPa",
  "temperatureShearRetentionPct",
  "adhesionStrengthsMPa",
  "peelStrengthsNPerMm",
  "staticShearMinutes",
  "dynamicShearN",
  "saftC",
  "meltingPointRangeC",
  "flowStartingTemperatureC",
  "flowRoomTemperatureMaxIn",
  "flowCureTemperatureMaxIn",
  "arcResistanceSeconds",
  "totalMassLossPct",
  "collectedVolatileCondensableMaterialPct",
  "waterVaporRecoveredPct",
  "weightLossHeatAgingPct",
  "mixingInstructions",
  "openedGuardBagUseWithinMinutes",
  "maximumUseTempC",
  "maximumBondStrengthMinutes",
  "adhesionBuildTimeHours",
  "shortTermServiceTemperatureMinC",
  "shortTermServiceTemperatureMaxC",
  "longTermServiceTemperatureMinC",
  "longTermServiceTemperatureMaxC",
  "strengthRetentionPct",
  "densityKgM3",
  "densityLbFt3",
  "densityLbPerGal",
  "densityLbPerGalRange",
  "specificHeatBtuLbF",
  "specificVolume",
  "totalTapeThicknessMm",
  "totalTapeThicknessMil",
  "adhesiveThicknessMil",
  "adhesiveThicknessMicron",
  "linerThicknessMil",
  "linerThicknessMicron",
  "peelAdhesionNPerCm",
  "normalTensileKPa",
  "overlapShearKPa",
  "staticShearProfiles",
  "bondBuildProfilesPct",
  "applicationPressureKPa",
  "applicationTemperatureIdealRangeC",
  "minimumApplicationTemperatureC",
  "differentialMovementPctOfThickness",
  "dynamicStressDesignKPa",
  "staticLoadAreaCm2PerKg",
  "waterVaporTransmissionGm2Day",
  "outgassingProfilesPct",
  "nasaLowOutgassing",
  "tackingConditions",
  "bondingConditions",
  "minimumCurePressurePsi",
  "crosslinkConditions",
  "glassTransitionProfiles",
  "dielectricBreakdownVoltageKV",
  "comparativeTrackingIndexV",
  "impactStrength",
  "impactStrengthJPerM",
  "impactStrengthKJPerM2",
  "impactStrengthJ",
  "impactShearStrengthJ",
  "impactToughnessKgfCmCm2",
  "peakExothermC",
  "maximumExothermRiseC",
  "peakExothermTimeRangeMinutes",
  "peakExothermTimeMinutes",
  "gapFillRangeMm",
  "bridgingGapIn",
  "glassBeadSpacerMm",
  "lowHalogen",
  "halogenContentPpm",
  "mslRating",
  "ionConcentrationPpm",
  "lowIonContentPpm",
  "plasticCompatibility",
  "thermalResistanceAfter120C168h",
  "moistureResistanceAfter85C85RH168h",
  "lowMolecularWeightSiloxanePpm",
  "lowMolecularWeightCyclicSiloxanePpm",
  "penetration",
  "penetrationTest",
  "reworkable",
  "reworkProfiles",
  "catalyticPoisonCautions",
  "timeTo90PctCureHours",
  "componentDensitiesGPerMl",
  "componentDensitiesLbPerGal",
  "componentViscositiesCps",
  "structuralViscosityRatio",
  "workLifeSeconds",
  "shearStrengthsPsi",
  "temperatureShearStrengthsPsi",
  "vocDuringCurePct",
  "applicationRateGMin",
  "extrusionRateGMin",
  "hotStrengthRetentionPct",
  "standards",
  "flameRating",
  "verticalBurningTest",
  "approvals",
  "mshaApprovals",
  "nsfAnsiStandard",
  "ulRecognized",
  "voltageRatingV",
  "serviceOverloadMaxC",
  "adhesionToMetalsPsi",
  "adhesionToCableJacketsPsi",
  "workingPressureBar",
  "oxygenPressureBar",
  "oxygenServiceMaxC",
  "pipeUseRatings",
  "torqueStrengthFtLb",
  "recommendedBondLineMil",
  "applicationTemperatureMinC",
  "applicationTemperatureMaxC",
  "applicationTemperatureMinF",
  "applicationTemperatureMaxF",
  "serviceTemperatureMinF",
  "serviceTemperatureMaxF",
  "serviceTemperatureExcursionMaxF",
  "serviceTemperatureQualifier",
  "hardenerDropsPerOunce",
  "totalMassMaxGrams",
  "requiredDispenser",
  "accessories",
  "colorOptions",
  "primerlessAdhesionRatings",
  "repairLayerOverlapIn",
  "heatLampDistanceIn",
  "heatLampCureMinutes",
  "cleanupSolvents",
  "storageTemperatureMinC",
  "storageTemperatureMaxC",
  "storageProfiles",
  "thawTimeMinutes",
  "refreezeAfterThaw",
  "storageRelativeHumidityPct",
  "rainReadyTimeMinutes",
  "waterReadyTimeMinutes",
  "paintReadyTimeMinutes",
  "returnToServiceTimeMinutes",
  "toolingTimeMinutes",
  "basePolymer",
  "weightSolidsPct",
  "weightSolidsPctRange",
  "weightSolidsPctMin",
  "volumeSolidsPct",
  "densityLbPerGal",
  "coverageLinearFeet",
  "coverageBeadDiameterIn",
  "verticalSagIn",
  "jointWidthMaxIn",
  "jointWidthMaxMm",
  "jointDepthMaxIn",
  "jointMovementCapabilityPct",
  "movementAbsorptionPct",
  "stabilityRunoffMm",
  "flowRateMm",
  "buildingMaterialClass",
  "inOperationLifeExpectancyYears",
  "shelfLifeMonths",
  "shelfLifeDays",
  "freezeThawCycles",
  "roomTemperatureWorkLifeWeeks",
  "shelfLifeProfilesMonths",
  "thumbPressureMinutes",
  "tapeRemovalDelayMinutes",
  "strainGageElongationPct",
  "strainGageElongationWithCeaOptionEPct",
  "stencilLife",
  "recommendedCureTemperatureMinC",
  "recommendedCureTemperatureMaxC",
  "maximumCureTemperatureC",
  "maximumDotVolumeMm3",
  "particleSizeMicron",
  "thermalData",
  "bondlineSpacerRangeMm",
  "chemicalResistance",
  "solventResistance",
  "coatingCoverage",
  "recommendedCoatingThicknessMil",
  "recommendedCoatingThicknessMicron",
  "dryToTouchTimeMinutes",
  "dryToHardTimeMinutes",
  "sandingTimeMinutes",
  "cathodicDisbondmentMm",
  "hotWaterSoakAdhesionRating",
  "adhesionRating",
  "flexibilityDegreesPerPipeDiameter",
  "torqueBreakNm",
  "torquePrevailNm",
  "maxThreadSize",
  "instantSealPsi",
  "fullSealPsi",
  "pressureHandlingPsi",
  "openTimeMinutes",
  "openTimeSeconds",
  "minimumCureTimeMinutes",
  "trafficReadyTimeMinutes",
  "setTimeByTemperatureMinutes",
  "holdTimeSeconds",
  "handlingStrengthMinutes",
  "relativeSetTime",
  "bodyClass",
  "pipeMaterial",
  "pipeDiameterMaxIn",
  "schedule80DiameterMaxIn",
  "primerOptional",
  "ultimateBondStrengthHours",
  "timeTo65To80PctStrengthHours",
  "timeTo80PctStrengthHours",
  "bondStrengthsPsi",
  "coverageSqFt",
  "coverageSqFtPerGallon",
  "requiredSpreadMil",
  "clampingPressurePsiByWood",
  "assemblyPressurePsi",
  "storageTemperatureMinF",
  "storageTemperatureMaxF",
  "hotMeltEcTemperatureModuleC",
  "hotMeltDeliveryTimeSeconds",
  "densityGPerCm3",
  "densityRangeGPerCm3",
  "filler",
  "fillerWeightPct",
  "particleSizeD90Micron",
  "adhesionNPerCm",
  "shieldingAttenuationDb",
  "solidsContentPct",
  "volumeShrinkagePctMax",
  "flashPointC",
  "flashPointF",
  "flashPointRangeC",
  "flammability",
  "vocContentGPerL",
  "vocContentByWeightPctMax",
  "vocLessWaterExemptSolventsPct",
  "compositionByWeightPct",
  "percentVolatilePct",
  "vaporPressureMmHg",
  "flammableLimitsVolumePct",
  "nfpaHazardRatings",
  "aerosolStorageCode",
  "productIdentificationNumbers",
  "solventByVariant",
  "specificGravityByVariant",
  "viscosityByVariantCps",
  "viscosityByTemperaturePaS",
  "primerActivationWindowMinutes",
  "kinematicViscosityMm2S",
  "boilingPointMinC",
  "setupTimeProfiles",
  "shearStrengthProfiles",
  "shearStrengthProfilesPsi",
  "containerVolumeMl",
  "applicatorIncluded",
  "lapShearForcesKN",
  "temperatureResistanceLapShearKN",
  "fluidResistanceLapShearMinKN",
  "materialSystemsCode",
  "packagingMethod",
  "packagingQuantity",
  "syringePackage",
  "curingMethods",
  "lowOutgassing",
  "psaOpenTimeRangeMinutes",
  "optimalPsaOpenTimeRangeMinutes",
  "initialPeelStrengthNPerMm",
  "overlapShearBuildMPa",
  "youngsModulusMPa",
  "dispensePressureMaxBar",
  "syringeTemperatureMaxC",
  "nozzleInnerDiameterMinMm",
  "durabilityProfiles",
  "environmentalOpticalTests",
  "cleanroomLaminationClass",
  "maxRollLengthYd",
  "maxRollWidthIn",
  "slittingToleranceMm",
  "foodContactRegulation",
  "chemicalInventoryCompliance",
  "rohsCompliant",
  "iso10993Part5",
  "electronicGrade",
  "heavyMetalFree",
  "pfosFree",
  "phthalateFree",
  "vocSolidsPct",
  "conegHeavyMetalsPpmMax",
  "prop65ChemicalsPresent",
  "conflictMineralsPresent",
  "netWeightLbPerGal",
  "weightPerGallonLb",
  "bondingRangeMinutes",
  "heatResistanceC",
  "ballRingMeltPointC",
  "peelStrengthPiw",
  "peelStrengthPpi",
  "modulusAt100PctPsi",
  "volumeSwellPct",
  "oilResistanceProfiles",
  "lowTemperatureShockC",
  "corrosionTestResult",
  "waterproof",
  "outdoorUse",
  "moistureResistant",
  "paintable",
  "stainable",
  "sandable",
  "drillable",
  "tappable",
  "fileable",
  "oilResistant",
  "waterResistant",
  "waterproof",
  "weatherproof",
  "wetDampSurfaceApplication",
  "shrinkCrackProof",
  "moldMildewResistant",
  "lowOdor",
  "vocCompliant",
  "foamSafe",
  "odorless",
  "nonFrosting",
  "nonFogging",
  "coralSafe",
  "aquaticOrganismSafe",
  "flexibleCure",
  "refrigeratedStorageRecommended",
  "chemicalResistant",
  "waterImmersionRecommended",
  "lifetimeGuarantee",
  "variantProperties",
  "gapFilling",
  "expandsWhenCured",
  "clampTimeRangeMinutes",
  "pressTimeSeconds",
  "pressTimeRangeSeconds",
  "packageSize",
  "productSku",
  "productEan",
  "dryColor",
  "driedFilmColor",
  "chalkTemperatureF",
  "chalkTemperatureC",
  "freezeThawStability",
  "woodFailurePct",
  "ansiWaterResistance",
  "foodContactIndirect",
  "astmD4236Conforms",
  "notStructural",
  "maximumUseTempF",
  "uvResistant",
  "saltwaterResistant",
  "solventResistant",
  "sourceRevisionDate",
  "tdsDownload",
  "professionalUseOnly",
  "rawSolventMethod",
  "flammable",
  "chlorinatedSolvent",
  "containsMethyleneChloride",
  "containsChloroform",
  "containsMek",
  "vocFree",
  "pipeCodeWarning",
  "fixtureTimeNote",
  "viscosityNote",
  "testPiece",
  "testCondition",
  "testMethod",
  "testTemperature",
  "testSubstrate",
  "testSurfacePrep",
  "testDwellTime",
  "testBondlineThickness",
  "recommendedBondLineMm",
];

const PROFILE_LIBRARY = {
  toughenedEpoxy: {
    chemistry: "Toughened epoxy",
    cureFamily: "2-part epoxy",
    cureDetail: "2-part room temperature cure",
    serviceMin: -55,
    serviceMax: 120,
    viscosityClass: "high",
    thixotropic: true,
    gapFill: 5,
    thermalConductivity: 0.2,
    clarity: "opaque",
    potLife: 20,
    fixtureTime: 120,
    lapShear: 32,
    stress: buildStress({ shear: 8.5, peel: 6, impact: 7 }),
    environment: buildEnvironment({ humidity: 0.9, fuel: 0.68, immersion: 0.74 }),
    substrates: buildRatings(
      {
        aluminum: 10,
        steel: 10,
        copper: 9,
        glass: 8,
        ceramic: 9,
        wood: 7,
        mdf: 6,
        paper: 4,
        fabric: 3,
        leather: 3,
        abs: 8,
        pvc: 7,
        acrylic: 6,
        polycarbonate: 7,
        petg: 6,
        rubber: 3,
        siliconeRubber: 0,
        hdpe: 1,
        concrete: 7,
        fr4: 9,
        carbonFiber: 10,
      },
      1,
    ),
    summary:
      "Forgiving structural epoxy for mixed-material joints that need gap filling and durable load transfer.",
    cautions: ["Surface prep still matters on passive or oily metals."],
  },
  flexibleEpoxy: {
    chemistry: "Flexible epoxy",
    cureFamily: "2-part epoxy",
    cureDetail: "2-part room temperature cure",
    serviceMin: -55,
    serviceMax: 95,
    viscosityClass: "high",
    thixotropic: true,
    gapFill: 4,
    thermalConductivity: 0.18,
    clarity: "opaque",
    potLife: 45,
    fixtureTime: 240,
    lapShear: 24,
    stress: buildStress({ shear: 7.2, peel: 8.3, impact: 8.5 }),
    environment: buildEnvironment({ humidity: 0.87, fuel: 0.58, immersion: 0.7 }),
    substrates: buildRatings(
      {
        aluminum: 9,
        steel: 9,
        copper: 8,
        glass: 8,
        ceramic: 8,
        wood: 8,
        mdf: 7,
        paper: 5,
        fabric: 4,
        leather: 4,
        abs: 8,
        pvc: 7,
        acrylic: 6,
        polycarbonate: 7,
        petg: 6,
        rubber: 5,
        siliconeRubber: 0,
        hdpe: 1,
        concrete: 7,
        fr4: 8,
        carbonFiber: 9,
      },
      1,
    ),
    summary:
      "Tough, more compliant epoxy for joints that see peel, impact, and a bit of flex instead of pure stiffness.",
    cautions: ["Longer clamp time than faster structural systems."],
  },
  clearEpoxy: {
    chemistry: "Clear epoxy",
    cureFamily: "2-part epoxy",
    cureDetail: "2-part room temperature cure",
    serviceMin: -40,
    serviceMax: 110,
    viscosityClass: "medium",
    thixotropic: false,
    gapFill: 2,
    thermalConductivity: 0.2,
    clarity: "transparent",
    potLife: 5,
    fixtureTime: 30,
    lapShear: 22,
    stress: buildStress({ shear: 7, peel: 4.5, impact: 4 }),
    environment: buildEnvironment({ humidity: 0.78, fuel: 0.52, immersion: 0.5 }),
    substrates: buildRatings(
      {
        aluminum: 7,
        steel: 7,
        copper: 7,
        glass: 8,
        ceramic: 8,
        wood: 6,
        mdf: 5,
        paper: 3,
        fabric: 2,
        leather: 2,
        abs: 7,
        pvc: 6,
        acrylic: 8,
        polycarbonate: 8,
        petg: 7,
        rubber: 2,
        siliconeRubber: 0,
        hdpe: 0,
        concrete: 5,
        fr4: 7,
        carbonFiber: 7,
      },
      0,
    ),
    summary:
      "Transparent epoxy for visible bond lines where appearance matters alongside moderate structural strength.",
    cautions: ["Can amber over time in UV-heavy outdoor exposure."],
  },
  structuralAcrylic: {
    chemistry: "Structural acrylic",
    cureFamily: "Structural acrylic",
    cureDetail: "2-part acrylic",
    serviceMin: -40,
    serviceMax: 140,
    viscosityClass: "high",
    thixotropic: true,
    gapFill: 6,
    thermalConductivity: 0.18,
    clarity: "opaque",
    potLife: 10,
    fixtureTime: 20,
    lapShear: 28,
    stress: buildStress({ shear: 8.1, peel: 7.4, impact: 8.2 }),
    environment: buildEnvironment({ humidity: 0.88, fuel: 0.65, immersion: 0.69 }),
    substrates: buildRatings(
      {
        aluminum: 9,
        steel: 9,
        copper: 8,
        glass: 7,
        ceramic: 7,
        wood: 7,
        mdf: 6,
        paper: 4,
        fabric: 3,
        leather: 3,
        abs: 9,
        pvc: 9,
        acrylic: 8,
        polycarbonate: 8,
        petg: 8,
        rubber: 5,
        siliconeRubber: 0,
        hdpe: 2,
        concrete: 6,
        fr4: 7,
        carbonFiber: 8,
      },
      1,
    ),
    summary:
      "Aggressive structural acrylic for metals and engineered plastics, especially where speed and impact toughness matter.",
    cautions: ["Strong odor during cure and shorter open time than slower epoxies."],
  },
  mmaPlasticWelder: {
    chemistry: "MMA plastic bonder",
    cureFamily: "Structural acrylic",
    cureDetail: "2-part methyl methacrylate",
    serviceMin: -40,
    serviceMax: 120,
    viscosityClass: "high",
    thixotropic: true,
    gapFill: 5,
    thermalConductivity: 0.16,
    clarity: "opaque",
    potLife: 4,
    fixtureTime: 15,
    lapShear: 24,
    stress: buildStress({ shear: 7.6, peel: 7.2, impact: 8.4 }),
    environment: buildEnvironment({ humidity: 0.84, fuel: 0.55, immersion: 0.61 }),
    substrates: buildRatings(
      {
        aluminum: 8,
        steel: 8,
        copper: 7,
        glass: 5,
        ceramic: 6,
        wood: 6,
        mdf: 6,
        paper: 2,
        fabric: 2,
        leather: 2,
        abs: 10,
        pvc: 9,
        acrylic: 8,
        polycarbonate: 9,
        petg: 9,
        rubber: 5,
        siliconeRubber: 0,
        hdpe: 1,
        concrete: 5,
        fr4: 6,
        carbonFiber: 7,
      },
      0,
    ),
    summary:
      "Fast MMA system built to bite into hard-to-bond plastics better than classic brittle chemistries.",
    cautions: ["Use ventilation and watch exotherm on larger masses."],
  },
  thinCA: {
    chemistry: "Thin cyanoacrylate",
    cureFamily: "Cyanoacrylate",
    cureDetail: "Moisture cure",
    serviceMin: -50,
    serviceMax: 80,
    viscosityClass: "wicking",
    thixotropic: false,
    gapFill: 0.05,
    thermalConductivity: 0.1,
    clarity: "transparent",
    potLife: 1,
    fixtureTime: 0.25,
    lapShear: 18,
    stress: buildStress({ shear: 5.7, peel: 2.4, impact: 2.4 }),
    environment: buildEnvironment({ humidity: 0.5, fuel: 0.35, immersion: 0.2 }),
    substrates: buildRatings(
      {
        aluminum: 7,
        steel: 7,
        copper: 6,
        glass: 7,
        ceramic: 8,
        wood: 9,
        mdf: 8,
        paper: 8,
        fabric: 4,
        leather: 6,
        abs: 7,
        pvc: 7,
        acrylic: 5,
        polycarbonate: 6,
        petg: 6,
        rubber: 7,
        siliconeRubber: 0,
        hdpe: 0,
        concrete: 4,
        fr4: 6,
        carbonFiber: 6,
      },
      0,
    ),
    summary:
      "Extremely fast wicking CA for tiny gaps, capillary action, and fast tack on close-fitting parts.",
    cautions: ["Brittle in peel and impact. Low surface energy plastics still need primer."],
  },
  gelCA: {
    chemistry: "Gel cyanoacrylate",
    cureFamily: "Cyanoacrylate",
    cureDetail: "Moisture cure",
    serviceMin: -50,
    serviceMax: 90,
    viscosityClass: "high",
    thixotropic: true,
    gapFill: 0.25,
    thermalConductivity: 0.1,
    clarity: "transparent",
    potLife: 2,
    fixtureTime: 0.5,
    lapShear: 18,
    stress: buildStress({ shear: 5.8, peel: 3.2, impact: 3.1 }),
    environment: buildEnvironment({ humidity: 0.52, fuel: 0.36, immersion: 0.22 }),
    substrates: buildRatings(
      {
        aluminum: 7,
        steel: 7,
        copper: 6,
        glass: 7,
        ceramic: 8,
        wood: 9,
        mdf: 8,
        paper: 8,
        fabric: 5,
        leather: 7,
        abs: 8,
        pvc: 8,
        acrylic: 5,
        polycarbonate: 6,
        petg: 6,
        rubber: 8,
        siliconeRubber: 0,
        hdpe: 0,
        concrete: 4,
        fr4: 6,
        carbonFiber: 6,
      },
      0,
    ),
    summary:
      "Gap-tolerant CA gel for fast repairs where run-off would ruin alignment or cosmetics.",
    cautions: ["Still brittle compared with structural acrylics or epoxies."],
  },
  hybridCA: {
    chemistry: "Hybrid instant epoxy",
    cureFamily: "Cyanoacrylate hybrid",
    cureDetail: "Dual-cure hybrid instant adhesive",
    serviceMin: -40,
    serviceMax: 120,
    viscosityClass: "medium",
    thixotropic: false,
    gapFill: 5,
    thermalConductivity: 0.14,
    clarity: "opaque",
    potLife: 4,
    fixtureTime: 10,
    lapShear: 24,
    stress: buildStress({ shear: 6.8, peel: 5.2, impact: 5.8 }),
    environment: buildEnvironment({ humidity: 0.76, fuel: 0.46, immersion: 0.44 }),
    substrates: buildRatings(
      {
        aluminum: 8,
        steel: 8,
        copper: 7,
        glass: 7,
        ceramic: 8,
        wood: 8,
        mdf: 7,
        paper: 5,
        fabric: 5,
        leather: 6,
        abs: 8,
        pvc: 8,
        acrylic: 6,
        polycarbonate: 7,
        petg: 7,
        rubber: 6,
        siliconeRubber: 0,
        hdpe: 0,
        concrete: 5,
        fr4: 7,
        carbonFiber: 7,
      },
      0,
    ),
    summary:
      "Hybrid chemistry that cures faster than structural epoxies while bridging much larger gaps than normal CA.",
    cautions: ["Not as temperature-stable as the best structural epoxies."],
  },
  uvOptical: {
    chemistry: "UV optical acrylic",
    cureFamily: "UV cure",
    cureDetail: "UV light cure",
    serviceMin: -40,
    serviceMax: 90,
    viscosityClass: "low",
    thixotropic: false,
    gapFill: 0.15,
    thermalConductivity: 0.12,
    clarity: "optically-clear",
    potLife: 60,
    fixtureTime: 1,
    lapShear: 16,
    stress: buildStress({ shear: 5.5, peel: 4.1, impact: 3.5 }),
    environment: buildEnvironment({ humidity: 0.75, fuel: 0.35, immersion: 0.42 }),
    substrates: buildRatings(
      {
        aluminum: 5,
        steel: 5,
        copper: 5,
        glass: 10,
        ceramic: 7,
        wood: 2,
        mdf: 1,
        paper: 1,
        fabric: 1,
        leather: 1,
        abs: 4,
        pvc: 4,
        acrylic: 9,
        polycarbonate: 9,
        petg: 8,
        rubber: 0,
        siliconeRubber: 0,
        hdpe: 0,
        concrete: 0,
        fr4: 4,
        carbonFiber: 1,
      },
      0,
    ),
    summary:
      "UV-curing optical adhesive for clear assemblies, display windows, and fast fixture when light can reach the bond line.",
    cautions: ["Opaque joints and shadowed areas need secondary cure support."],
  },
  rtvSilicone: {
    chemistry: "RTV silicone",
    cureFamily: "RTV silicone",
    cureDetail: "Moisture cure elastomer",
    serviceMin: -55,
    serviceMax: 200,
    viscosityClass: "high",
    thixotropic: true,
    gapFill: 6,
    thermalConductivity: 0.22,
    clarity: "translucent",
    potLife: 15,
    fixtureTime: 20,
    lapShear: 2.5,
    stress: buildStress({ shear: 3, peel: 9, impact: 8.5 }),
    environment: buildEnvironment({ humidity: 0.96, fuel: 0.42, immersion: 0.8 }),
    substrates: buildRatings(
      {
        aluminum: 6,
        steel: 6,
        copper: 5,
        glass: 9,
        ceramic: 9,
        wood: 6,
        mdf: 5,
        paper: 2,
        fabric: 4,
        leather: 4,
        abs: 4,
        pvc: 5,
        acrylic: 2,
        polycarbonate: 2,
        petg: 4,
        rubber: 7,
        siliconeRubber: 2,
        hdpe: 0,
        concrete: 7,
        fr4: 6,
        carbonFiber: 5,
      },
      0,
    ),
    summary:
      "Flexible, high-temperature sealant adhesive for weatherproofing, gasketing, and joints that move.",
    cautions: ["General RTV can stress-crack acrylic and polycarbonate."],
  },
  siliconeRubberAdhesive: {
    chemistry: "Silicone-to-silicone adhesive",
    cureFamily: "RTV silicone",
    cureDetail: "Moisture cure elastomer",
    serviceMin: -50,
    serviceMax: 205,
    viscosityClass: "high",
    thixotropic: true,
    gapFill: 4,
    thermalConductivity: 0.21,
    clarity: "translucent",
    potLife: 10,
    fixtureTime: 15,
    lapShear: 3,
    stress: buildStress({ shear: 3.2, peel: 10, impact: 9 }),
    environment: buildEnvironment({ humidity: 0.96, fuel: 0.4, immersion: 0.85 }),
    substrates: buildRatings(
      {
        aluminum: 5,
        steel: 5,
        copper: 4,
        glass: 8,
        ceramic: 8,
        wood: 4,
        mdf: 3,
        paper: 1,
        fabric: 4,
        leather: 3,
        abs: 2,
        pvc: 2,
        acrylic: 1,
        polycarbonate: 1,
        petg: 1,
        rubber: 7,
        siliconeRubber: 10,
        hdpe: 0,
        concrete: 5,
        fr4: 5,
        carbonFiber: 4,
      },
      0,
    ),
    summary:
      "Purpose-built option when silicone rubber itself is one side of the joint and normal adhesives fail outright.",
    cautions: ["Not a shortcut around low surface energy plastics like HDPE."],
  },
  polyurethaneSealant: {
    chemistry: "Polyurethane sealant",
    cureFamily: "Polyurethane",
    cureDetail: "Moisture cure polyurethane",
    serviceMin: -40,
    serviceMax: 100,
    viscosityClass: "very-high",
    thixotropic: true,
    gapFill: 10,
    thermalConductivity: 0.19,
    clarity: "opaque",
    potLife: 35,
    fixtureTime: 180,
    lapShear: 6,
    stress: buildStress({ shear: 5.8, peel: 9, impact: 8 }),
    environment: buildEnvironment({ humidity: 0.92, fuel: 0.55, immersion: 0.78 }),
    substrates: buildRatings(
      {
        aluminum: 7,
        steel: 7,
        copper: 6,
        glass: 7,
        ceramic: 8,
        wood: 9,
        mdf: 8,
        paper: 3,
        fabric: 5,
        leather: 5,
        abs: 6,
        pvc: 7,
        acrylic: 4,
        polycarbonate: 5,
        petg: 5,
        rubber: 7,
        siliconeRubber: 0,
        hdpe: 1,
        concrete: 9,
        fr4: 4,
        carbonFiber: 6,
      },
      1,
    ),
    summary:
      "High-build sealant adhesive for outdoor joints, marine seams, and assemblies that need flexibility more than stiffness.",
    cautions: ["Slow through-cure on thick beads."],
  },
  msPolymerSealant: {
    chemistry: "MS polymer sealant adhesive",
    cureFamily: "MS polymer",
    cureDetail: "One-part moisture-cure silane-modified polymer",
    serviceMin: -40,
    serviceMax: 100,
    viscosityClass: "very-high",
    thixotropic: true,
    gapFill: 8,
    thermalConductivity: 0.19,
    clarity: "opaque",
    potLife: 20,
    fixtureTime: 180,
    lapShear: 2,
    stress: buildStress({ shear: 3.8, peel: 8.2, impact: 7.8 }),
    environment: buildEnvironment({ humidity: 0.94, fuel: 0.34, immersion: 0.66 }),
    substrates: buildRatings(
      {
        aluminum: 8,
        steel: 8,
        copper: 6,
        glass: 8,
        ceramic: 7,
        wood: 9,
        mdf: 8,
        paper: 2,
        fabric: 4,
        leather: 4,
        abs: 6,
        pvc: 8,
        acrylic: 5,
        polycarbonate: 6,
        petg: 5,
        rubber: 5,
        siliconeRubber: 0,
        hdpe: 1,
        concrete: 7,
        fr4: 6,
        carbonFiber: 6,
      },
      1,
    ),
    summary:
      "Flexible weatherable sealant adhesive for mixed construction, panel bonding, and electronics sealing where movement tolerance matters more than high stiffness.",
    cautions: ["Moisture-cure depth depends on humidity and bead geometry; not a substitute for structural acrylic or epoxy in high-load joints."],
  },
  anaerobicThreadlocker: {
    chemistry: "Anaerobic threadlocker",
    cureFamily: "Anaerobic",
    cureDetail: "Anaerobic cure in metal threads",
    serviceMin: -55,
    serviceMax: 180,
    viscosityClass: "low",
    thixotropic: false,
    gapFill: 0.15,
    thermalConductivity: 0.11,
    clarity: "transparent",
    potLife: 30,
    fixtureTime: 10,
    lapShear: 15,
    stress: buildStress({ shear: 8.2, peel: 0.5, impact: 3.1 }),
    environment: buildEnvironment({ humidity: 0.82, fuel: 0.82, immersion: 0.7 }),
    substrates: buildRatings(
      {
        aluminum: 9,
        steel: 10,
        copper: 8,
      },
      0,
    ),
    summary:
      "Designed to lock threaded metal fasteners against vibration, leakage, and loosening.",
    cautions: ["Needs active metals or primer for fastest cure on passive alloys."],
  },
  anaerobicRetainer: {
    chemistry: "Anaerobic retaining compound",
    cureFamily: "Anaerobic",
    cureDetail: "Anaerobic cure in close metal fits",
    serviceMin: -55,
    serviceMax: 175,
    viscosityClass: "low",
    thixotropic: false,
    gapFill: 0.25,
    thermalConductivity: 0.11,
    clarity: "transparent",
    potLife: 30,
    fixtureTime: 15,
    lapShear: 24,
    stress: buildStress({ shear: 9, peel: 0.5, impact: 3.3 }),
    environment: buildEnvironment({ humidity: 0.82, fuel: 0.85, immersion: 0.72 }),
    substrates: buildRatings(
      {
        aluminum: 9,
        steel: 10,
        copper: 8,
      },
      0,
    ),
    summary:
      "Made for cylindrical metal fits such as bearings, shafts, bushings, and sleeves.",
    cautions: ["Works only in tight clearances and only on metal assemblies."],
  },
  foamTape: {
    chemistry: "Acrylic foam tape",
    cureFamily: "Pressure-sensitive tape",
    cureDetail: "Pressure-sensitive acrylic foam",
    serviceMin: -35,
    serviceMax: 95,
    viscosityClass: "very-high",
    thixotropic: true,
    gapFill: 1.1,
    thermalConductivity: 0.06,
    clarity: "opaque",
    potLife: 999,
    fixtureTime: 20,
    lapShear: 12,
    stress: buildStress({ shear: 6.2, peel: 10, impact: 7.2 }),
    environment: buildEnvironment({ humidity: 0.95, fuel: 0.35, immersion: 0.55 }),
    substrates: buildRatings(
      {
        aluminum: 9,
        steel: 9,
        copper: 7,
        glass: 10,
        ceramic: 8,
        wood: 5,
        mdf: 4,
        paper: 3,
        fabric: 3,
        leather: 3,
        abs: 8,
        pvc: 8,
        acrylic: 10,
        polycarbonate: 9,
        petg: 8,
        rubber: 5,
        siliconeRubber: 0,
        hdpe: 2,
        concrete: 3,
        fr4: 6,
        carbonFiber: 8,
      },
      0,
    ),
    summary:
      "Instant-handling structural tape for clean exterior bonds, peel-heavy loads, and differential thermal movement.",
    cautions: ["Needs good wet-out pressure and enough bonded area to shine."],
  },
  contactCement: {
    chemistry: "Contact cement",
    cureFamily: "Contact cement",
    cureDetail: "Solvent flash-off contact bond",
    serviceMin: -20,
    serviceMax: 90,
    viscosityClass: "medium",
    thixotropic: false,
    gapFill: 0.4,
    thermalConductivity: 0.08,
    clarity: "opaque",
    potLife: 20,
    fixtureTime: 15,
    lapShear: 4,
    stress: buildStress({ shear: 3.5, peel: 8.3, impact: 5 }),
    environment: buildEnvironment({ humidity: 0.65, fuel: 0.4, immersion: 0.2 }),
    substrates: buildRatings(
      {
        aluminum: 4,
        steel: 4,
        copper: 3,
        glass: 2,
        ceramic: 2,
        wood: 8,
        mdf: 8,
        paper: 8,
        fabric: 9,
        leather: 10,
        abs: 5,
        pvc: 6,
        acrylic: 3,
        polycarbonate: 3,
        petg: 3,
        rubber: 9,
        siliconeRubber: 0,
        hdpe: 0,
        concrete: 2,
        fr4: 1,
        carbonFiber: 2,
      },
      0,
    ),
    summary:
      "Classic tack-on-both-sides bond for laminates, leather, footwear, foam, and flexible sheet goods.",
    cautions: ["Alignment is mostly one-shot once both flashed surfaces touch."],
  },
  pvaWood: {
    chemistry: "Crosslinking PVA",
    cureFamily: "PVA",
    cureDetail: "Waterborne wood glue",
    serviceMin: 5,
    serviceMax: 90,
    viscosityClass: "medium",
    thixotropic: false,
    gapFill: 0.2,
    thermalConductivity: 0.09,
    clarity: "translucent",
    potLife: 8,
    fixtureTime: 30,
    lapShear: 8,
    stress: buildStress({ shear: 5, peel: 4, impact: 4.2 }),
    environment: buildEnvironment({ humidity: 0.75, fuel: 0.1, immersion: 0.18 }),
    substrates: buildRatings(
      {
        wood: 10,
        mdf: 9,
        paper: 8,
        fabric: 6,
        leather: 4,
      },
      0,
    ),
    summary:
      "Wood-first adhesive that excels in well-mated porous joints where the substrate should fail before the glue line.",
    cautions: ["Not for large gaps, constant wet immersion, or metal-to-plastic joints."],
  },
  hotMelt: {
    chemistry: "EVA hot melt",
    cureFamily: "Hot melt",
    cureDetail: "Thermoplastic hot melt",
    serviceMin: -10,
    serviceMax: 65,
    viscosityClass: "very-high",
    thixotropic: true,
    gapFill: 2,
    thermalConductivity: 0.09,
    clarity: "translucent",
    potLife: 5,
    fixtureTime: 1,
    lapShear: 3,
    stress: buildStress({ shear: 2.8, peel: 5.2, impact: 4.1 }),
    environment: buildEnvironment({ humidity: 0.55, fuel: 0.18, immersion: 0.08 }),
    substrates: buildRatings(
      {
        aluminum: 2,
        steel: 2,
        copper: 2,
        glass: 2,
        ceramic: 2,
        wood: 7,
        mdf: 7,
        paper: 9,
        fabric: 8,
        leather: 5,
        abs: 5,
        pvc: 4,
        acrylic: 4,
        polycarbonate: 4,
        petg: 4,
        rubber: 4,
        siliconeRubber: 0,
        hdpe: 1,
        concrete: 1,
        fr4: 2,
        carbonFiber: 1,
      },
      0,
    ),
    summary:
      "Fast, forgiving craft and packaging adhesive when you need immediate tack and low tooling overhead.",
    cautions: ["Heat quickly softens the bond back up."],
  },
  sprayAdhesive: {
    chemistry: "Spray adhesive",
    cureFamily: "Spray adhesive",
    cureDetail: "Aerosol pressure-sensitive bond",
    serviceMin: -20,
    serviceMax: 70,
    viscosityClass: "low",
    thixotropic: false,
    gapFill: 0.1,
    thermalConductivity: 0.06,
    clarity: "transparent",
    potLife: 5,
    fixtureTime: 2,
    lapShear: 2,
    stress: buildStress({ shear: 2.2, peel: 4.4, impact: 2.5 }),
    environment: buildEnvironment({ humidity: 0.45, fuel: 0.12, immersion: 0.05 }),
    substrates: buildRatings(
      {
        wood: 4,
        mdf: 4,
        paper: 9,
        fabric: 9,
        leather: 4,
        abs: 4,
        pvc: 4,
        acrylic: 3,
        polycarbonate: 3,
        petg: 3,
        rubber: 3,
      },
      0,
    ),
    summary:
      "Fast coverage for light laminations, insulation, fabric, paper, and layout work where structural strength is not the goal.",
    cautions: ["Overspray and heat resistance both need watching."],
  },
  thermalEpoxy: {
    chemistry: "Thermally conductive epoxy",
    cureFamily: "2-part epoxy",
    cureDetail: "Filled thermal epoxy",
    serviceMin: -40,
    serviceMax: 150,
    viscosityClass: "medium",
    thixotropic: false,
    gapFill: 0.3,
    thermalConductivity: 1.6,
    clarity: "opaque",
    potLife: 5,
    fixtureTime: 15,
    lapShear: 16,
    stress: buildStress({ shear: 7.1, peel: 3.1, impact: 3.3 }),
    environment: buildEnvironment({ humidity: 0.8, fuel: 0.5, immersion: 0.55 }),
    substrates: buildRatings(
      {
        aluminum: 9,
        steel: 8,
        copper: 10,
        glass: 5,
        ceramic: 9,
        wood: 1,
        mdf: 0,
        paper: 0,
        fabric: 0,
        leather: 0,
        abs: 2,
        pvc: 1,
        acrylic: 1,
        polycarbonate: 2,
        petg: 1,
        rubber: 0,
        siliconeRubber: 0,
        hdpe: 0,
        concrete: 0,
        fr4: 9,
        carbonFiber: 6,
      },
      0,
    ),
    summary:
      "Filled epoxy that trades some generality for real thermal transfer in electronics, heat spreaders, and sensor bonding.",
    cautions: ["Filled systems are less optically clean and less peel-tolerant than standard epoxies."],
  },
  solventAcrylic: {
    chemistry: "Acrylic solvent cement",
    cureFamily: "Solvent cement",
    cureDetail: "Solvent weld",
    serviceMin: -40,
    serviceMax: 80,
    viscosityClass: "wicking",
    thixotropic: false,
    gapFill: 0.08,
    thermalConductivity: 0.08,
    clarity: "transparent",
    potLife: 1,
    fixtureTime: 3,
    lapShear: 10,
    stress: buildStress({ shear: 5.2, peel: 2.8, impact: 2.2 }),
    environment: buildEnvironment({ humidity: 0.7, fuel: 0.2, immersion: 0.3 }),
    substrates: buildRatings(
      {
        acrylic: 10,
        polycarbonate: 5,
        petg: 4,
      },
      0,
    ),
    summary:
      "Capillary solvent weld for acrylic when the best bond is the one that effectively becomes the substrate.",
    cautions: ["Needs precise fit-up and can craze the wrong plastic."],
  },
  solventPVC: {
    chemistry: "PVC solvent cement",
    cureFamily: "Solvent cement",
    cureDetail: "Solvent weld",
    serviceMin: -10,
    serviceMax: 60,
    viscosityClass: "low",
    thixotropic: false,
    gapFill: 0.2,
    thermalConductivity: 0.08,
    clarity: "transparent",
    potLife: 2,
    fixtureTime: 4,
    lapShear: 10,
    stress: buildStress({ shear: 5.6, peel: 2.5, impact: 2.4 }),
    environment: buildEnvironment({ humidity: 0.72, fuel: 0.25, immersion: 0.45 }),
    substrates: buildRatings(
      {
        pvc: 10,
        abs: 4,
      },
      0,
    ),
    summary:
      "Plumbing-style solvent weld for rigid PVC joints where the bond is really a localized melt-and-fuse process.",
    cautions: ["Wrong for most other plastics and for decorative visible bond lines."],
  },
  solventCPVC: {
    chemistry: "CPVC solvent cement",
    cureFamily: "Solvent cement",
    cureDetail: "Solvent weld",
    serviceMin: -10,
    serviceMax: 82,
    viscosityClass: "high",
    thixotropic: false,
    gapFill: 0.5,
    thermalConductivity: 0.08,
    clarity: "opaque",
    potLife: 3,
    fixtureTime: 15,
    lapShear: 8,
    stress: buildStress({ shear: 5.8, peel: 2.4, impact: 2.5 }),
    environment: buildEnvironment({ humidity: 0.75, fuel: 0.25, immersion: 0.58 }),
    substrates: buildRatings(
      {
        cpvc: 10,
        pvc: 6,
      },
      0,
    ),
    summary:
      "CPVC pipe-and-fitting solvent cement for hot-water and industrial piping where CPVC compatibility is the point.",
    cautions: ["Use the pipe-system instructions, primers, cure tables, and code listings for pressure service."],
  },
  solventABSStyrene: {
    chemistry: "ABS/styrene solvent cement",
    cureFamily: "Solvent cement",
    cureDetail: "Solvent weld",
    serviceMin: -20,
    serviceMax: 70,
    viscosityClass: "wicking",
    thixotropic: false,
    gapFill: 0.08,
    thermalConductivity: 0.08,
    clarity: "transparent",
    potLife: 3,
    fixtureTime: 5,
    lapShear: 8,
    stress: buildStress({ shear: 5, peel: 2.4, impact: 2.6 }),
    environment: buildEnvironment({ humidity: 0.55, fuel: 0.18, immersion: 0.25 }),
    substrates: buildRatings(
      {
        abs: 10,
        polystyrene: 10,
        acrylic: 6,
        polycarbonate: 6,
      },
      0,
    ),
    summary:
      "Water-thin solvent cement family for ABS, styrene/HIPS, and model-style same-plastic fabrication.",
    cautions: ["Many ABS/styrene solvent cements are same-material only; do not infer dissimilar-plastic compatibility."],
  },
  solventPolycarbonate: {
    chemistry: "Polycarbonate solvent cement",
    cureFamily: "Solvent cement",
    cureDetail: "Solvent weld",
    serviceMin: -20,
    serviceMax: 80,
    viscosityClass: "wicking",
    thixotropic: false,
    gapFill: 0.05,
    thermalConductivity: 0.08,
    clarity: "transparent",
    potLife: 2,
    fixtureTime: 5,
    lapShear: 9,
    stress: buildStress({ shear: 5.2, peel: 2, impact: 1.8 }),
    environment: buildEnvironment({ humidity: 0.55, fuel: 0.12, immersion: 0.22 }),
    substrates: buildRatings(
      {
        polycarbonate: 10,
        acrylic: 6,
        pvc: 5,
      },
      0,
    ),
    summary:
      "Solvent bonding route for close-fitting polycarbonate joints when a fast, clear fused edge matters more than retained impact strength.",
    cautions: [
      "Solvent bonding can significantly reduce polycarbonate strength and trigger crazing in stressed parts.",
    ],
  },
  solventMultiPlastic: {
    chemistry: "Multi-plastic solvent cement",
    cureFamily: "Solvent cement",
    cureDetail: "Solvent weld",
    serviceMin: -20,
    serviceMax: 70,
    viscosityClass: "low",
    thixotropic: false,
    gapFill: 0.1,
    thermalConductivity: 0.08,
    clarity: "transparent",
    potLife: 8,
    fixtureTime: 12,
    lapShear: 6,
    stress: buildStress({ shear: 4.8, peel: 2.3, impact: 2.4 }),
    environment: buildEnvironment({ humidity: 0.6, fuel: 0.18, immersion: 0.32 }),
    substrates: buildRatings(
      {
        acrylic: 8,
        abs: 8,
        pvc: 8,
        polystyrene: 8,
        polycarbonate: 4,
        petg: 4,
      },
      0,
    ),
    summary:
      "Mixed-plastic solvent cement for selected thermoplastics where the specific product data sheet names both sides of the joint.",
    cautions: ["Material-pair coverage is product-specific; test before treating it as a universal plastic solvent."],
  },
  constructionAdhesive: {
    chemistry: "Construction adhesive",
    cureFamily: "Construction adhesive",
    cureDetail: "High-build moisture cure",
    serviceMin: -30,
    serviceMax: 120,
    viscosityClass: "very-high",
    thixotropic: true,
    gapFill: 12,
    thermalConductivity: 0.12,
    clarity: "opaque",
    potLife: 20,
    fixtureTime: 30,
    lapShear: 7,
    stress: buildStress({ shear: 6.4, peel: 7.1, impact: 7.2 }),
    environment: buildEnvironment({ humidity: 0.9, fuel: 0.3, immersion: 0.4 }),
    substrates: buildRatings(
      {
        aluminum: 6,
        steel: 6,
        copper: 5,
        glass: 4,
        ceramic: 8,
        wood: 9,
        mdf: 9,
        paper: 3,
        fabric: 1,
        leather: 1,
        abs: 3,
        pvc: 4,
        acrylic: 1,
        polycarbonate: 1,
        petg: 1,
        rubber: 3,
        siliconeRubber: 0,
        hdpe: 0,
        concrete: 10,
        fr4: 1,
        carbonFiber: 2,
      },
      0,
    ),
    summary:
      "Gap-filling site adhesive for building materials, stone, wood, masonry, and rough field assembly.",
    cautions: ["Overkill for small precision parts and ugly on visible joints."],
  },
  industrialClear: {
    chemistry: "Flexible industrial adhesive",
    cureFamily: "Flexible solvent adhesive",
    cureDetail: "Solvent release cure",
    serviceMin: -30,
    serviceMax: 82,
    viscosityClass: "medium",
    thixotropic: false,
    gapFill: 1.5,
    thermalConductivity: 0.08,
    clarity: "transparent",
    potLife: 15,
    fixtureTime: 60,
    lapShear: 5,
    stress: buildStress({ shear: 4.7, peel: 7.4, impact: 6.2 }),
    environment: buildEnvironment({ humidity: 0.8, fuel: 0.5, immersion: 0.4 }),
    substrates: buildRatings(
      {
        aluminum: 6,
        steel: 6,
        copper: 5,
        glass: 7,
        ceramic: 6,
        wood: 8,
        mdf: 7,
        paper: 6,
        fabric: 8,
        leather: 8,
        abs: 7,
        pvc: 7,
        acrylic: 5,
        polycarbonate: 5,
        petg: 5,
        rubber: 8,
        siliconeRubber: 0,
        hdpe: 0,
        concrete: 4,
        fr4: 4,
        carbonFiber: 4,
      },
      0,
    ),
    summary:
      "Flexible all-around repair adhesive for odd jobs, trim, textiles, leather, and light mixed-material repairs.",
    cautions: ["Solvent smell and moderate cure time may be a deal breaker indoors."],
  },
  fabricAdhesive: {
    chemistry: "Fabric adhesive",
    cureFamily: "Flexible solvent adhesive",
    cureDetail: "Fast solvent release",
    serviceMin: -20,
    serviceMax: 80,
    viscosityClass: "medium",
    thixotropic: false,
    gapFill: 0.5,
    thermalConductivity: 0.08,
    clarity: "transparent",
    potLife: 10,
    fixtureTime: 10,
    lapShear: 3,
    stress: buildStress({ shear: 3.1, peel: 8.1, impact: 5.1 }),
    environment: buildEnvironment({ humidity: 0.72, fuel: 0.2, immersion: 0.18 }),
    substrates: buildRatings(
      {
        wood: 2,
        mdf: 2,
        paper: 6,
        fabric: 10,
        leather: 8,
        abs: 3,
        pvc: 3,
        acrylic: 1,
        polycarbonate: 1,
        petg: 1,
        rubber: 5,
      },
      0,
    ),
    summary:
      "Fast-tack textile adhesive that stays supple enough for hems, trim, patches, and craft surfaces.",
    cautions: ["Not a structural plastic or metal bonder."],
  },
  craftPva: {
    chemistry: "Craft PVA",
    cureFamily: "PVA",
    cureDetail: "Waterborne craft glue",
    serviceMin: 5,
    serviceMax: 60,
    viscosityClass: "medium",
    thixotropic: false,
    gapFill: 0.2,
    thermalConductivity: 0.08,
    clarity: "translucent",
    potLife: 10,
    fixtureTime: 20,
    lapShear: 2,
    stress: buildStress({ shear: 2.5, peel: 4.5, impact: 2.5 }),
    environment: buildEnvironment({ humidity: 0.45, fuel: 0.05, immersion: 0.05 }),
    substrates: buildRatings(
      {
        wood: 6,
        mdf: 6,
        paper: 10,
        fabric: 8,
        leather: 3,
      },
      0,
    ),
    summary:
      "Low-cost craft and school glue for porous materials like paper, cardboard, felt, and light wood.",
    cautions: ["Poor water resistance and not intended for structural joints."],
  },
  structuralPolyurethane: {
    chemistry: "Structural polyurethane",
    cureFamily: "Polyurethane",
    cureDetail: "2-part polyurethane",
    serviceMin: -40,
    serviceMax: 116,
    viscosityClass: "high",
    thixotropic: true,
    gapFill: 8,
    thermalConductivity: 0.14,
    clarity: "opaque",
    potLife: 15,
    fixtureTime: 60,
    lapShear: 14,
    stress: buildStress({ shear: 6.5, peel: 8.5, impact: 8.4 }),
    environment: buildEnvironment({ humidity: 0.88, fuel: 0.42, immersion: 0.55 }),
    substrates: buildRatings(
      {
        aluminum: 7,
        steel: 7,
        copper: 6,
        glass: 4,
        ceramic: 5,
        wood: 7,
        mdf: 6,
        paper: 2,
        fabric: 4,
        leather: 5,
        abs: 7,
        pvc: 7,
        acrylic: 3,
        polycarbonate: 6,
        petg: 6,
        rubber: 7,
        siliconeRubber: 0,
        hdpe: 1,
        concrete: 4,
        fr4: 5,
        carbonFiber: 8,
      },
      0,
    ),
    summary:
      "Tough, more elastic structural polyurethane for composites, plastics, and dynamic mixed-material assemblies.",
    cautions: ["Not usually the first choice for very high-temperature service."],
  },
  uvAcrylate: {
    chemistry: "UV acrylate",
    cureFamily: "UV cure",
    cureDetail: "UV / visible-light cure",
    serviceMin: -50,
    serviceMax: 130,
    viscosityClass: "low",
    thixotropic: false,
    gapFill: 0.2,
    thermalConductivity: 0.1,
    clarity: "transparent",
    potLife: 60,
    fixtureTime: 0.5,
    lapShear: 14,
    stress: buildStress({ shear: 5, peel: 3.8, impact: 3.1 }),
    environment: buildEnvironment({ humidity: 0.76, fuel: 0.3, immersion: 0.38 }),
    substrates: buildRatings(
      {
        glass: 10,
        ceramic: 7,
        acrylic: 8,
        polycarbonate: 8,
        petg: 7,
        aluminum: 5,
        steel: 5,
        abs: 4,
        fr4: 4,
      },
      0,
    ),
    summary:
      "Fast light-cured acrylate for clear parts, glass bonding, and fast-fixture assemblies with light access.",
    cautions: ["Shadowed bond lines need secondary cure chemistry or a different adhesive."],
  },
};

function inferApplicationTagsForProduct(profileName, product, overrideTags = []) {
  const text = [
    product.name,
    product.summary,
    product.chemistry,
    product.cureFamily,
    product.cureDetail,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  const tags = [...(PROFILE_APPLICATION_TAGS[profileName] ?? []), ...overrideTags];
  const add = (tag) => {
    if (!tags.includes(tag)) tags.push(tag);
  };

  if (
    /structural|bonding epoxy|bonding acrylic|methacrylate|crash durable|vhb/.test(text)
  ) {
    add("structural-bonding");
  }
  if (/instant|cyanoacrylate|super glue/.test(text)) add("instant-bonding");
  if (/optically clear|optical|uv optical|glass bonding|visible-light|uv light/.test(text)) {
    add("optical-bonding");
  }
  if (/threadlocker|studlock|screwlock/.test(text)) add("threadlocking");
  if (/retaining compound|retainer|bearing mount|bushing|sleeve/.test(text)) add("retaining");
  if (/gasket maker|sealant|seam sealer|rtv|weatherproof/.test(text)) add("sealing-gasketing");
  if (/potting|thermal|conductive adhesive|insulating adhesive|heat spreader/.test(text)) {
    add("potting-thermal");
  }
  if (/contact cement|contact bond|laminate/.test(text)) add("contact-lamination");
  if (/construction adhesive|anchoring adhesive|masonry|concrete/.test(text)) add("construction");
  if (/spray adhesive|aerosol/.test(text)) add("spray-mounting");
  if (/hot melt|glue stick/.test(text)) add("hot-melt-assembly");
  if (/solvent cement|solvent weld/.test(text)) add("solvent-welding");
  if (/wood glue|paper|cardboard|fabric|leather|felt/.test(text)) add("wood-paper-fabric");
  if (/polyolefin|lse|plastic welder|plastic bonder|polyethylene|polypropylene/.test(text)) {
    add("plastic-repair");
  }

  if (product.thermalConductivity >= 1) add("potting-thermal");
  if (product.substrates?.hdpe >= 8) add("plastic-repair");
  if (product.profileKey === "clearEpoxy" && product.clarity !== "opaque") add("optical-bonding");
  if (!tags.length) add("general-repair");

  return dedupeList(tags);
}

const PROFILE_ALIASES = {
  acrylicLatexSealant: "constructionAdhesive",
  flexiblePolyurethane: "structuralPolyurethane",
  onePartEpoxy: "toughenedEpoxy",
  polyesterResin: "clearEpoxy",
};

const materialPairKey = ([left, right]) => [left, right].sort().join("::");
const materialPairListHas = (pairs, selectedMaterials) => {
  const selectedKey = materialPairKey(selectedMaterials);
  return (pairs ?? []).some((pair) => materialPairKey(pair) === selectedKey);
};

const makeProduct = (id, profileName, overrides) => {
  const libraryProfileName = hasOwn(PROFILE_LIBRARY, profileName)
    ? profileName
    : hasOwn(PROFILE_ALIASES, profileName)
      ? PROFILE_ALIASES[profileName]
      : undefined;
  const profile = PROFILE_LIBRARY[libraryProfileName];
  if (!profile) {
    throw new Error(`Unknown adhesive profile "${profileName}" for product "${id}"`);
  }
  const product = {
    id,
    profileKey: profileName,
    profileDerivedFields: [
      "serviceMin",
      "serviceMax",
      "viscosityClass",
      "thixotropic",
      "gapFill",
      "thermalConductivity",
      "clarity",
      "potLife",
      "fixtureTime",
      "lapShear",
    ].filter((field) => !hasOwn(overrides, field)),
    profileDerivedStress: Object.keys(profile.stress ?? {}).filter(
      (field) => !hasOwn(overrides.stress ?? {}, field),
    ),
    profileDerivedEnvironment: Object.keys(profile.environment ?? {}).filter(
      (field) => !hasOwn(overrides.environment ?? {}, field),
    ),
    profileDerivedSubstrates: MATERIAL_KEYS.filter(
      (material) => !hasOwn(overrides.substrates ?? {}, material),
    ),
    maker: overrides.maker,
    name: overrides.name,
    chemistry: profile.chemistry,
    cureFamily: profile.cureFamily,
    cureDetail: profile.cureDetail,
    serviceMin: profile.serviceMin,
    serviceMax: profile.serviceMax,
    viscosityClass: profile.viscosityClass,
    thixotropic: profile.thixotropic,
    gapFill: profile.gapFill,
    thermalConductivity: profile.thermalConductivity,
    clarity: profile.clarity,
    potLife: profile.potLife,
    fixtureTime: profile.fixtureTime,
    lapShear: profile.lapShear,
    stress: { ...profile.stress },
    environment: { ...profile.environment },
    substrates: { ...profile.substrates },
    compatibleMaterialPairs: (profile.compatibleMaterialPairs ?? []).map((pair) => [...pair]),
    incompatibleMaterialPairs: (profile.incompatibleMaterialPairs ?? []).map((pair) => [...pair]),
    profileDerivedCompatibleMaterialPairs: !hasOwn(overrides, "compatibleMaterialPairs"),
    profileDerivedIncompatibleMaterialPairs: !hasOwn(overrides, "incompatibleMaterialPairs"),
    summary: profile.summary,
    cautions: [...(profile.cautions ?? [])],
  };

  if (overrides.serviceMin !== undefined) product.serviceMin = overrides.serviceMin;
  if (overrides.serviceMax !== undefined) product.serviceMax = overrides.serviceMax;
  if (overrides.viscosityClass) product.viscosityClass = overrides.viscosityClass;
  if (overrides.thixotropic !== undefined) product.thixotropic = overrides.thixotropic;
  if (overrides.gapFill !== undefined) product.gapFill = overrides.gapFill;
  if (overrides.thermalConductivity !== undefined) {
    product.thermalConductivity = overrides.thermalConductivity;
  }
  if (overrides.clarity) product.clarity = overrides.clarity;
  if (overrides.potLife !== undefined) product.potLife = overrides.potLife;
  if (overrides.fixtureTime !== undefined) product.fixtureTime = overrides.fixtureTime;
  if (overrides.lapShear !== undefined) product.lapShear = overrides.lapShear;
  if (overrides.chemistry) product.chemistry = overrides.chemistry;
  if (overrides.summary) product.summary = overrides.summary;
  if (overrides.cureFamily) product.cureFamily = overrides.cureFamily;
  if (overrides.cureDetail) product.cureDetail = overrides.cureDetail;
  if (overrides.stress) product.stress = { ...product.stress, ...overrides.stress };
  if (overrides.environment) {
    product.environment = { ...product.environment, ...overrides.environment };
  }
  if (overrides.substrates) {
    product.substrates = { ...product.substrates, ...overrides.substrates };
  }
  if (overrides.compatibleMaterialPairs) {
    product.compatibleMaterialPairs = overrides.compatibleMaterialPairs.map((pair) => [...pair]);
  }
  if (overrides.incompatibleMaterialPairs) {
    product.incompatibleMaterialPairs = overrides.incompatibleMaterialPairs.map((pair) => [...pair]);
  }
  if (overrides.cautions) {
    product.cautions = [...product.cautions, ...overrides.cautions];
  }
  if (overrides.pricing) {
    product.pricing = overrides.pricing;
  }
  if (overrides.mcmaster) {
    product.mcmaster = { ...overrides.mcmaster };
  }
  OBSERVED_TDS_FIELDS.forEach((field) => {
    if (hasCatalogValue(overrides[field])) {
      product[field] = overrides[field];
    }
  });
  product.applicationTags = inferApplicationTagsForProduct(
    profileName,
    product,
    overrides.applicationTags ?? [],
  );

  product.referenceUrl =
    overrides.referenceUrl ??
    `https://www.google.com/search?q=${encodeURIComponent(`${product.name} TDS`)}`;
  if (overrides.specUrl) product.specUrl = overrides.specUrl;
  if (overrides.tdsUrl) product.tdsUrl = overrides.tdsUrl;
  if (overrides.productUrl) product.productUrl = overrides.productUrl;
  if (overrides.sdsUrl) product.sdsUrl = overrides.sdsUrl;
  if (overrides.catalogUrl) product.catalogUrl = overrides.catalogUrl;
  product.sourceLabel = overrides.sourceLabel ?? overrides.mcmaster?.sourceLabel;

  return product;
};

const GLUES = [
  makeProduct("3m-dp420ns", "toughenedEpoxy", {
    maker: "3M",
    name: "Scotch-Weld DP420NS",
    potLife: 20,
    fixtureTime: 120,
    lapShear: 38,
    summary:
      "A dependable structural mixed-material workhorse with strong metal bonding and good gap tolerance.",
  }),
  makeProduct("loctite-ea9460", "toughenedEpoxy", {
    maker: "Loctite",
    name: "EA 9460",
    potLife: 60,
    fixtureTime: 180,
    lapShear: 34,
    summary:
      "Longer-working structural epoxy for larger assemblies where precise alignment takes time.",
  }),
  makeProduct("jbweld-original", "toughenedEpoxy", {
    maker: "J-B Weld",
    name: "Original Cold-Weld",
    serviceMax: 287,
    potLife: 25,
    fixtureTime: 360,
    lapShear: 27,
    environment: { fuel: 0.8 },
    summary:
      "Steel-filled repair epoxy with unusually high heat tolerance for field fixes, brackets, and housings.",
    cautions: ["Not the fastest way to fixture a part."],
  }),
  makeProduct("loctite-ea9394-aero", "toughenedEpoxy", {
    maker: "Henkel Loctite",
    name: "EA 9394 AERO",
    serviceMax: 232,
    serviceMin: -55,
    potLife: 240,
    fixtureTime: 1440,
    lapShear: 34,
    viscosityClass: "very-high",
    thixotropic: true,
    gapFill: 1.5,
    summary:
      "Aerospace structural epoxy paste for high-temperature service, tough bondlines, and demanding composite-to-metal assemblies.",
  }),
  makeProduct("3m-1386-cream", "toughenedEpoxy", {
    maker: "3M",
    name: "Scotch-Weld 1386 (Cream)",
    cureFamily: "Heat-cure epoxy",
    cureDetail: "1-part heat cure epoxy",
    serviceMax: 121,
    serviceMin: -55,
    potLife: 9999,
    fixtureTime: 60,
    lapShear: 26,
    viscosityClass: "high",
    thixotropic: true,
    summary:
      "One-part heat-cure epoxy for high-temperature bonded assemblies where refrigerated storage and oven cure are acceptable.",
  }),
  makeProduct("loctite-e214hp", "toughenedEpoxy", {
    maker: "Henkel Loctite",
    name: "EA E-214HP",
    cureFamily: "Heat-cure epoxy",
    cureDetail: "1-part heat cure epoxy paste",
    serviceMax: 120,
    serviceMin: -55,
    potLife: 9999,
    fixtureTime: 120,
    lapShear: 31,
    viscosityClass: "high",
    thixotropic: true,
    summary:
      "One-part high-strength heat-cure epoxy paste for structural assemblies that need higher Tg than room-temperature systems.",
  }),
  makeProduct("west-gflex-650", "flexibleEpoxy", {
    maker: "WEST SYSTEM",
    name: "G/flex 650",
    potLife: 45,
    fixtureTime: 180,
    lapShear: 22,
    summary:
      "A more compliant epoxy that stays calm under peel, impact, and differential expansion.",
  }),
  makeProduct("3m-ec2216", "flexibleEpoxy", {
    maker: "3M",
    name: "Scotch-Weld EC-2216 B/A",
    potLife: 90,
    fixtureTime: 240,
    lapShear: 20,
    serviceMax: 121,
    summary:
      "Flexible aerospace-flavored epoxy for metal, composites, and joints that move a little in service.",
  }),
  makeProduct("3m-dp125", "flexibleEpoxy", {
    maker: "3M",
    name: "Scotch-Weld DP125",
    serviceMax: 82,
    serviceMin: -55,
    potLife: 25,
    fixtureTime: 180,
    lapShear: 20,
    summary:
      "Low-odor flexible epoxy that handles peel and movement better than rigid structural pastes.",
  }),
  makeProduct("3m-dp100-clear", "clearEpoxy", {
    maker: "3M",
    name: "Scotch-Weld DP100 Plus Clear",
    potLife: 5,
    fixtureTime: 20,
    lapShear: 23,
    clarity: "transparent",
    summary:
      "Clear fast-setting epoxy for visible bonds on glass, acrylic, and many plastics.",
  }),
  makeProduct("araldite-2011", "clearEpoxy", {
    maker: "Araldite",
    name: "2011",
    potLife: 100,
    fixtureTime: 420,
    lapShear: 20,
    clarity: "translucent",
    summary:
      "Toughened paste epoxy with slower working time and good performance on metals and many engineering plastics.",
  }),
  makeProduct("3m-dp8405ns", "structuralAcrylic", {
    maker: "3M",
    name: "Scotch-Weld DP8405NS",
    potLife: 4,
    fixtureTime: 12,
    lapShear: 27,
    summary:
      "Low-odor structural acrylic that bites into metals and plastics with impressive speed.",
  }),
  makeProduct("3m-dp8005", "structuralAcrylic", {
    maker: "3M",
    name: "Scotch-Weld DP8005",
    potLife: 3,
    fixtureTime: 180,
    lapShear: 18,
    viscosityClass: "medium",
    substrates: {
      hdpe: 9,
      abs: 8,
      pvc: 7,
      petg: 7,
      polycarbonate: 6,
      acrylic: 5,
      rubber: 6,
    },
    summary:
      "Specialized structural plastic adhesive for polyethylene, polypropylene, TPEs, and other low-surface-energy plastics without heavy pretreatment.",
    cautions: ["Short work life and slower handling strength than general-purpose structural acrylics."],
  }),
  makeProduct("permabond-ta4610", "structuralAcrylic", {
    maker: "Permabond",
    name: "TA4610",
    potLife: 10,
    fixtureTime: 20,
    lapShear: 30,
    summary:
      "Structural acrylic tuned for fast fixture and strong mixed-material bonding without excessive brittleness.",
  }),
  makeProduct("lord-406-19", "structuralAcrylic", {
    maker: "LORD",
    name: "406/19",
    potLife: 4,
    fixtureTime: 15,
    lapShear: 26,
    summary:
      "Classic acrylic for structural plastic-to-metal assemblies that need impact tolerance.",
  }),
  makeProduct("lord-201", "structuralAcrylic", {
    maker: "LORD / Parker",
    name: "201 Acrylic Adhesive",
    serviceMax: 148,
    serviceMin: -40,
    potLife: 18,
    fixtureTime: 120,
    lapShear: 25,
    viscosityClass: "medium",
    thixotropic: false,
    summary:
      "Self-leveling structural acrylic for metals, plastics, and ceramics where flow into hard-to-reach geometry helps.",
  }),
  makeProduct("lord-850s", "structuralAcrylic", {
    maker: "LORD / Parker",
    name: "850S Toughened Structural Acrylic",
    serviceMax: 148,
    serviceMin: -40,
    potLife: 15,
    fixtureTime: 120,
    lapShear: 23,
    viscosityClass: "very-high",
    thixotropic: true,
    stress: { peel: 8.2, impact: 8.9, shear: 7.4 },
    summary:
      "Impact-resistant non-sag structural acrylic with high elongation for joints that need toughness more than stiffness.",
  }),
  makeProduct("plexus-ma310", "structuralAcrylic", {
    maker: "ITW Plexus",
    name: "MA310",
    serviceMax: 121,
    serviceMin: -40,
    potLife: 16,
    fixtureTime: 50,
    lapShear: 25,
    summary:
      "Medium-cure structural MMA for composites, metals, and plastic panels where controlled work time matters.",
  }),
  makeProduct("loctite-h3000", "structuralAcrylic", {
    maker: "Henkel Loctite",
    name: "AA H3000 Speedbonder",
    serviceMax: 82,
    serviceMin: -55,
    potLife: 8,
    fixtureTime: 20,
    lapShear: 24,
    viscosityClass: "medium",
    summary:
      "General-purpose 1:1 methacrylate with strong peel and shear for fast multi-substrate assembly.",
  }),
  makeProduct("3m-dp8710ns", "structuralAcrylic", {
    maker: "3M",
    name: "Scotch-Weld DP8710NS",
    serviceMax: 82,
    serviceMin: -40,
    potLife: 10,
    fixtureTime: 30,
    lapShear: 22,
    viscosityClass: "high",
    thixotropic: true,
    summary:
      "Low-odor non-sag MMA with fast strength build and good low-temperature toughness on thin metals and plastics.",
  }),
  makeProduct("loctite-3032", "structuralAcrylic", {
    maker: "Henkel Loctite",
    name: "3032 Polyolefin Bonder",
    serviceMax: 121,
    serviceMin: -40,
    potLife: 5,
    fixtureTime: 30,
    lapShear: 17,
    viscosityClass: "high",
    thixotropic: true,
    substrates: {
      hdpe: 9,
      abs: 7,
      pvc: 6,
      petg: 6,
      polycarbonate: 5,
      rubber: 5,
    },
    summary:
      "Methacrylate built for low-surface-energy plastics such as HDPE and PP without a separate primer step.",
  }),
  makeProduct("devcon-plastic-welder", "mmaPlasticWelder", {
    maker: "Devcon",
    name: "Plastic Welder",
    potLife: 3,
    fixtureTime: 8,
    lapShear: 21,
    summary:
      "Fast MMA plastic bonder that performs better than generic epoxies on ABS, PVC, and many thermoplastics.",
  }),
  makeProduct("loctite-406", "thinCA", {
    maker: "Loctite",
    name: "406",
    fixtureTime: 0.2,
    summary:
      "Ultra-fast low-viscosity CA for close-fitting plastics, rubber, and quick bench repairs.",
  }),
  makeProduct("loctite-401", "thinCA", {
    maker: "Henkel Loctite",
    name: "401",
    fixtureTime: 0.3,
    serviceMax: 80,
    serviceMin: -40,
    summary:
      "Surface-insensitive general-purpose ethyl cyanoacrylate for quick bonding of metals, wood, leather, and many plastics.",
  }),
  makeProduct("starbond-em150", "thinCA", {
    maker: "Starbond",
    name: "EM-150 Medium",
    viscosityClass: "low",
    gapFill: 0.12,
    fixtureTime: 0.4,
    summary:
      "Slightly fuller-bodied instant adhesive for precise repairs where you want speed without pure water-thin run-off.",
  }),
  makeProduct("loctite-454", "gelCA", {
    maker: "Loctite",
    name: "454 Gel",
    fixtureTime: 0.5,
    summary:
      "Non-drip CA gel for vertical surfaces, porous materials, and quick tack without migration.",
  }),
  makeProduct("permabond-2050", "gelCA", {
    maker: "Permabond",
    name: "2050",
    gapFill: 0.3,
    lapShear: 19,
    stress: { impact: 3.8 },
    summary:
      "Rubber-toughened CA that hangs onto peel and impact a bit better than classic brittle instant adhesives.",
  }),
  makeProduct("loctite-hy4090", "hybridCA", {
    maker: "Loctite",
    name: "HY 4090",
    potLife: 4,
    fixtureTime: 10,
    gapFill: 5,
    lapShear: 24,
    summary:
      "Hybrid instant adhesive that bridges real gaps while still fixing parts much faster than conventional epoxies.",
  }),
  makeProduct("loctite-hy4070", "hybridCA", {
    maker: "Loctite",
    name: "HY 4070",
    potLife: 4,
    fixtureTime: 6,
    gapFill: 5,
    clarity: "transparent",
    lapShear: 22,
    summary:
      "Transparent cyanoacrylate-acrylic hybrid for fast structural repairs on larger gaps than normal instant adhesives can tolerate.",
  }),
  makeProduct("loctite-aa330", "structuralAcrylic", {
    maker: "Loctite",
    name: "AA 330",
    potLife: 15,
    fixtureTime: 20,
    lapShear: 24,
    viscosityClass: "medium",
    cureDetail: "2-step acrylic with activator",
    substrates: {
      pvc: 9,
      acrylic: 9,
      abs: 8,
      polycarbonate: 7,
      petg: 7,
      aluminum: 7,
      steel: 7,
    },
    summary:
      "Acrylic structural bonder for dissimilar substrates such as PVC, acrylics, phenolics, and metals when used with an activator system.",
  }),
  makeProduct("dymax-3099", "uvOptical", {
    maker: "Dymax",
    name: "3099",
    serviceMax: 125,
    fixtureTime: 0.5,
    lapShear: 18,
    summary:
      "Fast UV adhesive for glass, metal, and clear plastic assemblies where light reaches the joint.",
  }),
  makeProduct("norland-noa61", "uvOptical", {
    maker: "Norland",
    name: "NOA 61",
    clarity: "optically-clear",
    fixtureTime: 1,
    lapShear: 12,
    summary:
      "Optical adhesive tuned for clear bond lines, lenses, and display-window style assemblies.",
  }),
  makeProduct("dymax-light-weld-429", "uvOptical", {
    maker: "Dymax",
    name: "Light-Weld 429",
    serviceMax: 130,
    serviceMin: -50,
    fixtureTime: 0.4,
    lapShear: 15,
    clarity: "transparent",
    substrates: {
      glass: 10,
      acrylic: 8,
      polycarbonate: 8,
      petg: 7,
      aluminum: 5,
      steel: 5,
    },
    summary:
      "UV/visible-light glass and clear-plastic bonder for fast fixture and clean transparent assemblies.",
  }),
  makeProduct("momentive-rtv162", "rtvSilicone", {
    maker: "Momentive",
    name: "RTV162",
    serviceMax: 250,
    summary:
      "Neutral-cure silicone adhesive sealant with strong weather resistance and solid electronics compatibility.",
  }),
  makeProduct("permatex-ultra-red", "rtvSilicone", {
    maker: "Permatex",
    name: "Ultra Red RTV",
    serviceMax: 343,
    viscosityClass: "very-high",
    gapFill: 6,
    fixtureTime: 60,
    summary:
      "High-temperature sensor-safe RTV for exhaust-adjacent gasketing and hot mechanical sealing work.",
    cautions: ["Not recommended for parts in direct contact with gasoline."],
  }),
  makeProduct("permatex-right-stuff-red", "rtvSilicone", {
    maker: "Permatex",
    name: "The Right Stuff Red 90 Minute",
    serviceMax: 343,
    viscosityClass: "very-high",
    gapFill: 6,
    fixtureTime: 90,
    summary:
      "Fast-return high-temperature RTV gasket maker for vibration-heavy automotive assemblies and rapid service turnaround.",
    cautions: ["Optimized for formed-in-place gasketing more than general-purpose visible bonding."],
  }),
  makeProduct("dow-3145", "rtvSilicone", {
    maker: "Dow",
    name: "3145 RTV Mil-A-46146",
    serviceMax: 200,
    summary:
      "Electronics-friendly silicone for sealing, strain relief, and flexible high-temperature bonds.",
  }),
  makeProduct("loctite-si5699", "rtvSilicone", {
    maker: "Henkel Loctite",
    name: "SI 5699",
    serviceMax: 175,
    serviceMin: -55,
    viscosityClass: "very-high",
    gapFill: 6,
    summary:
      "Automotive neutral-cure silicone gasket maker for formed-in-place gasketing and flexible hot-service sealing.",
  }),
  makeProduct("smoothon-silpoxy", "siliconeRubberAdhesive", {
    maker: "Smooth-On",
    name: "Sil-Poxy",
    fixtureTime: 15,
    gapFill: 3,
    summary:
      "One of the few dependable answers when silicone rubber itself is one side of the bond.",
  }),
  makeProduct("permatex-ultra-black", "rtvSilicone", {
    maker: "Permatex",
    name: "Ultra Black",
    serviceMax: 260,
    viscosityClass: "very-high",
    gapFill: 6,
    summary:
      "Automotive gasket maker that behaves like a robust non-sag silicone sealant for oily mechanical joints.",
    environment: { fuel: 0.68, immersion: 0.82 },
  }),
  makeProduct("sikaflex-221", "polyurethaneSealant", {
    maker: "Sika",
    name: "Sikaflex-221",
    potLife: 45,
    fixtureTime: 120,
    gapFill: 12,
    summary:
      "Flexible high-build adhesive sealant for vehicle bodies, housings, and outdoor assemblies.",
  }),
  makeProduct("sikaflex-252", "polyurethaneSealant", {
    maker: "Sika",
    name: "Sikaflex-252",
    potLife: 35,
    fixtureTime: 120,
    gapFill: 12,
    stress: { shear: 6.8, impact: 8.3, peel: 9.2 },
    summary:
      "Elastic polyurethane adhesive designed for dynamic vehicle assembly bonding across metals, composites, ceramic materials, and some plastics.",
  }),
  makeProduct("3m-5200", "polyurethaneSealant", {
    maker: "3M",
    name: "5200 Marine Adhesive Sealant",
    potLife: 60,
    fixtureTime: 240,
    gapFill: 15,
    environment: { immersion: 0.9 },
    summary:
      "A famously tenacious marine polyurethane for submerged, outdoor, and high-movement joints.",
    cautions: ["Removal later is difficult and often destructive."],
  }),
  makeProduct("loctite-243", "anaerobicThreadlocker", {
    maker: "Loctite",
    name: "243",
    summary:
      "Medium-strength oil-tolerant threadlocker for vibrating fasteners and serviceable metal hardware.",
  }),
  makeProduct("loctite-222", "anaerobicThreadlocker", {
    maker: "Henkel Loctite",
    name: "222",
    viscosityClass: "high",
    summary:
      "Low-strength threadlocker for small fasteners and adjustable hardware that still needs serviceability.",
  }),
  makeProduct("loctite-271", "anaerobicThreadlocker", {
    maker: "Henkel Loctite",
    name: "271",
    summary:
      "High-strength permanent threadlocker for studs and fasteners that should not back out in service.",
  }),
  makeProduct("loctite-290-wicking", "anaerobicThreadlocker", {
    maker: "Henkel Loctite",
    name: "290 Wicking",
    viscosityClass: "wicking",
    fixtureTime: 10,
    summary:
      "Wicking threadlocker for pre-assembled metal fasteners that need post-assembly vibration resistance.",
  }),
  makeProduct("loctite-638", "anaerobicRetainer", {
    maker: "Loctite",
    name: "638",
    summary:
      "High-strength retaining compound for cylindrical metal fits such as bearings, sleeves, and shafts.",
  }),
  makeProduct("loctite-648", "anaerobicRetainer", {
    maker: "Henkel Loctite",
    name: "648",
    serviceMax: 175,
    serviceMin: -55,
    summary:
      "High-temperature retaining compound for close-fitting metal sleeves, hubs, bushings, and shafts.",
  }),
  makeProduct("loctite-620", "anaerobicRetainer", {
    maker: "Henkel Loctite",
    name: "620",
    serviceMax: 230,
    serviceMin: -55,
    viscosityClass: "high",
    thixotropic: true,
    gapFill: 0.3,
    summary:
      "High-temperature retaining compound for larger-gap cylindrical metal fits and hot-service repairs.",
  }),
  makeProduct("3m-vhb-5952", "foamTape", {
    maker: "3M",
    name: "VHB 5952",
    gapFill: 1.1,
    summary:
      "Acrylic foam tape for clean exterior mounting, signage, panels, and mixed-material peel loads.",
  }),
  makeProduct("tesa-7058", "foamTape", {
    maker: "tesa",
    name: "ACXplus 7058",
    gapFill: 0.8,
    summary:
      "Structural acrylic foam tape with strong performance on metals, glass, and many coated surfaces.",
  }),
  makeProduct("dap-weldwood", "contactCement", {
    maker: "DAP",
    name: "Weldwood Original Contact Cement",
    summary:
      "Reliable laminate and leather contact cement when both sides can be coated and aligned once.",
  }),
  makeProduct("titebond-iii", "pvaWood", {
    maker: "Titebond",
    name: "III Ultimate Wood Glue",
    serviceMin: 4,
    environment: { humidity: 0.82, immersion: 0.28 },
    summary:
      "Outdoor-rated wood glue for cabinetry, furniture, jigs, and general porous wood assemblies.",
  }),
  makeProduct("gorilla-hot-glue", "hotMelt", {
    maker: "Gorilla",
    name: "Hot Glue Sticks",
    summary:
      "Fast craft adhesive for packaging, display mockups, light fixtures, and low-load household fixes.",
  }),
  makeProduct("3m-super-77", "sprayAdhesive", {
    maker: "3M",
    name: "Super 77",
    summary:
      "Spray adhesive for foam, paper, fabric, and broad laminations that do not need structural strength.",
  }),
  makeProduct("mg-8329tcm", "thermalEpoxy", {
    maker: "MG Chemicals",
    name: "8329TCM",
    thermalConductivity: 1.9,
    fixtureTime: 20,
    potLife: 10,
    summary:
      "Thermally conductive epoxy for heat sinks, power electronics, and sensors that need both bond and heat path.",
  }),
  makeProduct("mg-832ht", "toughenedEpoxy", {
    maker: "MG Chemicals",
    name: "832HT",
    serviceMax: 180,
    serviceMin: -50,
    viscosityClass: "medium",
    gapFill: 1.5,
    substrates: {
      aluminum: 8,
      steel: 8,
      copper: 8,
      glass: 8,
      ceramic: 10,
      fr4: 10,
      carbonFiber: 8,
      abs: 5,
      pvc: 4,
      polycarbonate: 4,
    },
    environment: { humidity: 0.9, fuel: 0.7, immersion: 0.78 },
    summary:
      "High-temperature rigid epoxy for electronics, mechanical protection, chemical resistance, and hot-service assemblies.",
  }),
  makeProduct("arctic-silver-thermal", "thermalEpoxy", {
    maker: "Arctic Silver",
    name: "Thermal Adhesive",
    thermalConductivity: 1.2,
    fixtureTime: 5,
    potLife: 3,
    summary:
      "Fast thermal adhesive for smaller electronics assemblies and quick heat spreader attachment.",
  }),
  makeProduct("scigrip-4", "solventAcrylic", {
    maker: "SCIGRIP",
    name: "4 / Weld-On 4",
    fixtureTime: 2,
    substrates: { acrylic: 10, polycarbonate: 7, petg: 7, polystyrene: 7 },
    compatibleMaterialPairs: [
      ["acrylic", "acrylic"],
      ["polycarbonate", "polycarbonate"],
      ["petg", "petg"],
      ["polystyrene", "polystyrene"],
    ],
    summary:
      "Capillary acrylic solvent cement that can disappear visually in tight, polished acrylic joints.",
  }),
  makeProduct("oatey-pvc-cement", "solventPVC", {
    maker: "Oatey",
    name: "Medium Clear PVC Cement",
    compatibleMaterialPairs: [["pvc", "pvc"]],
    summary:
      "Purpose-built PVC solvent weld for plumbing-style joints and rigid PVC assemblies.",
  }),
  makeProduct("loctite-pl-premium", "constructionAdhesive", {
    maker: "Loctite",
    name: "PL Premium",
    potLife: 20,
    fixtureTime: 30,
    summary:
      "Rugged construction adhesive for wood, masonry, concrete, and rough field-fit structural work.",
  }),
  makeProduct("e6000", "industrialClear", {
    maker: "Eclectic",
    name: "E6000",
    fixtureTime: 120,
    potLife: 15,
    summary:
      "Flexible all-around repair adhesive for trim, leather, glass, fabric, and everyday odd jobs.",
  }),
  makeProduct("gorilla-clear-grip", "industrialClear", {
    maker: "Gorilla",
    name: "Clear Grip",
    fixtureTime: 90,
    potLife: 10,
    summary:
      "Clear flexible repair adhesive for hobby, household, and light mixed-material fixes.",
  }),
  makeProduct("beacon-fabri-tac", "fabricAdhesive", {
    maker: "Beacon",
    name: "Fabri-Tac",
    fixtureTime: 5,
    potLife: 8,
    summary:
      "Fast-tack textile adhesive that stays soft enough for hems, patches, trim, and embellishment work.",
  }),
  makeProduct("barge-all-purpose", "contactCement", {
    maker: "Barge",
    name: "All-Purpose Cement",
    summary:
      "Footwear and leather shop classic for rubber, leather, fabric, and flexible sheet stock.",
  }),
  makeProduct("3m-dp460", "toughenedEpoxy", {
    maker: "3M",
    name: "Scotch-Weld DP460",
    potLife: 60,
    fixtureTime: 240,
    lapShear: 36,
    summary:
      "High-strength toughened epoxy for slower, more deliberate structural assemblies that still need gap filling.",
  }),
  makeProduct("loctite-e120hp", "toughenedEpoxy", {
    maker: "Loctite",
    name: "EA E-120HP",
    potLife: 120,
    fixtureTime: 360,
    lapShear: 34,
    summary:
      "Long-working structural epoxy suited to larger bond lines and multi-part alignment work.",
  }),
  makeProduct("gorilla-epoxy", "clearEpoxy", {
    maker: "Gorilla",
    name: "2 Part Epoxy",
    potLife: 5,
    fixtureTime: 5,
    lapShear: 15,
    clarity: "translucent",
    summary:
      "Fast consumer two-part epoxy for general repairs where convenience matters more than top-tier structural performance.",
  }),
  makeProduct("devcon-5-minute", "clearEpoxy", {
    maker: "Devcon",
    name: "5 Minute Epoxy",
    potLife: 5,
    fixtureTime: 12,
    lapShear: 17,
    clarity: "transparent",
    summary:
      "Quick epoxy for fixtures, hobby work, and light-duty mixed-material repairs.",
  }),
  makeProduct("plexus-ma300", "structuralAcrylic", {
    maker: "Plexus",
    name: "MA300",
    potLife: 15,
    fixtureTime: 20,
    lapShear: 27,
    stress: { impact: 8.6, peel: 7.6 },
    summary:
      "Marine and transportation favorite for composites, metals, and plastics that need a tough structural acrylic.",
  }),
  makeProduct("sikafast-5211", "structuralAcrylic", {
    maker: "Sika",
    name: "SikaFast-5211 NT",
    potLife: 8,
    fixtureTime: 18,
    lapShear: 25,
    summary:
      "Fast structural acrylic with good mixed-material performance in production-style assembly windows.",
  }),
  makeProduct("3m-dp8010", "structuralAcrylic", {
    maker: "3M",
    name: "Scotch-Weld DP8010 Blue",
    potLife: 10,
    fixtureTime: 20,
    lapShear: 18,
    substrates: {
      hdpe: 8,
      abs: 7,
      pvc: 7,
      polycarbonate: 6,
      petg: 7,
    },
    summary:
      "Specialized acrylic for low-surface-energy plastics such as polyethylene without the usual surface treatment drama.",
    cautions: ["Best value shows up when one side is HDPE or another tough polyolefin-like plastic."],
  }),
  makeProduct("loctite-3038", "structuralAcrylic", {
    maker: "Loctite",
    name: "3038",
    potLife: 6,
    fixtureTime: 18,
    lapShear: 17,
    substrates: {
      hdpe: 7,
      abs: 7,
      pvc: 7,
      polycarbonate: 6,
      petg: 6,
    },
    summary:
      "Low-surface-energy acrylic option for polyethylene-heavy assemblies where normal glues usually shrug and fail.",
  }),
  makeProduct("permatex-plastic-welder", "mmaPlasticWelder", {
    maker: "Permatex",
    name: "Plastic Welder",
    potLife: 4,
    fixtureTime: 10,
    lapShear: 20,
    summary:
      "Fast MMA repair adhesive for automotive plastics, tabs, housings, and cracked trim pieces.",
  }),
  makeProduct("loctite-480", "gelCA", {
    maker: "Loctite",
    name: "480 Prism",
    gapFill: 0.2,
    lapShear: 21,
    stress: { impact: 4.8, peel: 4.1 },
    summary:
      "Rubber-toughened black cyanoacrylate that holds up better under impact than standard instant adhesives.",
  }),
  makeProduct("loctite-380-black-max", "gelCA", {
    maker: "Henkel Loctite",
    name: "380 Black Max",
    gapFill: 0.2,
    lapShear: 20,
    serviceMax: 100,
    stress: { impact: 5.2, peel: 4.8 },
    summary:
      "Rubber-toughened black cyanoacrylate for higher peel and impact resistance on metals, elastomers, and small parts.",
  }),
  makeProduct("permabond-731", "thinCA", {
    maker: "Permabond",
    name: "731",
    fixtureTime: 0.2,
    summary:
      "Very fast low-viscosity CA for clean, close-fitting components and rapid production tack.",
  }),
  makeProduct("dymax-621", "uvOptical", {
    maker: "Dymax",
    name: "6-621",
    fixtureTime: 0.4,
    lapShear: 17,
    summary:
      "UV-curable adhesive for glass, clear plastics, and electronics-friendly transparent bonding.",
  }),
  makeProduct("3m-vhb-4910", "foamTape", {
    maker: "3M",
    name: "VHB 4910",
    clarity: "transparent",
    summary:
      "Clear acrylic foam tape for glass and transparent plastic assemblies where visible bond lines matter.",
  }),
  makeProduct("loctite-290", "anaerobicThreadlocker", {
    maker: "Loctite",
    name: "290",
    viscosityClass: "wicking",
    fixtureTime: 10,
    summary:
      "Wicking threadlocker for pre-assembled metal fasteners that need post-assembly vibration resistance.",
  }),
  makeProduct("loctite-680", "anaerobicRetainer", {
    maker: "Loctite",
    name: "680",
    fixtureTime: 10,
    lapShear: 26,
    summary:
      "High-strength retaining compound for tight metal fits that need serious torque and slip resistance.",
  }),
  makeProduct("sikaflex-291", "polyurethaneSealant", {
    maker: "Sika",
    name: "Sikaflex-291",
    potLife: 45,
    fixtureTime: 150,
    environment: { immersion: 0.84 },
    summary:
      "Marine-grade polyurethane sealant adhesive for exterior seams, deck hardware, and wet-service movement joints.",
  }),
  makeProduct("titebond-original", "pvaWood", {
    maker: "Titebond",
    name: "Original Wood Glue",
    serviceMin: 8,
    environment: { humidity: 0.55, immersion: 0.05 },
    summary:
      "Fast, shop-friendly interior wood glue for furniture, cabinetry, and porous close-fitting joints.",
  }),
  makeProduct("titebond-ii", "pvaWood", {
    maker: "Titebond",
    name: "II Premium Wood Glue",
    serviceMin: 6,
    environment: { humidity: 0.7, immersion: 0.16 },
    summary:
      "Water-resistant wood glue that sits between interior PVA and the more outdoor-focused Type I options.",
  }),
  makeProduct("scigrip-16", "solventAcrylic", {
    maker: "SCIGRIP",
    name: "16 / Weld-On 16",
    viscosityClass: "medium",
    gapFill: 0.4,
    fixtureTime: 6,
    substrates: { acrylic: 10, polycarbonate: 6, petg: 5, abs: 6, polystyrene: 6 },
    compatibleMaterialPairs: [
      ["acrylic", "acrylic"],
      ["polycarbonate", "polycarbonate"],
      ["petg", "petg"],
      ["abs", "abs"],
      ["polystyrene", "polystyrene"],
    ],
    summary:
      "Thicker acrylic cement for edge fill, small gaps, and less-than-perfect capillary joints in PMMA work.",
  }),
  makeProduct("oatey-abs-cement", "solventABSStyrene", {
    maker: "Oatey",
    name: "ABS Cement",
    substrates: { abs: 10, pvc: 2, polystyrene: 4 },
    compatibleMaterialPairs: [["abs", "abs"]],
    summary:
      "Purpose-built ABS solvent cement for rigid ABS piping and fabricated ABS assemblies.",
  }),
  makeProduct("3m-90", "sprayAdhesive", {
    maker: "3M",
    name: "Hi-Strength 90",
    fixtureTime: 2,
    serviceMax: 82,
    substrates: {
      wood: 5,
      mdf: 5,
      paper: 8,
      fabric: 8,
      leather: 5,
      abs: 5,
      pvc: 5,
      rubber: 4,
    },
    summary:
      "Higher-strength spray adhesive for laminate and trim work when standard craft sprays are too weak.",
  }),
];

const COMMON_GLUE_EXPANSION = [
  {
    id: "gorilla-super-glue-gel",
    profile: "gelCA",
    maker: "Gorilla",
    name: "Super Glue Gel",
    summary: "Everyday thicker CA gel for quick household repairs on plastics, rubber, wood, and metal.",
  },
  {
    id: "loctite-ultra-gel-control",
    profile: "gelCA",
    maker: "Henkel Loctite",
    name: "Super Glue Ultra Gel Control",
    summary: "Consumer rubber-toughened instant adhesive with better shock handling than plain thin super glue.",
  },
  {
    id: "gorilla-micro-precise",
    profile: "thinCA",
    maker: "Gorilla",
    name: "Micro Precise Super Glue",
    summary: "Fast low-viscosity super glue for clean, precise small-part repairs and hobby work.",
  },
  {
    id: "jbweld-superweld",
    profile: "gelCA",
    maker: "J-B Weld",
    name: "SuperWeld",
    summary: "General-purpose consumer CA for metal, ceramic, plastic, and mixed quick-fix work.",
  },
  {
    id: "elmers-glue-all",
    profile: "craftPva",
    maker: "Elmer's",
    name: "Glue-All",
    summary: "Classic all-purpose PVA for paper, cardboard, craft wood, and light porous assemblies.",
  },
  {
    id: "elmers-school-glue",
    profile: "craftPva",
    maker: "Elmer's",
    name: "School Glue",
    summary: "Light-duty washable PVA for paper crafts, classrooms, and non-structural hobby work.",
  },
  {
    id: "aleenes-original-tacky",
    profile: "craftPva",
    maker: "Aleene's",
    name: "Original Tacky Glue",
    viscosityClass: "high",
    thixotropic: true,
    summary: "High-grab craft glue for fabric, felt, paper, foam, and decorative assembly.",
  },
  {
    id: "mod-podge-matte",
    profile: "craftPva",
    maker: "Mod Podge",
    name: "Matte",
    clarity: "transparent",
    summary: "Decoupage-oriented craft adhesive and sealer for paper, prints, and decorative surfaces.",
  },
  {
    id: "dap-rapidfuse",
    profile: "hybridCA",
    maker: "DAP",
    name: "RapidFuse All Purpose",
    fixtureTime: 0.5,
    gapFill: 3,
    summary: "Fast all-purpose consumer bonder that bridges larger gaps than standard super glue.",
  },
  {
    id: "gorilla-original-glue",
    profile: "structuralPolyurethane",
    maker: "Gorilla",
    name: "Original Gorilla Glue",
    cureFamily: "Moisture-cure polyurethane",
    cureDetail: "Foaming moisture cure polyurethane",
    fixtureTime: 60,
    summary: "Expanding polyurethane glue for wood, stone, ceramic, foam, and rough mixed-material joints.",
  },
  {
    id: "gorilla-max-strength-construction",
    profile: "constructionAdhesive",
    maker: "Gorilla",
    name: "Max Strength Construction Adhesive",
    summary: "High-grab construction adhesive for panels, trim, wood, drywall, masonry, and repair work.",
  },
  {
    id: "liquid-nails-heavy-duty",
    profile: "constructionAdhesive",
    maker: "Liquid Nails",
    name: "Heavy Duty",
    summary: "Field-friendly construction adhesive for wood, drywall, masonry, and general building repairs.",
  },
  {
    id: "liquid-nails-fuze-it",
    profile: "constructionAdhesive",
    maker: "Liquid Nails",
    name: "Fuze*It",
    summary: "More versatile construction adhesive for mixed indoor and outdoor materials with decent initial grab.",
  },
  {
    id: "shoe-goo",
    profile: "industrialClear",
    maker: "Shoe Goo",
    name: "Original",
    summary: "Flexible repair adhesive for footwear, rubber, leather, canvas, and abrasion-prone repairs.",
  },
  {
    id: "amazing-goop",
    profile: "industrialClear",
    maker: "Amazing GOOP",
    name: "Original",
    summary: "General-purpose flexible repair adhesive for household fixes, trim, leather, and odd materials.",
  },
  {
    id: "devcon-5-minute-epoxy",
    profile: "clearEpoxy",
    maker: "Devcon",
    name: "5 Minute Epoxy",
    summary: "Fast two-part epoxy for light repairs, fixtures, and quick mixed-material household work.",
  },
  {
    id: "jbweld-clearweld",
    profile: "clearEpoxy",
    maker: "J-B Weld",
    name: "ClearWeld",
    clarity: "transparent",
    summary: "Clear quick-setting epoxy for visible repairs and mixed-material bench work.",
  },
  {
    id: "jbweld-kwikweld",
    profile: "toughenedEpoxy",
    maker: "J-B Weld",
    name: "KwikWeld",
    potLife: 6,
    fixtureTime: 10,
    summary: "Fast steel-reinforced repair epoxy for brackets, housings, and rapid mechanical fixes.",
  },
  {
    id: "elmers-rubber-cement",
    profile: "contactCement",
    maker: "Elmer's",
    name: "Rubber Cement",
    summary: "Classic paper and photo mounting adhesive with repositionability and soft flexible bonds.",
  },
  {
    id: "surebonder-all-temp",
    profile: "hotMelt",
    maker: "Surebonder",
    name: "All Temp Glue Sticks",
    summary: "General hot-melt sticks for crafts, packaging, displays, and light assembly.",
  },
  {
    id: "adtech-multi-temp",
    profile: "hotMelt",
    maker: "AdTech",
    name: "MultiTemp Glue Sticks",
    summary: "Widely available hot-melt sticks for craft, decor, floral, and light utility bonding.",
  },
  {
    id: "e6000-fabri-fuse",
    profile: "fabricAdhesive",
    maker: "E6000",
    name: "Fabri-Fuse",
    summary: "Fabric-focused flexible adhesive for textiles, trim, patches, and embellishment work.",
  },
  {
    id: "beacon-3-in-1",
    profile: "industrialClear",
    maker: "Beacon",
    name: "3-in-1 Advanced Craft Glue",
    summary: "Clear fast-setting hobby adhesive for crafts, fabric, embellishment, and light repair jobs.",
  },
  {
    id: "3m-30nf",
    profile: "contactCement",
    maker: "3M",
    name: "Fastbond 30NF",
    cureFamily: "Waterborne contact adhesive",
    cureDetail: "Waterborne contact bond",
    summary: "Industrial waterborne contact adhesive for laminate, foam, fabrics, and upholstery work.",
  },
];

const ENGINEERING_GLUE_EXPANSION = [
  {
    id: "3m-2214-regular",
    profile: "toughenedEpoxy",
    maker: "3M",
    name: "Scotch-Weld 2214 Regular",
    cureFamily: "Heat-cure epoxy",
    cureDetail: "1-part heat cure epoxy paste",
    potLife: 9999,
    fixtureTime: 40,
    serviceMax: 121,
    summary: "Low-temperature-curing one-part epoxy for structural assemblies that can be oven processed.",
  },
  {
    id: "3m-1469",
    profile: "toughenedEpoxy",
    maker: "3M",
    name: "Scotch-Weld 1469",
    cureFamily: "Heat-cure epoxy",
    cureDetail: "1-part heat cure epoxy",
    potLife: 9999,
    fixtureTime: 120,
    serviceMax: 121,
    summary: "Low-viscosity one-part heat-cure epoxy for bondlines and potting-style structural use.",
  },
  {
    id: "3m-dp105",
    profile: "clearEpoxy",
    maker: "3M",
    name: "Scotch-Weld DP105 Clear",
    serviceMax: 82,
    summary: "Very flexible clear epoxy for visible bond lines that need compliance more than stiffness.",
  },
  {
    id: "3m-dp110",
    profile: "flexibleEpoxy",
    maker: "3M",
    name: "Scotch-Weld DP110",
    serviceMax: 82,
    summary: "General-purpose flexible epoxy for metal, composites, and mixed-material peel-prone joints.",
  },
  {
    id: "3m-dp190",
    profile: "flexibleEpoxy",
    maker: "3M",
    name: "Scotch-Weld DP190",
    serviceMax: 82,
    potLife: 90,
    fixtureTime: 240,
    summary: "Longer-open-time flexible epoxy for assemblies that need more working time and movement tolerance.",
  },
  {
    id: "3m-dp490",
    profile: "toughenedEpoxy",
    maker: "3M",
    name: "Scotch-Weld DP490",
    serviceMax: 82,
    potLife: 90,
    fixtureTime: 240,
    summary: "Very long open-time structural epoxy for larger assemblies and slower alignment work.",
  },
  {
    id: "3m-dp270",
    profile: "toughenedEpoxy",
    maker: "3M",
    name: "Scotch-Weld DP270",
    serviceMax: 82,
    potLife: 70,
    fixtureTime: 180,
    lapShear: 12,
    summary: "Rigid non-corrosive epoxy often used for potting and electronics-adjacent structural bonding.",
  },
  {
    id: "loctite-ea9430",
    profile: "toughenedEpoxy",
    maker: "Henkel Loctite",
    name: "EA 9430",
    serviceMax: 82,
    potLife: 60,
    fixtureTime: 300,
    summary: "Modified epoxy with a useful balance of shear and peel for general structural assembly.",
  },
  {
    id: "loctite-e20hp",
    profile: "toughenedEpoxy",
    maker: "Henkel Loctite",
    name: "EA E-20HP",
    serviceMax: 80,
    potLife: 20,
    fixtureTime: 300,
    summary: "Toughened structural epoxy with concrete-rated heritage and general-purpose metal bonding utility.",
  },
  {
    id: "loctite-e30ut",
    profile: "flexibleEpoxy",
    maker: "Henkel Loctite",
    name: "EA E-30UT",
    serviceMax: 82,
    potLife: 30,
    fixtureTime: 1080,
    summary: "Ultra-tough structural epoxy with extended work life for demanding peel and impact conditions.",
  },
  {
    id: "loctite-e30cl",
    profile: "clearEpoxy",
    maker: "Henkel Loctite",
    name: "EA E-30CL",
    serviceMax: 95,
    clarity: "transparent",
    potLife: 30,
    fixtureTime: 300,
    summary: "Clear glass-bonding epoxy for transparent assemblies and visible joints.",
  },
  {
    id: "loctite-e60hp",
    profile: "toughenedEpoxy",
    maker: "Henkel Loctite",
    name: "EA E-60HP",
    serviceMax: 120,
    potLife: 60,
    fixtureTime: 240,
    summary: "Fast-curing structural epoxy with better high-temperature headroom than the common 80-82 °C systems.",
  },
  {
    id: "loctite-e60nc",
    profile: "toughenedEpoxy",
    maker: "Henkel Loctite",
    name: "EA E-60NC",
    serviceMax: 121,
    potLife: 60,
    fixtureTime: 240,
    lapShear: 12,
    summary: "Flowable non-corrosive epoxy used for potting, encapsulation, and electrical/mechanical bonding.",
  },
  {
    id: "araldite-2014-2",
    profile: "toughenedEpoxy",
    maker: "Araldite",
    name: "2014-2",
    serviceMax: 100,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Chemically resistant paste epoxy for tougher service conditions and more controlled bondline placement.",
  },
  {
    id: "araldite-2015-1",
    profile: "flexibleEpoxy",
    maker: "Araldite",
    name: "2015-1",
    serviceMax: 80,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Toughened gap-filling epoxy often used on composites and GRP/SMC where some flexibility helps.",
  },
  {
    id: "epo-tek-353nd",
    profile: "toughenedEpoxy",
    maker: "EPO-TEK",
    name: "353ND",
    cureFamily: "Heat-cure epoxy",
    cureDetail: "2-part heat-accelerated epoxy",
    serviceMax: 225,
    serviceMin: -55,
    potLife: 120,
    fixtureTime: 10,
    summary: "High-temperature electronics and optical packaging epoxy with very wide service capability.",
  },
  {
    id: "master-bond-ep21tdcht-lo",
    profile: "toughenedEpoxy",
    maker: "Master Bond",
    name: "EP21TDCHT-LO",
    serviceMax: 177,
    serviceMin: -269,
    potLife: 60,
    fixtureTime: 2880,
    summary: "Low-outgassing toughened epoxy for cryogenic, aerospace, and vacuum-adjacent environments.",
  },
  {
    id: "lord-3170",
    profile: "toughenedEpoxy",
    maker: "LORD / Parker",
    name: "3170 Cryogenic Epoxy",
    serviceMax: 148,
    serviceMin: -269,
    potLife: 60,
    fixtureTime: 5760,
    summary: "Cryogenic-rated structural epoxy for very low-temperature service where standard systems become risky.",
  },
  {
    id: "lord-320-310b",
    profile: "toughenedEpoxy",
    maker: "LORD / Parker",
    name: "320/310-B Epoxy Adhesive",
    serviceMax: 163,
    potLife: 30,
    fixtureTime: 1440,
    summary: "Toughened epoxy with good peel response and rubber-bonding credibility when properly surface treated.",
  },
  {
    id: "teroson-ep5089",
    profile: "toughenedEpoxy",
    maker: "Henkel Loctite",
    name: "Teroson EP 5089",
    cureFamily: "Heat-cure epoxy",
    cureDetail: "1-part automotive heat cure epoxy",
    serviceMax: 90,
    potLife: 9999,
    fixtureTime: 25,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Automotive hem-flange and crash-durable heat-cure epoxy for production-style metal assembly.",
  },
  {
    id: "delo-monopox-ml5249",
    profile: "toughenedEpoxy",
    maker: "DELO",
    name: "MONOPOX ML5249",
    cureFamily: "Heat-cure epoxy",
    cureDetail: "1-part electronics-grade heat cure epoxy",
    serviceMax: 150,
    potLife: 9999,
    fixtureTime: 30,
    summary: "Electronics-focused one-part heat-cure epoxy for automated dispense and oven-cure manufacturing flows.",
  },
  {
    id: "lord-309-1d",
    profile: "toughenedEpoxy",
    maker: "LORD / Parker",
    name: "309-1D Specialty Epoxy",
    serviceMax: 148,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Gap-filling specialty epoxy with good bondline control and more demanding structural positioning.",
  },
  {
    id: "lord-304",
    profile: "toughenedEpoxy",
    maker: "LORD / Parker",
    name: "304 Epoxy Adhesive",
    serviceMax: 148,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "General-purpose non-sag epoxy for gap-filling metal, composite, and plastic assembly.",
  },
  {
    id: "lord-305",
    profile: "toughenedEpoxy",
    maker: "LORD / Parker",
    name: "305 Epoxy Adhesive",
    serviceMax: 148,
    viscosityClass: "medium",
    thixotropic: false,
    summary: "Self-leveling epoxy with stronger chemical resistance and good general structural performance.",
  },
  {
    id: "lord-360",
    profile: "toughenedEpoxy",
    maker: "LORD / Parker",
    name: "360 Rapid Cure Epoxy",
    serviceMax: 148,
    potLife: 3,
    fixtureTime: 30,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Rapid-cure paste epoxy for quick structural repairs and production fixtures.",
  },
  {
    id: "3m-dp100fr",
    profile: "toughenedEpoxy",
    maker: "3M",
    name: "Scotch-Weld DP100FR",
    serviceMax: 82,
    summary: "Flame-retardant rigid epoxy for electronics housings and assemblies that need UL-style behavior.",
  },
  {
    id: "lord-403",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "403 Acrylic Adhesive",
    serviceMax: 148,
    potLife: 4,
    fixtureTime: 30,
    summary: "Fast-fixturing general-purpose structural acrylic for metals, plastics, and FRP.",
  },
  {
    id: "lord-406",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "406 Acrylic Adhesive",
    serviceMax: 148,
    potLife: 8,
    fixtureTime: 45,
    summary: "Medium-work-time structural acrylic with balanced handling and durable mixed-material performance.",
  },
  {
    id: "lord-410",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "410 Acrylic Adhesive",
    serviceMax: 148,
    potLife: 20,
    fixtureTime: 90,
    summary: "Longer-open-time general-purpose acrylic for bigger bonded assemblies and slower line speeds.",
  },
  {
    id: "lord-506",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "506 Plastic Bonding Acrylic",
    serviceMax: 148,
    substrates: { abs: 9, pvc: 9, acrylic: 8, polycarbonate: 8, petg: 8 },
    summary: "Plastic-bonding acrylic formulated for thermoplastics and thermosets with good shock resistance.",
  },
  {
    id: "lord-606",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "606 Composite / Cross-Bonding Acrylic",
    serviceMax: 148,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Cross-bonding acrylic for composite-to-metal and plastic-to-metal assemblies with high toughness.",
  },
  {
    id: "lord-661",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "661 Long Work Time Composite Acrylic",
    serviceMax: 148,
    potLife: 15,
    fixtureTime: 120,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Longer-work-time composite acrylic for larger beads, gaps, and panel-bonding operations.",
  },
  {
    id: "lord-810s",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "810S Low Read-Through Acrylic",
    serviceMax: 148,
    summary: "Low-read-through acrylic for visible exterior panels and flexible substrates where cosmetic distortion matters.",
  },
  {
    id: "lord-852s",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "852S Toughened Structural Acrylic",
    serviceMax: 148,
    potLife: 25,
    fixtureTime: 300,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Longer-open-time version of a highly impact-tolerant toughened acrylic system.",
  },
  {
    id: "lord-maxlok-t6s",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "Maxlok T6S",
    serviceMax: 148,
    viscosityClass: "very-high",
    thixotropic: true,
    substrates: { aluminum: 10, steel: 10, abs: 7, pvc: 7, carbonFiber: 8 },
    summary: "High-strength metal-bonding acrylic tuned for coated metals and automotive-style surfaces.",
  },
  {
    id: "lord-5206",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "5206 Acrylic Adhesive",
    serviceMax: 148,
    viscosityClass: "high",
    summary: "High-impact, high-peel acrylic with bondline control credibility for structural panel bonding.",
  },
  {
    id: "plexus-ma300",
    profile: "structuralAcrylic",
    maker: "ITW Plexus",
    name: "MA300",
    serviceMax: 121,
    potLife: 5,
    fixtureTime: 20,
    summary: "Fast-cure structural MMA for composites, plastics, and mixed-material industrial assemblies.",
  },
  {
    id: "plexus-ma832",
    profile: "structuralAcrylic",
    maker: "ITW Plexus",
    name: "MA832",
    serviceMax: 121,
    substrates: { carbonFiber: 10, abs: 7, pvc: 7, aluminum: 8, steel: 8 },
    summary: "Composite-bonding MMA favored where primerless composite adhesion and production handling matter.",
  },
  {
    id: "loctite-h3300",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA H3300 Speedbonder",
    serviceMax: 82,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Fast-fixture thixotropic methacrylate for gap-tolerant structural assembly.",
  },
  {
    id: "loctite-h3101",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA H3101 Speedbonder",
    serviceMax: 82,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "High-thixotropy methacrylate with moderate fixture time and broad structural assembly use.",
  },
  {
    id: "loctite-h8000",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA H8000 Speedbonder",
    serviceMax: 100,
    substrates: { fr4: 8, carbonFiber: 9, abs: 8, pvc: 8, polycarbonate: 8 },
    summary: "Toughened MMA for composites, ferrites, FRP, and engineering plastics.",
  },
  {
    id: "loctite-h8100",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA H8100 Speedbonder",
    serviceMax: 100,
    summary: "Toughened methacrylate for high peel, high impact, and low-temperature durability.",
  },
  {
    id: "loctite-h8500",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA H8500 Speedbonder",
    serviceMax: 100,
    potLife: 30,
    fixtureTime: 120,
    summary: "Long-work-time methacrylate for larger structural assemblies and longer application windows.",
  },
  {
    id: "loctite-h4800",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA H4800 Speedbonder",
    serviceMax: 100,
    potLife: 30,
    substrates: { pvc: 9, acrylic: 9, polycarbonate: 8, petg: 8, abs: 8 },
    summary: "Longer-open-time methacrylate aimed at PVC, acrylic, polycarbonate, and similar plastics.",
  },
  {
    id: "loctite-h4500",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA H4500 Speedbonder",
    serviceMax: 100,
    potLife: 15,
    fixtureTime: 45,
    summary: "High-temperature-capable methacrylate for demanding structural bonding with more thermal headroom.",
  },
  {
    id: "loctite-3034",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA 3034",
    serviceMax: 100,
    viscosityClass: "high",
    thixotropic: true,
    substrates: { hdpe: 8, abs: 7, pvc: 6, petg: 6, polycarbonate: 5 },
    summary: "Low-surface-energy plastic bonder with built-in bond-gap control orientation.",
  },
  {
    id: "loctite-3035",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA 3035",
    serviceMax: 80,
    substrates: { hdpe: 8, abs: 7, pvc: 6, petg: 6, polycarbonate: 5 },
    summary: "Two-part methacrylate for HDPE and PP where primerless LSE bonding is the main requirement.",
  },
  {
    id: "loctite-a671",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA A-671",
    serviceMax: 150,
    substrates: { steel: 8, fr4: 7, ceramic: 7 },
    summary: "Magnet-bonding acrylic for rare-earth, ferrite, and motor-style assemblies.",
  },
  {
    id: "lord-5801s",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "5801S Low-Viscosity Acrylic",
    serviceMax: 148,
    viscosityClass: "low",
    thixotropic: false,
    potLife: 5,
    fixtureTime: 180,
    summary: "Low-viscosity acrylic with UV photo-initiator help for tighter geometries and fast cure support.",
  },
  {
    id: "loctite-aa324",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA 324",
    cureFamily: "Activator-cured acrylic",
    cureDetail: "Activator-cured toughened acrylic",
    serviceMax: 120,
    substrates: { aluminum: 8, steel: 8, ferrite: 0 },
    summary: "Impact-tolerant activator-cured acrylic for metals and motor-style assemblies.",
  },
  {
    id: "loctite-aa325",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA 325",
    cureFamily: "Activator-cured acrylic",
    cureDetail: "Activator-cured modified acrylic",
    serviceMax: 120,
    summary: "Modified acrylic for thermal-cycling environments and activator-based structural bonding.",
  },
  {
    id: "loctite-aa326",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA 326",
    cureFamily: "Activator-cured acrylic",
    cureDetail: "Activator-cured modified acrylic",
    serviceMax: 120,
    summary: "Fast activator-cured acrylic with strong shear for metal-to-metal assemblies.",
  },
  {
    id: "loctite-aa331",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA 331",
    cureFamily: "Activator-cured acrylic",
    cureDetail: "Activator-cured motor-bonding acrylic",
    serviceMax: 150,
    summary: "Motor and magnet bonding acrylic with stronger temperature range than general-purpose activator systems.",
  },
  {
    id: "loctite-aa332",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA 332",
    cureFamily: "Activator-cured acrylic",
    cureDetail: "Activator-cured motor-bonding acrylic",
    serviceMax: 150,
    summary: "Impact-resistant acrylic for magnet and motor component bonding.",
  },
  {
    id: "loctite-aa334",
    profile: "structuralAcrylic",
    maker: "Henkel Loctite",
    name: "AA 334",
    cureFamily: "Activator-cured acrylic",
    cureDetail: "Filled activator-cured acrylic",
    serviceMax: 175,
    viscosityClass: "high",
    thixotropic: true,
    summary: "Filled acrylic for gap management and hotter-service motor-style bonds.",
  },
  {
    id: "loctite-414",
    profile: "thinCA",
    maker: "Henkel Loctite",
    name: "414",
    serviceMax: 80,
    summary: "General-purpose low-viscosity ethyl cyanoacrylate for rapid close-fit bonding.",
  },
  {
    id: "loctite-496",
    profile: "thinCA",
    maker: "Henkel Loctite",
    name: "496",
    serviceMax: 80,
    substrates: { metal: 0, aluminum: 8, steel: 8, copper: 8, rubber: 7, abs: 7 },
    summary: "General engineering-grade instant adhesive with broad metals/plastics/rubber utility.",
  },
  {
    id: "3m-pr100",
    profile: "thinCA",
    maker: "3M",
    name: "Scotch-Weld PR100",
    serviceMax: 82,
    summary: "Plastic and rubber oriented engineering-grade CA for fast close-fitting bonds.",
  },
  {
    id: "3m-si1500",
    profile: "gelCA",
    maker: "3M",
    name: "Scotch-Weld SI1500",
    serviceMax: 82,
    summary: "Surface-insensitive CA with better tolerance for porous or slightly contaminated substrates.",
  },
  {
    id: "3m-rt5000b",
    profile: "gelCA",
    maker: "3M",
    name: "Scotch-Weld RT5000B",
    serviceMax: 82,
    stress: { impact: 5.2, peel: 4.8 },
    summary: "Rubber-toughened CA for more impact and vibration resistance than general-purpose instant adhesives.",
  },
  {
    id: "3m-ca40",
    profile: "thinCA",
    maker: "3M",
    name: "Scotch-Weld CA40",
    serviceMax: 82,
    fixtureTime: 0.15,
    summary: "Very fast engineering CA for quick fixture on close-fitting parts.",
  },
  {
    id: "3m-ca100",
    profile: "gelCA",
    maker: "3M",
    name: "Scotch-Weld CA100",
    serviceMax: 100,
    summary: "High-peel, thermal-shock-oriented CA for metal-heavy small-part assemblies.",
  },
  {
    id: "born2bond-ultra",
    profile: "thinCA",
    maker: "Born2Bond",
    name: "Ultra",
    serviceMax: 100,
    summary: "Low-bloom, lower-odor instant adhesive for cleaner cosmetic results on visible assemblies.",
  },
  {
    id: "loctite-si5910",
    profile: "rtvSilicone",
    maker: "Henkel Loctite",
    name: "SI 5910",
    serviceMax: 200,
    serviceMin: -55,
    viscosityClass: "very-high",
    gapFill: 6,
    summary: "High-temperature oxime-cure silicone gasket maker for hot mechanical sealing.",
  },
  {
    id: "loctite-uk-u05fl",
    profile: "structuralPolyurethane",
    maker: "Henkel Loctite",
    name: "UK U-05FL",
    serviceMax: 80,
    summary: "Flexible industrial polyurethane adhesive for resilient bond lines in mixed-material assemblies.",
  },
  {
    id: "loctite-uk-u09fl",
    profile: "structuralPolyurethane",
    maker: "Henkel Loctite",
    name: "UK U-09FL",
    serviceMax: 80,
    clarity: "transparent",
    summary: "Ultra-clear flexible polyurethane for transparent or translucent resilient bond lines.",
  },
  {
    id: "loctite-uk-3364",
    profile: "structuralPolyurethane",
    maker: "Henkel Loctite",
    name: "UK 3364",
    serviceMax: 80,
    summary: "Flame-retardant rigid polyurethane used for electronics, potting, and structural encapsulation work.",
  },
  {
    id: "loctite-uk-1366-5452",
    profile: "structuralPolyurethane",
    maker: "Henkel Loctite",
    name: "UK 1366 B10 / UK 5452",
    serviceMax: 80,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Hard-elastic structural polyurethane for metal and plastic bonding with good gap tolerance.",
  },
  {
    id: "loctite-uk-1351-5452",
    profile: "structuralPolyurethane",
    maker: "Henkel Loctite",
    name: "UK 1351 B25 / UK 5452",
    serviceMax: 100,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Structural polyurethane used in marine, wind, and composite-heavy applications.",
  },
  {
    id: "lord-7542",
    profile: "structuralPolyurethane",
    maker: "LORD / Parker",
    name: "7542 Urethane Adhesive",
    serviceMax: 116,
    summary: "Structural urethane aimed at FRP, SMC, and plastic assembly with good elongation.",
  },
  {
    id: "lord-7545",
    profile: "structuralPolyurethane",
    maker: "LORD / Parker",
    name: "7545 Urethane Adhesive",
    serviceMax: 116,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Non-sag structural urethane for wide-curative-range composite and plastic assembly.",
  },
  {
    id: "lord-7800",
    profile: "structuralPolyurethane",
    maker: "LORD / Parker",
    name: "7800 Urethane Adhesive",
    serviceMax: 116,
    summary: "Rapid-strength structural urethane with lower exotherm and good composite/plastic performance.",
  },
  {
    id: "lord-7610dtm",
    profile: "polyurethaneSealant",
    maker: "LORD / Parker",
    name: "7610DTM Direct-to-Metal Urethane",
    serviceMax: 116,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Single-component urethane seam sealer and bond/seal option with direct-to-metal orientation.",
  },
  {
    id: "lord-7550",
    profile: "structuralPolyurethane",
    maker: "LORD / Parker",
    name: "7550 Optically Clear Urethane",
    serviceMax: 116,
    clarity: "transparent",
    summary: "Non-yellowing optically clear urethane for visible flexible bond lines and encapsulation-style uses.",
  },
  {
    id: "lord-7555",
    profile: "polyurethaneSealant",
    maker: "LORD / Parker",
    name: "7555 Bright White Urethane",
    serviceMax: 116,
    viscosityClass: "very-high",
    thixotropic: true,
    summary: "Bright-white non-sag urethane for bond-and-seal applications with outdoor durability.",
  },
  {
    id: "lord-7556",
    profile: "polyurethaneSealant",
    maker: "LORD / Parker",
    name: "7556 Translucent Urethane",
    serviceMax: 116,
    viscosityClass: "very-high",
    thixotropic: true,
    clarity: "translucent",
    summary: "Translucent non-sag urethane with environmental and chemical resistance for bond-and-seal use.",
  },
  {
    id: "3m-dp6310ns",
    profile: "structuralPolyurethane",
    maker: "3M",
    name: "Scotch-Weld DP6310NS",
    serviceMax: 82,
    summary: "Semi-rigid urethane for multi-material bonding and more compliant structural joints.",
  },
  {
    id: "3m-dp604ns",
    profile: "structuralPolyurethane",
    maker: "3M",
    name: "Scotch-Weld DP604NS",
    serviceMax: 82,
    summary: "Flexible non-sag urethane for peel-heavy dynamic assemblies.",
  },
  {
    id: "3m-dp605ns",
    profile: "structuralPolyurethane",
    maker: "3M",
    name: "Scotch-Weld DP605NS",
    serviceMax: 82,
    summary: "Semi-rigid non-sag urethane for plastic and composite assembly where flexibility still matters.",
  },
  {
    id: "3m-dp640",
    profile: "structuralPolyurethane",
    maker: "3M",
    name: "Scotch-Weld DP640",
    serviceMax: 82,
    summary: "Tough flexible urethane for more compliant mixed-material structural bonding.",
  },
  {
    id: "3m-ts230",
    profile: "structuralPolyurethane",
    maker: "3M",
    name: "Scotch-Weld TS230",
    cureFamily: "PUR hot melt",
    cureDetail: "Reactive polyurethane hot melt",
    serviceMax: 82,
    viscosityClass: "medium",
    thixotropic: false,
    fixtureTime: 2,
    summary: "Reactive PUR hot melt for fast-fixture plastic-to-metal and appliance-style assembly.",
  },
  {
    id: "loctite-3631-hysol",
    profile: "structuralPolyurethane",
    maker: "Henkel Loctite",
    name: "3631 Hysol Hot Melt",
    cureFamily: "PUR hot melt",
    cureDetail: "Reactive polyurethane hot melt",
    serviceMax: 130,
    viscosityClass: "medium",
    thixotropic: false,
    fixtureTime: 2,
    summary: "Reactive PUR hot melt for higher-temperature flexible structural assembly.",
  },
  {
    id: "loctite-603",
    profile: "anaerobicRetainer",
    maker: "Henkel Loctite",
    name: "603",
    summary: "Low-viscosity oil-tolerant retaining compound for cylindrical metal fits and repairs.",
  },
  {
    id: "loctite-609",
    profile: "anaerobicRetainer",
    maker: "Henkel Loctite",
    name: "609",
    summary: "General-purpose low-viscosity retaining compound for shafts, bushings, and bearings.",
  },
  {
    id: "loctite-660",
    profile: "anaerobicRetainer",
    maker: "Henkel Loctite",
    name: "660 Quick Metal",
    viscosityClass: "very-high",
    thixotropic: true,
    gapFill: 0.5,
    summary: "Large-gap metal retaining and slip-fit repair compound for worn cylindrical parts.",
  },
  {
    id: "loctite-263",
    profile: "anaerobicThreadlocker",
    maker: "Henkel Loctite",
    name: "263",
    serviceMax: 180,
    summary: "High-strength oil-tolerant threadlocker for permanent or hard-service fastener retention.",
  },
  {
    id: "loctite-277",
    profile: "anaerobicThreadlocker",
    maker: "Henkel Loctite",
    name: "277",
    serviceMax: 150,
    viscosityClass: "high",
    thixotropic: true,
    summary: "High-strength threadlocker for larger-diameter fasteners and studlocking.",
  },
  {
    id: "3m-tl22",
    profile: "anaerobicThreadlocker",
    maker: "3M",
    name: "Scotch-Weld TL22",
    serviceMax: 149,
    viscosityClass: "medium",
    summary: "Low-strength threadlocker for smaller fasteners and adjustable assemblies.",
  },
  {
    id: "3m-tl42",
    profile: "anaerobicThreadlocker",
    maker: "3M",
    name: "Scotch-Weld TL42",
    serviceMax: 149,
    summary: "Medium-strength general-purpose threadlocker for serviceable fasteners.",
  },
  {
    id: "3m-tl43",
    profile: "anaerobicThreadlocker",
    maker: "3M",
    name: "Scotch-Weld TL43",
    serviceMax: 149,
    summary: "Oil-tolerant medium-strength threadlocker for dirtier or less pristine metal hardware.",
  },
  {
    id: "3m-tl71",
    profile: "anaerobicThreadlocker",
    maker: "3M",
    name: "Scotch-Weld TL71",
    serviceMax: 204,
    summary: "High-strength red studlocking threadlocker for hotter permanent metal fastening.",
  },
  {
    id: "3m-tl90",
    profile: "anaerobicThreadlocker",
    maker: "3M",
    name: "Scotch-Weld TL90",
    serviceMax: 149,
    viscosityClass: "wicking",
    summary: "Wicking penetrating threadlocker for already-assembled fasteners.",
  },
  {
    id: "permabond-hm160",
    profile: "anaerobicRetainer",
    maker: "Permabond",
    name: "HM160",
    serviceMax: 180,
    summary: "High-strength retaining compound in the same slot as Loctite 638-style cylindrical bonding.",
  },
  {
    id: "permabond-hh040",
    profile: "anaerobicThreadlocker",
    maker: "Permabond",
    name: "HH040",
    serviceMax: 200,
    summary: "Permanent high-strength threadlocker for hot-service and high-security metal fasteners.",
  },
  {
    id: "threebond-1305n",
    profile: "anaerobicThreadlocker",
    maker: "ThreeBond",
    name: "1305N",
    serviceMax: 150,
    summary: "Medium-strength engineering threadlocker for serviceable metal fasteners and general machinery use.",
  },
  {
    id: "3m-vhb-4910",
    profile: "foamTape",
    maker: "3M",
    name: "VHB 4910",
    clarity: "transparent",
    summary: "Clear acrylic foam tape for glass, clear plastic, and cosmetically visible mounting.",
  },
  {
    id: "3m-vhb-4941",
    profile: "foamTape",
    maker: "3M",
    name: "VHB 4941",
    summary: "General-purpose structural acrylic foam tape for mixed metal and plastic panel bonding.",
  },
  {
    id: "permabond-uv610",
    profile: "uvAcrylate",
    maker: "Permabond",
    name: "UV610",
    summary: "UV/visible cure acrylate for glass bonding and fast transparent assembly.",
  },
  {
    id: "loctite-aa3494",
    profile: "uvAcrylate",
    maker: "Henkel Loctite",
    name: "AA 3494",
    serviceMax: 150,
    summary: "UV/visible light cure acrylic for glass and transparent component bonding.",
  },
  {
    id: "loctite-aa352",
    profile: "uvAcrylate",
    maker: "Henkel Loctite",
    name: "AA 352",
    serviceMax: 121,
    cureDetail: "UV, heat, or activator cure acrylic",
    summary: "Dual-path cure acrylic for metal, glass, and plastic assemblies where light access may be partial.",
  },
  {
    id: "lord-cooltherm-tc850",
    profile: "structuralAcrylic",
    maker: "LORD / Parker",
    name: "CoolTherm TC-850",
    thermalConductivity: 0.9,
    serviceMax: 148,
    stress: { peel: 8.1, impact: 8.2 },
    summary: "Thermally conductive structural acrylic with high elongation for battery and electronics assemblies.",
  },
  {
    id: "lord-cooltherm-tc2002",
    profile: "thermalEpoxy",
    maker: "LORD / Parker",
    name: "CoolTherm TC-2002",
    thermalConductivity: 2,
    serviceMax: 148,
    summary: "Thermally conductive adhesive for bare-metal heat paths, electronics, and power modules.",
  },
  {
    id: "ips-weld-on-3",
    profile: "solventAcrylic",
    maker: "IPS Weld-On",
    name: "#3",
    fixtureTime: 1,
    substrates: { acrylic: 10, polystyrene: 7, polycarbonate: 7 },
    compatibleMaterialPairs: [
      ["acrylic", "acrylic"],
      ["polystyrene", "polystyrene"],
      ["polycarbonate", "polycarbonate"],
    ],
    summary: "Very thin solvent cement for capillary acrylic bonding and clean PMMA edges.",
  },
  {
    id: "tamiya-extra-thin-cement",
    profile: "solventABSStyrene",
    maker: "Tamiya",
    name: "Extra Thin Cement",
    fixtureTime: 0.7,
    substrates: { polystyrene: 10, abs: 6 },
    compatibleMaterialPairs: [
      ["polystyrene", "polystyrene"],
      ["abs", "abs"],
    ],
    summary: "Water-thin hobby solvent cement for close-fitting polystyrene model parts and some ABS parts.",
    cautions: ["Use CA or epoxy for resin, metal, rubbery elastomers, or unknown plastics."],
    referenceUrl: "https://www.tamiyausa.com/shop/finishing/extra-thin-cement-2/",
  },
  {
    id: "pc-dcm-chloroform-solvent-weld",
    profile: "solventPolycarbonate",
    maker: "Lab solvent method",
    name: "DCM / chloroform PC solvent weld",
    fixtureTime: 1,
    lapShear: null,
    substrates: { polycarbonate: 10 },
    compatibleMaterialPairs: [["polycarbonate", "polycarbonate"]],
    summary:
      "Raw-solvent route for polycarbonate-to-polycarbonate capillary or edge-dip welding when a commercial PC cement is not the right fit.",
    professionalUseOnly: true,
    rawSolventMethod: true,
    chlorinatedSolvent: true,
    containsMethyleneChloride: true,
    containsChloroform: true,
    cautions: [
      "Treat this as industrial lab work, not a consumer glue recommendation; methylene chloride and chloroform require strict ventilation, PPE, and SDS controls.",
      "Solvent-welded polycarbonate loses impact strength at the joint and can craze if stressed.",
    ],
    referenceUrl: "https://www.eplastics.com/pdf/polycarbonate-fabrication-manual.pdf",
  },
];

GLUES.push(
  ...COMMON_GLUE_EXPANSION.map(({ id, profile, ...overrides }) =>
    makeProduct(id, profile, overrides),
  ),
  ...ENGINEERING_GLUE_EXPANSION.map(({ id, profile, ...overrides }) =>
    makeProduct(id, profile, overrides),
  ),
);

const REFERENCE_LIBRARY = Array.isArray(globalThis.MCMASTER_REFERENCE_FAMILIES)
  ? globalThis.MCMASTER_REFERENCE_FAMILIES
  : [];
let MCMASTER_PIPELINE_STATS = globalThis.MCMASTER_PIPELINE_STATS ?? {};
const TDS_MANUAL_REFERENCE_FAMILIES = Array.isArray(globalThis.TDS_MANUAL_REFERENCE_FAMILIES)
  ? globalThis.TDS_MANUAL_REFERENCE_FAMILIES
  : [];
let TDS_MANUAL_STATS = globalThis.TDS_MANUAL_STATS ?? {};

const normalizeCatalogString = (value) =>
  (value ?? "")
    .toLowerCase()
    .replace(/henkel /g, "")
    .replace(/lord\s*\/\s*parker/g, "lord")
    .replace(/j[-\s]?b\s*weld/g, "jbweld")
    .replace(/3m\s*scotch[-\s]?weld/g, "3m")
    .replace(/scotch[-\s]?weld/g, "")
    .replace(/speedbonder/g, "")
    .replace(/[^a-z0-9]+/g, "");

const normalizeMakerKey = (maker) => {
  const token = normalizeCatalogString(maker);
  if (!token) return "";
  if (token.includes("loctite")) return "loctite";
  if (token.includes("3m")) return "3m";
  if (token.includes("permabond")) return "permabond";
  if (token.includes("lord")) return "lord";
  if (token.includes("plexus")) return "plexus";
  if (token.includes("sika")) return "sika";
  if (token.includes("gorilla")) return "gorilla";
  if (token.includes("jbweld")) return "jbweld";
  if (token.includes("devcon")) return "devcon";
  if (token.includes("permatex")) return "permatex";
  if (token.includes("momentive")) return "momentive";
  if (token.includes("dowcorning")) return "dowcorning";
  if (token.includes("weldon")) return "weldon";
  return token;
};

const normalizeProductNameKey = (maker, name) => {
  const makerKey = normalizeMakerKey(maker);
  let nameKey = normalizeCatalogString(name);

  [
    /^loctite/,
    /^3m/,
    /^henkelloctite/,
    /^lord/,
    /^permabond/,
    /^plexus/,
    /^sika/,
    /^gorilla/,
    /^jbweld/,
    /^devcon/,
    /^permatex/,
    /^momentive/,
    /^dowcorning/,
    /^weldon/,
  ].forEach((pattern) => {
    nameKey = nameKey.replace(pattern, "");
  });

  if (makerKey === "loctite") {
    nameKey = nameKey.replace(/^(aa|ea|si|uk|hy)(?=[a-z]?\d)/, "");
  }

  return nameKey;
};

const buildCatalogKey = ({ maker, name }) => {
  const makerKey = normalizeMakerKey(maker);
  const nameKey = normalizeProductNameKey(maker, name);
  return `${makerKey}:${nameKey}`;
};

const buildReferenceFamilyKey = (family) =>
  `${normalizeMakerKey(family.manufacturer)}:${normalizeProductNameKey(
    family.manufacturer,
    family.familyName,
  )}`;

const mergeObservedCatalogData = (existing, generated) => {
  [
    "serviceMin",
    "serviceMax",
    "gapFill",
    "potLife",
    "fixtureTime",
    "lapShear",
    "thermalConductivity",
    "clarity",
    "viscosityClass",
    ...OBSERVED_TDS_FIELDS,
  ].forEach((field) => {
    if (
      hasCatalogValue(generated[field]) &&
      !generated.profileDerivedFields?.includes(field)
    ) {
      existing[field] = generated[field];
      existing.profileDerivedFields = (existing.profileDerivedFields ?? []).filter(
        (derivedField) => derivedField !== field,
      );
    }
  });
  if (
    generated.thixotropic !== undefined &&
    !generated.profileDerivedFields?.includes("thixotropic")
  ) {
    existing.thixotropic = generated.thixotropic;
    existing.profileDerivedFields = (existing.profileDerivedFields ?? []).filter(
      (field) => field !== "thixotropic",
    );
  }
  if (generated.stress) {
    existing.stress = { ...(existing.stress ?? {}) };
    Object.entries(generated.stress).forEach(([load, value]) => {
      if (generated.profileDerivedStress?.includes(load)) return;
      existing.stress[load] = value;
      existing.profileDerivedStress = (existing.profileDerivedStress ?? []).filter(
        (field) => field !== load,
      );
    });
  }
  if (generated.environment) {
    existing.environment = { ...(existing.environment ?? {}) };
    Object.entries(generated.environment).forEach(([environment, value]) => {
      if (generated.profileDerivedEnvironment?.includes(environment)) return;
      existing.environment[environment] = value;
      existing.profileDerivedEnvironment = (existing.profileDerivedEnvironment ?? []).filter(
        (field) => field !== environment,
      );
    });
  }
  if (generated.substrates) {
    existing.substrates = { ...(existing.substrates ?? {}) };
    Object.entries(generated.substrates).forEach(([material, score]) => {
      if (generated.profileDerivedSubstrates?.includes(material)) return;
      existing.substrates[material] = score;
      existing.profileDerivedSubstrates = (existing.profileDerivedSubstrates ?? []).filter(
        (field) => field !== material,
      );
    });
  }
  if (generated.pricing && (!existing.pricing || existing.pricing.basis !== "observed")) {
    existing.pricing = generated.pricing;
  }
  if (generated.applicationTags?.length) {
    existing.applicationTags = dedupeList([
      ...(existing.applicationTags ?? []),
      ...generated.applicationTags,
    ]);
  }
  if (
    !generated.profileDerivedCompatibleMaterialPairs &&
    generated.compatibleMaterialPairs
  ) {
    existing.compatibleMaterialPairs = generated.compatibleMaterialPairs.map((pair) => [...pair]);
    existing.profileDerivedCompatibleMaterialPairs = false;
  }
  if (
    !generated.profileDerivedIncompatibleMaterialPairs &&
    generated.incompatibleMaterialPairs
  ) {
    existing.incompatibleMaterialPairs = generated.incompatibleMaterialPairs.map((pair) => [...pair]);
    existing.profileDerivedIncompatibleMaterialPairs = false;
  }
  if (generated.mcmaster) {
    existing.mcmaster = {
      ...(existing.mcmaster ?? {}),
      ...generated.mcmaster,
    };
  }
  if (
    generated.referenceUrl &&
    (!existing.referenceUrl ||
      existing.referenceUrl.includes("google.com/search?q=") ||
      generated.sourceLabel?.startsWith("McMaster"))
  ) {
    existing.referenceUrl = generated.referenceUrl;
  }
  if (generated.specUrl) {
    existing.specUrl = generated.specUrl;
  }
  if (generated.tdsUrl) {
    existing.tdsUrl = generated.tdsUrl;
  }
  if (generated.productUrl) {
    existing.productUrl = generated.productUrl;
  }
  if (generated.sdsUrl) {
    existing.sdsUrl = generated.sdsUrl;
  }
  if (generated.catalogUrl) {
    existing.catalogUrl = generated.catalogUrl;
  }
  if (generated.sourceLabel) {
    existing.sourceLabel = generated.sourceLabel;
  }
  if (generated.cautions?.length) {
    existing.cautions = Array.from(new Set([...existing.cautions, ...generated.cautions]));
  }
};

const catalogKeys = new Map(GLUES.map((glue) => [buildCatalogKey(glue), glue]));

function ingestSelectorProducts(products) {
  products.forEach(({ id, profile, ...overrides }) => {
    const generated = makeProduct(id, profile, overrides);
    const key = buildCatalogKey(generated);
    const existing = catalogKeys.get(key);

    if (existing) {
      mergeObservedCatalogData(existing, generated);
      existing.pricing = existing.pricing ?? assignPricing(existing);
      return;
    }

    generated.pricing = generated.pricing ?? assignPricing(generated);
    catalogKeys.set(key, generated);
    GLUES.push(generated);
  });
}

const referenceFamilyKeys = new Set(REFERENCE_LIBRARY.map((family) => buildReferenceFamilyKey(family)));
TDS_MANUAL_REFERENCE_FAMILIES.forEach((family) => {
  const key = buildReferenceFamilyKey(family);
  if (referenceFamilyKeys.has(key)) return;
  referenceFamilyKeys.add(key);
  REFERENCE_LIBRARY.push(family);
});

const flOzToMl = (value) => value * 29.5735;
const ydToMeters = (value) => value * 0.9144;
const roundMoney = (value) => Math.round(value * 100) / 100;

const observedUnitPrice = (priceUsd, size, unit, example, sourceUrl) => ({
  basis: "observed",
  unit,
  unitPrice: roundMoney(priceUsd / size),
  example,
  sourceUrl,
});

const estimatedUnitPrice = (unitPrice, unit, example) => ({
  basis: "estimated",
  unit,
  unitPrice: roundMoney(unitPrice),
  example,
});

const PRICE_DEFAULTS = {
  toughenedEpoxy: estimatedUnitPrice(0.95, "mL"),
  flexibleEpoxy: estimatedUnitPrice(0.8, "mL"),
  clearEpoxy: estimatedUnitPrice(0.45, "mL"),
  structuralAcrylic: estimatedUnitPrice(0.88, "mL"),
  mmaPlasticWelder: estimatedUnitPrice(0.52, "mL"),
  thinCA: estimatedUnitPrice(1.45, "mL"),
  gelCA: estimatedUnitPrice(1.65, "mL"),
  hybridCA: estimatedUnitPrice(1.15, "mL"),
  uvOptical: estimatedUnitPrice(2.2, "mL"),
  uvAcrylate: estimatedUnitPrice(2.25, "mL"),
  rtvSilicone: estimatedUnitPrice(0.1, "mL"),
  siliconeRubberAdhesive: estimatedUnitPrice(0.62, "mL"),
  polyurethaneSealant: estimatedUnitPrice(0.1, "mL"),
  msPolymerSealant: estimatedUnitPrice(0.12, "mL"),
  structuralPolyurethane: estimatedUnitPrice(0.72, "mL"),
  anaerobicThreadlocker: estimatedUnitPrice(2.2, "mL"),
  anaerobicRetainer: estimatedUnitPrice(0.82, "mL"),
  foamTape: estimatedUnitPrice(6.3, "m"),
  contactCement: estimatedUnitPrice(0.03, "mL"),
  pvaWood: estimatedUnitPrice(0.017, "mL"),
  hotMelt: estimatedUnitPrice(0.45, "stick"),
  sprayAdhesive: estimatedUnitPrice(15.5, "can"),
  thermalEpoxy: estimatedUnitPrice(1.2, "mL"),
  solventAcrylic: estimatedUnitPrice(0.08, "mL"),
  solventPVC: estimatedUnitPrice(0.035, "mL"),
  solventCPVC: estimatedUnitPrice(0.04, "mL"),
  solventABSStyrene: estimatedUnitPrice(0.045, "mL"),
  solventPolycarbonate: estimatedUnitPrice(0.08, "mL"),
  solventMultiPlastic: estimatedUnitPrice(0.06, "mL"),
  constructionAdhesive: estimatedUnitPrice(0.026, "mL"),
  industrialClear: estimatedUnitPrice(0.2, "mL"),
  fabricAdhesive: estimatedUnitPrice(0.16, "mL"),
  craftPva: estimatedUnitPrice(0.012, "mL"),
};

const PRICE_OVERRIDES = {
  "3m-dp420ns": observedUnitPrice(
    56.58,
    50,
    "mL",
    "50 mL Duo-Pak ~$56.58",
    "https://www.ellsworth.com/products/by-manufacturer/3m/adhesives/epoxy/3m-scotch-weld-dp420ns-epoxy-adhesive-black-50-ml-duo-pak-cartridge/",
  ),
  "loctite-ea9460": observedUnitPrice(
    41.78,
    50,
    "mL",
    "50 mL cartridge ~$41.78",
    "https://www.arbell.com/products/608976",
  ),
  "west-gflex-650": observedUnitPrice(
    38.72,
    flOzToMl(8),
    "mL",
    "8 oz kit ~$38.72",
    "https://www.boatoutfitters.com/west-system-g-flex-650-toughened-epoxy",
  ),
  "loctite-401": observedUnitPrice(32.73, flOzToMl(0.7), "mL", "0.7 oz bottle ~$32.73"),
  "loctite-406": observedUnitPrice(33.02, flOzToMl(0.7), "mL", "0.7 oz bottle ~$33.02"),
  "loctite-414": observedUnitPrice(34.41, flOzToMl(1), "mL", "1 oz bottle ~$34.41"),
  "loctite-454": observedUnitPrice(35.38, flOzToMl(0.7), "mL", "0.7 oz tube ~$35.38"),
  "loctite-480": observedUnitPrice(35.56, flOzToMl(0.7), "mL", "0.7 oz bottle ~$35.56"),
  "loctite-380-black-max": observedUnitPrice(
    40.13,
    flOzToMl(1),
    "mL",
    "1 oz bottle ~$40.13",
  ),
  "loctite-496": observedUnitPrice(34.25, flOzToMl(1), "mL", "1 oz bottle ~$34.25"),
  "3m-pr100": observedUnitPrice(21.01, flOzToMl(0.7), "mL", "0.7 oz bottle ~$21.01"),
  "3m-ca40": observedUnitPrice(46.6, flOzToMl(1), "mL", "1 oz bottle ~$46.60"),
  "3m-ca100": observedUnitPrice(55.61, flOzToMl(1), "mL", "1 oz bottle ~$55.61"),
  "gorilla-super-glue-gel": observedUnitPrice(
    6.16,
    15,
    "mL",
    "15 g bottle ~$6.16",
    "https://www.walmart.com/ip/15g-Gorilla-Super-Glue-Gel-ALT-UPC/104145847",
  ),
  "gorilla-micro-precise": observedUnitPrice(
    5.98,
    10,
    "mL",
    "10 g bottle ~$5.98",
    "https://www.walmart.com/ip/15g-Gorilla-Super-Glue-Gel-ALT-UPC/104145847",
  ),
  "loctite-pl-premium": observedUnitPrice(
    7.48,
    flOzToMl(10),
    "mL",
    "10 oz cartridge ~$7.48",
    "https://www.homedepot.com/p/Loctite-PL-Premium-10-oz-Polyurethane-Construction-Adhesive-Tan-Cartridge-each-1390595/202020473",
  ),
  "titebond-iii": observedUnitPrice(
    7.97,
    flOzToMl(16),
    "mL",
    "16 oz bottle ~$7.97",
    "https://business.walmart.com/ip/16-oz-Franklin-International-1414-Titebond-III-Ultimate-Wood-Glue/21129755",
  ),
  "3m-90": observedUnitPrice(
    16.88,
    flOzToMl(14.6),
    "mL",
    "14.6 oz aerosol ~$16.88",
    "https://business.walmart.com/ip/3M-Hi-Strength-90-Contact-Adhesive-Low-VOC-14-6-oz/587998698",
  ),
  "permatex-ultra-red": observedUnitPrice(
    8.97,
    flOzToMl(3.35),
    "mL",
    "3.35 oz tube ~$8.97",
    "https://pitstopusa.com/products/permatex-ultra-red-sensor-safe-silicone-3-35-oz-tube",
  ),
  "sikaflex-221": observedUnitPrice(
    26.92,
    300,
    "mL",
    "300 mL cartridge ~$26.92",
    "https://www.walmart.com/c/kp/sikaflex-221",
  ),
  "3m-5200": observedUnitPrice(
    31.99,
    flOzToMl(10),
    "mL",
    "10 oz cartridge ~$31.99",
    "https://www.bow.com/product/3m-marine-5200-adhesive-sealant-06504-black-10-oz-cartridge/",
  ),
  "loctite-243": observedUnitPrice(
    25.93,
    10,
    "mL",
    "10 mL bottle ~$25.93",
    "https://www.aftfasteners.com/loctite-243-threadlockers-medium-strength-10-ml-3-4-in-thread-blue-1-ea/",
  ),
  "loctite-638": observedUnitPrice(
    27.99,
    50,
    "mL",
    "50 mL bottle ~$27.99",
    "https://www.metricmarine.com/products/loctite-638-retaining-compound-high-strength-50-ml-1",
  ),
  "3m-vhb-5952": observedUnitPrice(
    28.79,
    ydToMeters(5),
    "m",
    '1/8" x 5 yd roll ~$28.79',
    "https://www.walmart.com/c/kp/5952-vhb-tape",
  ),
  "oatey-pvc-cement": observedUnitPrice(
    8.29,
    flOzToMl(8),
    "mL",
    "8 oz can ~$8.29",
    "https://www.webstaurantstore.com/oatey-30863-8-oz-pvc-heavy-duty-clear-cement/83530863.html",
  ),
};

function assignPricing(product) {
  return (
    PRICE_OVERRIDES[product.id] ??
    PRICE_DEFAULTS[product.profileKey] ?? {
      basis: "estimated",
      unit: "mL",
      unitPrice: null,
    }
  );
}

GLUES.forEach((glue) => {
  glue.pricing = glue.pricing ?? assignPricing(glue);
});

const PRESETS = {
  outdoorMixed: {
    substrateA: "aluminum",
    substrateB: "polycarbonate",
    coldest: -20,
    hottest: 100,
    stress: "impact",
    viscosity: ["high", "very-high"],
    environment: ["humidity"],
    thixotropicOnly: true,
    excludeWarnings: false,
    excludeHazardousSolvents: false,
    excludePipeCodeWarnings: false,
    application: "any",
    cure: "any",
    manufacturer: "any",
    minPotLife: 0,
    maxFixtureTime: 300,
    minGapFill: 1,
    minThermalConductivity: 0,
    clarity: "any",
    minLapShear: 0,
  },
  opticalClear: {
    substrateA: "glass",
    substrateB: "acrylic",
    coldest: -10,
    hottest: 70,
    stress: "peel",
    viscosity: ["wicking", "low", "medium"],
    environment: [],
    thixotropicOnly: false,
    excludeWarnings: false,
    excludeHazardousSolvents: false,
    excludePipeCodeWarnings: false,
    application: "optical-bonding",
    cure: "any",
    manufacturer: "any",
    minPotLife: 0,
    maxFixtureTime: 120,
    minGapFill: 0,
    minThermalConductivity: 0,
    clarity: "transparent",
    minLapShear: 0,
  },
  threadlocker: {
    substrateA: "steel",
    substrateB: "steel",
    coldest: -40,
    hottest: 150,
    stress: "shear",
    viscosity: ["wicking", "low"],
    environment: ["fuel"],
    thixotropicOnly: false,
    excludeWarnings: false,
    excludeHazardousSolvents: false,
    excludePipeCodeWarnings: false,
    application: "threadlocking",
    cure: "Anaerobic",
    manufacturer: "Loctite",
    minPotLife: 0,
    maxFixtureTime: 30,
    minGapFill: 0,
    minThermalConductivity: 0,
    clarity: "any",
    minLapShear: 10,
  },
  thermal: {
    substrateA: "aluminum",
    substrateB: "fr4",
    coldest: -40,
    hottest: 120,
    stress: "shear",
    viscosity: ["low", "medium"],
    environment: [],
    thixotropicOnly: false,
    excludeWarnings: false,
    excludeHazardousSolvents: false,
    excludePipeCodeWarnings: false,
    application: "potting-thermal",
    cure: "any",
    manufacturer: "any",
    minPotLife: 0,
    maxFixtureTime: 30,
    minGapFill: 0,
    minThermalConductivity: 1,
    clarity: "any",
    minLapShear: 10,
  },
};

const filterForm = document.querySelector("#filter-form");
const substrateASelect = document.querySelector("#substrate-a");
const substrateBSelect = document.querySelector("#substrate-b");
const applicationSelect = document.querySelector("#application-select");
const cureSelect = document.querySelector("#cure-select");
const manufacturerSelect = document.querySelector("#manufacturer-select");
const resultsBody = document.querySelector("#results-body");
const resultsEmpty = document.querySelector("#results-empty");
const resultsCount = document.querySelector("#results-count");
const resultsContext = document.querySelector("#results-context");
const resultsTitle = document.querySelector("#results-title");
const resultsSearch = document.querySelector("#results-search");
const resultsSort = document.querySelector("#results-sort");
const resultsPagination = document.querySelector("#results-pagination");
const productDetailDialog = document.querySelector("#product-detail-dialog");
const productDetailTitle = document.querySelector("#product-detail-title");
const productDetailMaker = document.querySelector("#product-detail-maker");
const productDetailContent = document.querySelector("#product-detail-content");
const productDetailClose = document.querySelector("#product-detail-close");
const activeTags = document.querySelector("#active-tags");
const compareState = document.querySelector("#compare-state");
const fitAHeading = document.querySelector("#fit-a-heading");
const fitBHeading = document.querySelector("#fit-b-heading");
const heroStats = document.querySelector("#hero-stats");
const glueDensity = document.querySelector("#glue-density");
const referenceBody = document.querySelector("#reference-body");
const referenceEmpty = document.querySelector("#reference-empty");
const referenceCount = document.querySelector("#reference-count");
const referenceContext = document.querySelector("#reference-context");
const referenceSearch = document.querySelector("#reference-search");
const referenceCategorySelect = document.querySelector("#reference-category");
const referenceApplicationSelect = document.querySelector("#reference-application");
const resetFiltersButton = document.querySelector("#reset-filters");
const resetHeroButton = document.querySelector("#reset-hero");
const presetButtons = document.querySelectorAll("[data-preset]");
const stressButtons = document.querySelectorAll("#stress-mode .segment");
const SAVED_GLUES_COOKIE = "glueguySavedGlues";
const SAVED_GLUES_STORAGE_KEY = "glueguy.savedGlueIds";

const appState = {
  stress: "shear",
  savedIds: readSavedGlueIds(),
  renderFrame: 0,
  resultPage: 1,
  referencePage: 1,
};

const usdFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const formatUsd = (value) => usdFormatter.format(value);
const formatTemperature = (value) => `${value}°C`;

function readSavedGlueIds() {
  try {
    const storedIds = JSON.parse(localStorage.getItem(SAVED_GLUES_STORAGE_KEY) ?? "null");
    if (Array.isArray(storedIds)) {
      return storedIds.filter((id) => typeof id === "string");
    }
  } catch {
    // Fall through to the legacy cookie for a seamless migration.
  }

  const cookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${SAVED_GLUES_COOKIE}=`));
  if (!cookie) return [];

  try {
    const value = decodeURIComponent(cookie.slice(SAVED_GLUES_COOKIE.length + 1));
    const ids = JSON.parse(value);
    return Array.isArray(ids) ? ids.filter((id) => typeof id === "string") : [];
  } catch {
    return [];
  }
}

function writeSavedGlueIds() {
  try {
    localStorage.setItem(SAVED_GLUES_STORAGE_KEY, JSON.stringify(appState.savedIds));
  } catch {
    const value = encodeURIComponent(JSON.stringify(appState.savedIds));
    document.cookie = `${SAVED_GLUES_COOKIE}=${value}; max-age=31536000; path=/; samesite=lax`;
  }
}
const formatTemperatureRange = (min, max) => {
  if (Number.isFinite(min) && Number.isFinite(max)) {
    return `${formatTemperature(min)} to ${formatTemperature(max)}`;
  }
  if (Number.isFinite(max)) return `up to ${formatTemperature(max)}`;
  if (Number.isFinite(min)) return `from ${formatTemperature(min)}`;
  return "n/a";
};
const formatMinutes = (value) => {
  if (!Number.isFinite(value)) return "n/a";
  return value < 1 ? `${Math.round(value * 60)} sec` : `${value} min`;
};
const formatGap = (value) => {
  if (!Number.isFinite(value)) return "n/a";
  return `${value.toFixed(value < 1 ? 2 : 1)} mm`;
};
const formatThermal = (value) => {
  if (!Number.isFinite(value)) return "n/a";
  return `${value.toFixed(1)} W/m·K`;
};
const formatLapShear = (value) => (Number.isFinite(value) ? `${value} MPa` : "n/a");
const materialLabel = (value) => MATERIAL_LABELS[value] ?? value;
const applicationLabel = (value) => APPLICATION_LABELS[value] ?? value;
const formatFit = (value) => `${value.toFixed(1)}/10`;
const formatPricing = (pricing) =>
  pricing && Number.isFinite(pricing.unitPrice) && pricing.unitPrice > 0
    ? `${pricing.basis === "estimated" ? "Est. " : ""}${formatUsd(pricing.unitPrice)}/${pricing.unit}`
    : "Price unavailable";
const formatPricingDetail = (pricing) => pricing?.example ?? "";
const formatMcMasterPackage = (meta) =>
  [meta?.packageSize, meta?.packageType].filter(Boolean).join(" ") || "";
const formatMcMasterSummary = (meta) =>
  [
    meta?.partNo ? `McMaster ${meta.partNo}` : "",
    formatMcMasterPackage(meta),
    meta?.color ?? "",
  ]
    .filter(Boolean)
    .join(" • ");
const formatMcMasterChemistry = (meta) =>
  [
    meta?.cureType ?? "",
    meta?.mixRatio ? `${meta.mixRatio} mix` : "",
    meta?.consistency ?? "",
  ]
    .filter(Boolean)
    .join(" • ");
const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
const formatApplicationTags = (tags, limit = 2) =>
  dedupeList(tags ?? [])
    .slice(0, limit)
    .map((tag) => applicationLabel(tag))
    .join(" • ");

function populateSelect(select, options) {
  select.innerHTML = "";
  options.forEach((option) => {
    const element = document.createElement("option");
    element.value = option.value;
    element.textContent = option.label;
    select.append(element);
  });
}

function populateFilters() {
  populateSelect(substrateASelect, MATERIALS);
  populateSelect(substrateBSelect, MATERIALS);
  populateSelect(applicationSelect, APPLICATION_OPTIONS);

  const cureFamilies = Array.from(new Set(GLUES.map((glue) => glue.cureFamily))).sort();
  populateSelect(cureSelect, [
    { value: "any", label: "Any cure family" },
    ...cureFamilies.map((value) => ({ value, label: value })),
  ]);

  const makers = Array.from(new Set(GLUES.map((glue) => glue.maker))).sort();
  populateSelect(manufacturerSelect, [
    { value: "any", label: "Any manufacturer" },
    ...makers.map((value) => ({ value, label: value })),
  ]);
}

function repopulateCatalogFilters() {
  const values = {
    substrateA: substrateASelect.value,
    substrateB: substrateBSelect.value,
    application: applicationSelect.value,
    cure: cureSelect.value,
    manufacturer: manufacturerSelect.value,
  };
  populateFilters();
  substrateASelect.value = values.substrateA;
  substrateBSelect.value = values.substrateB;
  applicationSelect.value = values.application;
  cureSelect.value = Array.from(cureSelect.options).some((option) => option.value === values.cure)
    ? values.cure
    : "any";
  manufacturerSelect.value = Array.from(manufacturerSelect.options).some(
    (option) => option.value === values.manufacturer,
  )
    ? values.manufacturer
    : "any";
}

function populateReferenceFilters() {
  if (!referenceCategorySelect || !referenceApplicationSelect) return;
  const chemistries = Array.from(new Set(GLUES.map((product) => product.chemistry).filter(Boolean))).sort();
  const applications = Array.from(new Set(GLUES.flatMap((product) => product.applicationTags ?? []).filter(Boolean)))
    .sort((left, right) => applicationLabel(left).localeCompare(applicationLabel(right)));
  populateSelect(referenceCategorySelect, [
    { value: "any", label: "All chemistries" },
    ...chemistries.map((value) => ({ value, label: value })),
  ]);
  populateSelect(referenceApplicationSelect, [
    { value: "any", label: "All use cases" },
    ...applications.map((value) => ({ value, label: applicationLabel(value) })),
  ]);
}

function renderHeroStats() {
  const chemistries = new Set(GLUES.map((glue) => glue.chemistry)).size;
  const makers = new Set(GLUES.map((glue) => glue.maker)).size;
  const statItems = [
    { label: "Chemistries", value: chemistries },
    { label: "Makers", value: makers },
  ];

  heroStats.replaceChildren(
    ...statItems.map((item) => {
      const chip = document.createElement("div");
      chip.className = "stat-chip";
      chip.innerHTML = `<strong>${item.value}</strong><span>${item.label}</span>`;
      return chip;
    }),
  );

  glueDensity.textContent = `${GLUES.length} products`;
}

function collectFilters() {
  const formData = new FormData(filterForm);
  return {
    substrateA: formData.get("substrateA") || "any",
    substrateB: formData.get("substrateB") || "any",
    application: formData.get("application") || "any",
    coldest: readTemperatureInput(formData.get("coldest")),
    hottest: readTemperatureInput(formData.get("hottest")),
    stress: appState.stress,
    viscosity: formData.getAll("viscosity"),
    environment: formData.getAll("environment"),
    thixotropicOnly: formData.get("thixotropicOnly") === "yes",
    excludeWarnings: formData.get("excludeWarnings") === "yes",
    excludeHazardousSolvents: formData.get("excludeHazardousSolvents") === "yes",
    excludePipeCodeWarnings: formData.get("excludePipeCodeWarnings") === "yes",
    savedOnly: formData.get("savedOnly") === "yes",
    cure: formData.get("cure") || "any",
    manufacturer: formData.get("manufacturer") || "any",
    minPotLife: Number(formData.get("minPotLife") || 0),
    maxFixtureTime: Number(formData.get("maxFixtureTime") || 9999),
    minGapFill: Number(formData.get("minGapFill") || 0),
    minThermalConductivity: Number(formData.get("minThermalConductivity") || 0),
    clarity: formData.get("clarity") || "any",
    minLapShear: Number(formData.get("minLapShear") || 0),
  };
}


function readTemperatureInput(value) {
  if (typeof value !== "string" || value.trim() === "") return Number.NaN;
  const temperature = Number(value);
  return Number.isFinite(temperature) ? temperature : Number.NaN;
}

function validateTemperatureWindow(filters) {
  const errors = [];
  if (!Number.isFinite(filters.coldest)) errors.push("Enter a minimum service temperature.");
  if (!Number.isFinite(filters.hottest)) errors.push("Enter a maximum service temperature.");
  if (
    Number.isFinite(filters.coldest) &&
    Number.isFinite(filters.hottest) &&
    filters.hottest < filters.coldest
  ) {
    errors.push("Maximum service temperature must be greater than or equal to the minimum.");
  }
  return errors;
}

function showTemperatureValidation(errors) {
  const message = document.querySelector("#temperature-range-error");
  const inputs = [
    filterForm.elements.coldest,
    filterForm.elements.hottest,
  ];
  const invalid = errors.length > 0;
  message?.classList.toggle("hidden", !invalid);
  if (message) message.textContent = errors.join(" ");
  inputs.forEach((input) => input?.setAttribute("aria-invalid", String(invalid)));
}

function setStressMode(value) {
  appState.stress = value;
  stressButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.value === value);
    button.setAttribute("aria-pressed", String(button.dataset.value === value));
  });
}

function setCheckedValues(name, values) {
  filterForm.querySelectorAll(`input[name="${name}"]`).forEach((input) => {
    input.checked = values.includes(input.value);
  });
}

function setFormValues(preset) {
  substrateASelect.value = preset.substrateA;
  substrateBSelect.value = preset.substrateB;
  applicationSelect.value = preset.application ?? "any";
  filterForm.elements.coldest.value = preset.coldest;
  filterForm.elements.hottest.value = preset.hottest;
  setStressMode(preset.stress);
  setCheckedValues("viscosity", preset.viscosity);
  setCheckedValues("environment", preset.environment);
  filterForm.elements.thixotropicOnly.checked = preset.thixotropicOnly;
  filterForm.elements.excludeWarnings.checked = preset.excludeWarnings;
  filterForm.elements.excludeHazardousSolvents.checked = preset.excludeHazardousSolvents;
  filterForm.elements.excludePipeCodeWarnings.checked = preset.excludePipeCodeWarnings;
  filterForm.elements.savedOnly.checked = false;
  cureSelect.value = preset.cure;
  manufacturerSelect.value = preset.manufacturer;
  filterForm.elements.minPotLife.value = preset.minPotLife;
  filterForm.elements.maxFixtureTime.value = preset.maxFixtureTime;
  filterForm.elements.minGapFill.value = preset.minGapFill;
  filterForm.elements.minThermalConductivity.value = preset.minThermalConductivity;
  filterForm.elements.clarity.value = preset.clarity;
  filterForm.elements.minLapShear.value = preset.minLapShear;
}

function resetAllFilters() {
  filterForm.reset();
  substrateASelect.value = "any";
  substrateBSelect.value = "any";
  applicationSelect.value = "any";
  cureSelect.value = "any";
  manufacturerSelect.value = "any";
  filterForm.elements.coldest.value = -20;
  filterForm.elements.hottest.value = 90;
  filterForm.elements.maxFixtureTime.value = 9999;
  filterForm.elements.minPotLife.value = 0;
  filterForm.elements.minGapFill.value = 0;
  filterForm.elements.minThermalConductivity.value = 0;
  filterForm.elements.minLapShear.value = 0;
  filterForm.elements.clarity.value = "any";
  filterForm.elements.excludeHazardousSolvents.checked = false;
  filterForm.elements.excludePipeCodeWarnings.checked = false;
  filterForm.elements.savedOnly.checked = false;
  setStressMode("shear");
}


function scoreProduct(product, filters) {
  if (filters.manufacturer !== "any" && product.maker !== filters.manufacturer) return null;
  if (filters.cure !== "any" && product.cureFamily !== filters.cure) return null;
  if (filters.application !== "any" && !(product.applicationTags ?? []).includes(filters.application)) return null;

  const profileFields = new Set(product.profileDerivedFields ?? []);
  const profileStress = new Set(product.profileDerivedStress ?? []);
  const profileEnvironment = new Set(product.profileDerivedEnvironment ?? []);
  const profileSubstrates = new Set(product.profileDerivedSubstrates ?? []);
  const unverifiedRequirements = new Set();
  const isRecorded = (field) =>
    !profileFields.has(field) &&
    product[field] !== null &&
    product[field] !== undefined &&
    (typeof product[field] !== "number" || Number.isFinite(product[field]));

  const requireRecordedThreshold = (field, label, threshold, comparison, active) => {
    if (!active) return true;
    if (!isRecorded(field) || !Number.isFinite(product[field])) {
      unverifiedRequirements.add(label);
      return true;
    }
    return comparison === "min" ? product[field] >= threshold : product[field] <= threshold;
  };
  if (!requireRecordedThreshold("potLife", "minimum pot life", filters.minPotLife, "min", filters.minPotLife > 0)) return null;
  if (!requireRecordedThreshold("fixtureTime", "maximum fixture time", filters.maxFixtureTime, "max", filters.maxFixtureTime < 9999)) return null;
  if (!requireRecordedThreshold("gapFill", "minimum gap fill", filters.minGapFill, "min", filters.minGapFill > 0)) return null;
  if (!requireRecordedThreshold("thermalConductivity", "minimum thermal conductivity", filters.minThermalConductivity, "min", filters.minThermalConductivity > 0)) return null;
  if (!requireRecordedThreshold("lapShear", "minimum lap shear", filters.minLapShear, "min", filters.minLapShear > 0)) return null;

  if (filters.clarity !== "any") {
    if (profileFields.has("clarity") || !Object.prototype.hasOwnProperty.call(CLARITY_RANK, product.clarity)) {
      unverifiedRequirements.add(filters.clarity.replace("-", " ") + " clarity");
    } else if (CLARITY_RANK[product.clarity] < CLARITY_RANK[filters.clarity]) return null;
  }
  if (filters.viscosity.length) {
    if (profileFields.has("viscosityClass") || !product.viscosityClass) {
      unverifiedRequirements.add("requested viscosity");
    } else if (!filters.viscosity.includes(product.viscosityClass)) return null;
  }
  if (filters.thixotropicOnly) {
    if (profileFields.has("thixotropic") || typeof product.thixotropic !== "boolean") {
      unverifiedRequirements.add("non-sag behavior");
    } else if (!product.thixotropic) return null;
  }
  if (
    filters.excludeHazardousSolvents &&
    (product.rawSolventMethod || product.chlorinatedSolvent || product.containsMethyleneChloride || product.containsChloroform)
  ) return null;
  if (filters.excludePipeCodeWarnings && product.pipeCodeWarning) return null;

  const selectedMaterials = [filters.substrateA, filters.substrateB].filter(
    (material) => material && material !== "any",
  );
  selectedMaterials.forEach((material) => {
    if (profileSubstrates.has(material) || !Number.isFinite(product.substrates?.[material])) {
      unverifiedRequirements.add(materialLabel(material) + " material affinity");
    }
  });
  const substrateScores = selectedMaterials.map((material) => product.substrates?.[material] ?? 0);
  const rankingSubstrateScores = selectedMaterials.map((material, index) =>
    profileSubstrates.has(material) || !Number.isFinite(product.substrates?.[material])
      ? 6.5
      : substrateScores[index],
  );
  const explicitWeakSubstrate = selectedMaterials.some(
    (material) =>
      !profileSubstrates.has(material) &&
      Number.isFinite(product.substrates?.[material]) &&
      product.substrates[material] < 3,
  );
  if (selectedMaterials.length && explicitWeakSubstrate) return null;
  if (
    selectedMaterials.length === 2 &&
    !product.profileDerivedIncompatibleMaterialPairs &&
    product.incompatibleMaterialPairs?.length &&
    materialPairListHas(product.incompatibleMaterialPairs, selectedMaterials)
  ) return null;
  if (
    selectedMaterials.length === 2 &&
    !product.profileDerivedCompatibleMaterialPairs &&
    product.compatibleMaterialPairs?.length &&
    !materialPairListHas(product.compatibleMaterialPairs, selectedMaterials)
  ) return null;
  if (
    selectedMaterials.length === 2 &&
    (product.profileDerivedCompatibleMaterialPairs ||
      product.profileDerivedIncompatibleMaterialPairs ||
      !product.compatibleMaterialPairs?.length)
  ) {
    unverifiedRequirements.add(
      materialLabel(selectedMaterials[0]) + " to " + materialLabel(selectedMaterials[1]) + " joint compatibility",
    );
  }

  const averageSubstrate = selectedMaterials.length
    ? rankingSubstrateScores.reduce((sum, value) => sum + value, 0) / selectedMaterials.length
    : 6.5;
  const minimumSubstrate = selectedMaterials.length ? Math.min(...rankingSubstrateScores) : 6.5;
  const temperatureIsProfileDerived =
    profileFields.has("serviceMin") || profileFields.has("serviceMax") ||
    !Number.isFinite(product.serviceMin) || !Number.isFinite(product.serviceMax);
  if (temperatureIsProfileDerived) unverifiedRequirements.add("service temperature range");
  const lowTempMiss = temperatureIsProfileDerived ? 0 : Math.max(0, product.serviceMin - filters.coldest);
  const highTempMiss = temperatureIsProfileDerived ? 0 : Math.max(0, filters.hottest - product.serviceMax);
  const temperaturePenalty = lowTempMiss * 0.7 + highTempMiss * 0.45;
  const temperatureFit = temperatureIsProfileDerived ? 0 : clamp(12 - temperaturePenalty, -16, 12);

  filters.environment.forEach((name) => {
    if (profileEnvironment.has(name) || !Number.isFinite(product.environment?.[name])) {
      unverifiedRequirements.add(ENVIRONMENT_LABELS[name] + " resistance");
    }
  });
  const environmentValues = filters.environment.map((name) =>
    profileEnvironment.has(name) || !Number.isFinite(product.environment?.[name])
      ? 0.5
      : product.environment[name],
  );
  const environmentAverage = environmentValues.length
    ? environmentValues.reduce((sum, value) => sum + value, 0) / environmentValues.length
    : 0.72;
  if (profileStress.has(filters.stress) || !Number.isFinite(product.stress?.[filters.stress])) {
    unverifiedRequirements.add("primary " + STRESS_LABELS[filters.stress] + " performance");
  }
  const stressFit =
    profileStress.has(filters.stress) || !Number.isFinite(product.stress?.[filters.stress])
      ? 0.5
      : product.stress[filters.stress];
  const gapFillIsRecorded = isRecorded("gapFill");
  const nonSagIsRecorded = isRecorded("thixotropic");

  const rawScore =
    averageSubstrate * 5 +
    minimumSubstrate * 2.2 +
    stressFit * 4.1 +
    environmentAverage * 12 +
    temperatureFit +
    (nonSagIsRecorded && product.thixotropic ? 2 : 0) +
    (gapFillIsRecorded && Number.isFinite(product.gapFill) ? Math.min(product.gapFill, 5) : 0);

  const reasons = [];
  const warnings = [];
  if (
    selectedMaterials.length === 2 &&
    selectedMaterials.every((material) => !profileSubstrates.has(material) && Number.isFinite(product.substrates?.[material])) &&
    minimumSubstrate >= 8
  ) {
    reasons.push("Strong on " + materialLabel(selectedMaterials[0]) + " and " + materialLabel(selectedMaterials[1]) + ".");
  } else if (
    selectedMaterials.length === 1 &&
    !profileSubstrates.has(selectedMaterials[0]) &&
    Number.isFinite(product.substrates?.[selectedMaterials[0]]) &&
    averageSubstrate >= 8
  ) {
    reasons.push("High affinity for " + materialLabel(selectedMaterials[0]) + ".");
  }
  if (
    selectedMaterials.length === 2 &&
    !product.profileDerivedCompatibleMaterialPairs &&
    product.compatibleMaterialPairs?.length &&
    materialPairListHas(product.compatibleMaterialPairs, selectedMaterials)
  ) {
    reasons.push("Listed for " + materialLabel(selectedMaterials[0]) + " to " + materialLabel(selectedMaterials[1]) + ".");
  }

  if (!temperatureIsProfileDerived && temperaturePenalty === 0) {
    reasons.push("Product record lists " + formatTemperature(filters.coldest) + " to " + formatTemperature(filters.hottest) + " service coverage.");
  } else if (!temperatureIsProfileDerived) {
    warnings.push("Product-record temperature range does not cover the full requested window.");
  }
  if (
    !temperatureIsProfileDerived &&
    filters.hottest <= product.serviceMax &&
    product.serviceMax - filters.hottest < 10
  ) {
    warnings.push(
      "Service temp only " + formatTemperature(product.serviceMax) +
      " (design at " + formatTemperature(filters.hottest) + " leaves <10 °C margin).",
    );
  }

  const environmentIsFullyRecorded = filters.environment.every(
    (name) => !profileEnvironment.has(name) && Number.isFinite(product.environment?.[name]),
  );
  if (filters.environment.length && environmentIsFullyRecorded && environmentAverage >= 0.76) {
    reasons.push("Comfortable in " + filters.environment.map((key) => ENVIRONMENT_LABELS[key]).join(", ") + ".");
  }
  if (filters.environment.some(
    (name) => !profileEnvironment.has(name) && Number.isFinite(product.environment?.[name]) && product.environment[name] < 0.6,
  )) warnings.push("Selected environment is tougher than this glue prefers.");
  if (product.rawSolventMethod || product.chlorinatedSolvent) {
    warnings.push("Raw or chlorinated solvent method; use industrial controls and SDS procedures.");
  } else if (product.flammable || product.containsMek) {
    warnings.push("Flammable solvent cement; ventilation, PPE, and ignition control matter.");
  }
  if (product.pipeCodeWarning) {
    warnings.push("Pipe-code-limited product; verify local approval before using it for plumbing transitions.");
  }

  if (filters.thixotropicOnly && nonSagIsRecorded && product.thixotropic) {
    reasons.push("Recorded non-sag behavior suits vertical joints.");
  } else if (
    nonSagIsRecorded && gapFillIsRecorded && product.thixotropic &&
    Number.isFinite(product.gapFill) && product.gapFill >= 3
  ) {
    reasons.push("Bridges around " + formatGap(product.gapFill) + " without slumping.");
  }
  if (
    filters.clarity !== "any" &&
    isRecorded("clarity") &&
    CLARITY_RANK[product.clarity] >= CLARITY_RANK[filters.clarity]
  ) reasons.push("Bond line stays " + product.clarity.replace("-", " ") + ".");
  if (
    isRecorded("thermalConductivity") &&
    Number.isFinite(product.thermalConductivity) &&
    product.thermalConductivity >= Math.max(1, filters.minThermalConductivity)
  ) reasons.push("Moves heat at " + formatThermal(product.thermalConductivity) + ".");
  if (isRecorded("fixtureTime") && product.fixtureTime <= 5) {
    reasons.push("Fast fixture in " + formatMinutes(product.fixtureTime) + ".");
  } else if (
    filters.minPotLife > 0 && isRecorded("potLife") &&
    product.potLife >= filters.minPotLife
  ) {
    reasons.push("Working time meets minimum at " + formatMinutes(product.potLife) + ".");
  }
  if (selectedMaterials.length && minimumSubstrate < 5) {
    warnings.push("Recorded substrate fit is marginal for at least one side of the joint.");
  }

  warnings.push(...product.cautions);
  const dedupedWarnings = Array.from(new Set(warnings));
  const dedupedUnverifiedRequirements = Array.from(unverifiedRequirements);
  if (filters.excludeWarnings && (dedupedWarnings.length || dedupedUnverifiedRequirements.length)) return null;

  return {
    product,
    score: clamp(Math.round(rawScore), 0, 100),
    substrateFit: averageSubstrate,
    minimumSubstrate,
    materialFits: Object.fromEntries(selectedMaterials.map((material) => [material, product.substrates?.[material] ?? 0])),
    materialFitIsProfileDerived: selectedMaterials.filter((material) => profileSubstrates.has(material)),
    unverifiedRequirements: dedupedUnverifiedRequirements,
    reasons: reasons.slice(0, 2),
    warnings: dedupedWarnings.slice(0, 2),
  };
}

function scoreColor(score) {
  if (score >= 80) return { bg: "rgba(30, 157, 115, 0.16)", text: "#106348" };
  if (score >= 60) return { bg: "rgba(210, 124, 29, 0.16)", text: "#8f520d" };
  return { bg: "rgba(201, 63, 47, 0.14)", text: "#9c3024" };
}

function buildActiveTags(filters) {
  const tags = [];
  if (filters.substrateA !== "any") tags.push(`This: ${materialLabel(filters.substrateA)}`);
  if (filters.substrateB !== "any") tags.push(`That: ${materialLabel(filters.substrateB)}`);
  if (filters.application !== "any") tags.push(applicationLabel(filters.application));
  if (filters.environment.length) {
    filters.environment.forEach((name) => tags.push(ENVIRONMENT_LABELS[name]));
  }
  if (filters.cure !== "any") tags.push(filters.cure);
  if (filters.clarity !== "any") tags.push(filters.clarity.replace("-", " "));
  if (filters.excludeHazardousSolvents) tags.push("no raw/chlorinated solvents");
  if (filters.excludePipeCodeWarnings) tags.push("no code-limited pipe cements");
  if (filters.savedOnly) tags.push("inventory only");
  if (filters.minThermalConductivity > 0) {
    tags.push(`>= ${formatThermal(filters.minThermalConductivity)}`);
  }
  return tags;
}

function buildReferenceContext() {
  const parts = [];
  if (MCMASTER_PIPELINE_STATS.offers) {
    parts.push(`${MCMASTER_PIPELINE_STATS.offers} observed offers`);
  }
  if (MCMASTER_PIPELINE_STATS.pagesCrawled) {
    parts.push(`${MCMASTER_PIPELINE_STATS.pagesCrawled} McMaster pages crawled`);
  }
  if (MCMASTER_PIPELINE_STATS.leafPages) {
    parts.push(`${MCMASTER_PIPELINE_STATS.leafPages} leaf pages`);
  }
  if (MCMASTER_PIPELINE_STATS.detailPages) {
    parts.push(`${MCMASTER_PIPELINE_STATS.detailPages} part pages enriched`);
  }
  return parts.join(" • ") || "McMaster-derived browse table";
}

function formatReferenceCost(family) {
  if (Number.isFinite(family.bestPricePerMl)) {
    return `${formatUsd(family.bestPricePerMl)}/mL`;
  }
  if (family.pricing && Number.isFinite(family.pricing.unitPrice) && family.pricing.unit) {
    return `${formatUsd(family.pricing.unitPrice)}/${family.pricing.unit}`;
  }
  if (Number.isFinite(family.lowestPriceUsd)) {
    return `${formatUsd(family.lowestPriceUsd)}/pkg`;
  }
  return "n/a";
}

function renderReferenceLibrary() {
  if (!referenceBody || !referenceCount || !referenceContext) return;
  const query = referenceSearch?.value.trim().toLowerCase() ?? "";
  const chemistry = referenceCategorySelect?.value ?? "any";
  const application = referenceApplicationSelect?.value ?? "any";
  const visibleProducts = GLUES.filter((product) => {
    if (chemistry !== "any" && product.chemistry !== chemistry) return false;
    if (application !== "any" && !(product.applicationTags ?? []).includes(application)) return false;
    if (!query) return true;
    const haystack = [
      product.name, product.maker, product.chemistry, product.cureFamily, product.cureDetail,
      product.productSku, product.productCode, product.partNumber, product.id,
      product.mcmaster?.partNo, ...(product.applicationTags ?? []),
    ].filter(Boolean).join(" ").toLowerCase();
    return haystack.includes(query);
  });
  referenceCount.textContent = `${visibleProducts.length} product${visibleProducts.length === 1 ? "" : "s"}`;
  referenceBody.replaceChildren();
  referenceEmpty?.classList.toggle("hidden", visibleProducts.length > 0);
  const pageCount = Math.max(1, Math.ceil(visibleProducts.length / REFERENCE_PAGE_SIZE));
  appState.referencePage = Math.min(appState.referencePage, pageCount);
  const pageStart = (appState.referencePage - 1) * REFERENCE_PAGE_SIZE;
  const pageProducts = visibleProducts.slice(pageStart, pageStart + REFERENCE_PAGE_SIZE);
  referenceContext.textContent = visibleProducts.length
    ? `Showing ${pageStart + 1}–${Math.min(pageStart + REFERENCE_PAGE_SIZE, visibleProducts.length)} of ${visibleProducts.length} • ${GLUES.length} catalog products`
    : `${GLUES.length} catalog products • Search product, maker, part number, chemistry, or use case`;
  if (!visibleProducts.length) {
    renderReferencePagination(0, 1);
    return;
  }

  const makeText = (tagName, className, value) => {
    const node = document.createElement(tagName);
    if (className) node.className = className;
    node.textContent = value ?? "";
    return node;
  };
  const fragment = document.createDocumentFragment();
  pageProducts.forEach((product) => {
    const row = document.createElement("tr");
    const productCell = document.createElement("td");
    productCell.append(makeText("p", "maker", product.maker || "Unknown maker"));
    const detail = document.createElement("button");
    detail.type = "button";
    detail.className = "product-name product-detail-trigger";
    detail.textContent = product.name || "Unnamed product";
    detail.setAttribute("aria-haspopup", "dialog");
    detail.setAttribute("aria-controls", "product-detail-dialog");
    detail.addEventListener("click", () => openProductDetail(product));
    productCell.append(detail);
    const part = product.productSku || product.productCode || product.partNumber || product.mcmaster?.partNo;
    if (part) productCell.append(makeText("p", "table-note", `Part ${part}`));

    const applicationsCell = document.createElement("td");
    const applications = document.createElement("div");
    applications.className = "application-list";
    const tags = dedupeList(product.applicationTags ?? []);
    if (tags.length) tags.forEach((tag) => applications.append(makeText("span", "application-pill", applicationLabel(tag))));
    else applications.append(makeText("span", "empty-text", "Not reported"));
    applicationsCell.append(applications);

    const chemistryCell = document.createElement("td");
    chemistryCell.append(makeText("div", "", product.chemistry || "Not reported"));
    if (product.cureFamily) chemistryCell.append(makeText("div", "table-note", product.cureFamily));
    if (product.mcmaster) chemistryCell.append(makeText("div", "table-note", formatMcMasterSummary(product.mcmaster)));

    const temperatureCell = makeText("td", "", formatTemperatureRange(product.serviceMin, product.serviceMax));
    const priceCell = document.createElement("td");
    priceCell.append(makeText("div", "cost-main", formatPricing(product.pricing)));
    const priceDetail = formatPricingDetail(product.pricing);
    if (priceDetail) priceCell.append(makeText("div", "table-note", priceDetail));

    const sourcesCell = document.createElement("td");
    const sources = productSourceLinks(product);
    if (sources.length) {
      const links = document.createElement("div");
      links.className = "reference-source-links";
      sources.forEach(({ url, label, ariaLabel }) => {
        const link = document.createElement("a");
        link.className = "reference-link";
        link.href = url;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.textContent = label;
        link.setAttribute("aria-label", `${ariaLabel} for ${product.maker} ${product.name}`);
        links.append(link);
      });
      sourcesCell.append(links);
    } else {
      sourcesCell.append(makeText("span", "empty-text", "No source links recorded"));
    }
    row.append(productCell, applicationsCell, chemistryCell, temperatureCell, priceCell, sourcesCell);
    fragment.append(row);
  });
  referenceBody.append(fragment);
  renderReferencePagination(visibleProducts.length, pageCount);
}


function renderReferencePagination(total, pageCount) {
  const pagination = document.querySelector("#reference-pagination");
  if (!pagination) return;
  pagination.replaceChildren();
  if (total <= REFERENCE_PAGE_SIZE) return;
  const makeButton = (label, page, disabled = false, current = false) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "page-button";
    button.textContent = label;
    button.dataset.referencePage = String(page);
    button.disabled = disabled;
    if (current) button.setAttribute("aria-current", "page");
    return button;
  };
  const previous = Math.max(1, appState.referencePage - 1);
  const next = Math.min(pageCount, appState.referencePage + 1);
  pagination.append(
    makeButton("Previous", previous, appState.referencePage === 1),
    makeButton("1", 1, false, appState.referencePage === 1),
  );
  if (appState.referencePage > 3) pagination.append(document.createTextNode("…"));
  const start = Math.max(2, appState.referencePage - 1);
  const end = Math.min(pageCount - 1, appState.referencePage + 1);
  for (let page = start; page <= end; page += 1) {
    if (page > 1 && page < pageCount) pagination.append(makeButton(String(page), page, false, page === appState.referencePage));
  }
  if (appState.referencePage < pageCount - 2) pagination.append(document.createTextNode("…"));
  if (pageCount > 1) pagination.append(makeButton(String(pageCount), pageCount, false, appState.referencePage === pageCount));
  pagination.append(makeButton("Next", next, appState.referencePage === pageCount));
}

function setCatalogView(showCatalog) {
  const workbench = document.querySelector("#lab");
  const catalogPanel = document.querySelector("#reference-library-panel");
  const catalogToggle = document.querySelector("#catalog-toggle");
  if (!workbench || !catalogPanel || !catalogToggle) return;
  workbench.classList.toggle("hidden", showCatalog);
  catalogPanel.classList.toggle("hidden", !showCatalog);
  catalogToggle.setAttribute("aria-expanded", String(showCatalog));
  if (showCatalog) {
    renderReferenceLibrary();
    catalogPanel.querySelector("#reference-search")?.focus();
  } else {
    catalogToggle.focus({ preventScroll: true });
  }
}

function safeSourceUrl(value) {
  if (typeof value !== "string" || !value.trim()) return null;
  try {
    const url = new URL(value, window.location.href);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch {
    return null;
  }
}

function isSearchSourceUrl(value) {
  const safeUrl = safeSourceUrl(value);
  if (!safeUrl) return false;
  try {
    const url = new URL(safeUrl);
    return /(^|\.)(google|bing|duckduckgo)\./i.test(url.hostname) &&
      (url.pathname === "/search" || url.searchParams.has("q"));
  } catch {
    return false;
  }
}

function productSourceLinks(product) {
  const links = [];
  const seen = new Set();
  const add = (value, label, ariaLabel, kind) => {
    const url = safeSourceUrl(value);
    if (!url || seen.has(url)) return;
    seen.add(url);
    links.push({ url, label, ariaLabel, kind });
  };

  add(product.tdsUrl, "TDS", "Manufacturer technical data sheet", "tds");
  add(
    product.productUrl,
    "Product",
    "Product page",
    "product",
  );
  add(
    product.specUrl,
    product.sourceLabel?.startsWith("McMaster") ? "Distributor" : "Spec",
    product.sourceLabel?.startsWith("McMaster") ? "Distributor product specification" : "Product specification",
    "spec",
  );
  add(product.sdsUrl, "SDS", "Safety data sheet", "sds");
  add(product.pricing?.sourceUrl, "Price", "Price source listing", "price");
  add(
    product.catalogUrl,
    product.sourceLabel?.startsWith("McMaster") ? "Distributor" : "Catalog",
    product.sourceLabel?.startsWith("McMaster") ? "Distributor catalog listing" : "Catalog listing",
    "catalog",
  );

  const referenceUrl = safeSourceUrl(product.referenceUrl);
  const referenceText = referenceUrl
    ? (() => {
        const parsed = new URL(referenceUrl);
        return `${parsed.hostname}${parsed.pathname}`.toLowerCase();
      })()
    : "";
  const referenceIsSds =
    referenceText.includes("sds") || referenceText.includes("safety-data");
  const referenceIsTds =
    referenceText.includes("/tds") ||
    referenceText.includes("-tds") ||
    referenceText.includes("_tds") ||
    referenceText.includes("datasheet") ||
    referenceText.includes("data-sheet") ||
    referenceText.includes("technical-data") ||
    referenceText.includes("tech-data");
  const referenceIsSearch = isSearchSourceUrl(product.referenceUrl);
  let hasManufacturerTds = Boolean(safeSourceUrl(product.tdsUrl));

  if (referenceUrl && !referenceIsSearch) {
    const isDistributor = product.sourceLabel?.startsWith("McMaster");
    if (referenceIsSds) {
      add(referenceUrl, "SDS", "Safety data sheet", "sds");
    } else if (referenceIsTds) {
      add(referenceUrl, "TDS", "Manufacturer technical data sheet", "tds");
      hasManufacturerTds = true;
    } else {
      const isPdf = referenceText.endsWith(".pdf");
      add(
        referenceUrl,
        isDistributor ? "Distributor" : isPdf ? "PDF" : "Reference",
        isDistributor
          ? "Distributor listing"
          : isPdf
            ? "PDF reference document"
            : "Reference page",
        isDistributor ? "distributor" : "reference",
      );
    }
  }

  if (!hasManufacturerTds) {
    const fallback = referenceIsSearch
      ? product.referenceUrl
      : `https://www.google.com/search?q=${encodeURIComponent(`${product.name} ${product.maker} TDS`)}`;
    add(fallback, "Search TDS", "Search the web for this product's technical data sheet", "search");
  }

  return links;
}

const DETAIL_EVIDENCE_FIELDS = [
  ["Mix ratio", "mixRatio"],
  ["Electrical behavior", "electricalBehavior"],
  ["Volume resistivity", "volumeResistivity"],
  ["Volume resistivity (Ω·m)", "volumeResistivityOhmM"],
  ["Surface resistivity", "surfaceResistivity"],
  ["Surface resistivity (Ω)", "surfaceResistivityOhm"],
  ["Dielectric constant", "dielectricConstant"],
  ["Dielectric breakdown", "dielectricBreakdown"],
  ["Tensile strength", "tensileStrength"],
  ["Tensile strength (MPa)", "tensileStrengthMPa"],
  ["Tensile modulus (MPa)", "tensileModulusMPa"],
  ["Elongation (%)", "elongationPct"],
  ["Hardness", "hardnessValue"],
  ["Peel strength (N/25 mm)", "peelStrengthNPer25Mm"],
  ["Cure depth", "cureDepth"],
  ["Cure rate (mm/24 h)", "cureRateMmPer24h"],
  ["Working life (days)", "workingLifeDays"],
  ["Storage condition", "storageCondition"],
  ["TDS revision date", "sourceRevisionDate"],
  ["Test methods / standards", "standards"],
  ["Lap-shear substrate and conditions", "lapShearSubstrate"],
  ["Service-temperature note", "serviceTemperatureNote"],
  ["Working-life conditions", "potLifeConditions"],
  ["Handling-time note", "fixtureTimeNote"],
  ["Viscosity note", "viscosityNote"],
  ["Test specimen", "testPiece"],
  ["Test condition", "testCondition"],
  ["Test method", "testMethod"],
  ["Test temperature", "testTemperature"],
  ["Test substrate", "testSubstrate"],
  ["Test surface preparation", "testSurfacePrep"],
  ["Test dwell time", "testDwellTime"],
  ["Test bond-line thickness", "testBondlineThickness"],
  ["Bonding conditions", "bondingConditions"],
  ["Cure conditions", "cureCondition"],
  ["Recommended cure conditions", "recommendedCureConditions"],
  ["Recommended bond line", "recommendedBondLineMm"],
  ["Product code", "productSku"],
];

function formatDetailValue(value) {
  if (value === null || value === undefined || value === "") return "";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map(formatDetailValue).filter(Boolean).join(" • ");
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, entry]) => {
        const label = key.replace(/([a-z0-9])([A-Z])/g, "$1 $2").replace(/^./, (char) => char.toUpperCase());
        const formatted = formatDetailValue(entry);
        return formatted ? `${label}: ${formatted}` : "";
      })
      .filter(Boolean)
      .join(" • ");
  }
  return "";
}

function createDetailSection(title, description = "") {
  const section = document.createElement("section");
  section.className = "product-detail-section";
  const heading = document.createElement("h3");
  heading.textContent = title;
  section.append(heading);
  if (description) {
    const note = document.createElement("p");
    note.className = "product-detail-note";
    note.textContent = description;
    section.append(note);
  }
  const facts = document.createElement("dl");
  facts.className = "product-detail-facts";
  section.append(facts);
  return section;
}

function appendDetailFact(section, label, value, profileDerived = false, sourceLabel = "") {
  if (value === null || value === undefined || value === "") return;
  const fact = document.createElement("div");
  fact.className = "product-detail-fact";
  const term = document.createElement("dt");
  term.textContent = label;
  const definition = document.createElement("dd");
  const text = document.createElement("span");
  text.textContent = value;
  definition.append(text);
  const provenance = document.createElement("span");
  provenance.className = profileDerived ? "field-evidence" : "detail-provenance";
  provenance.textContent = profileDerived ? "Profile guide" : sourceLabel || "Product record";
  provenance.title = profileDerived
    ? "This value is inherited from a chemistry profile, not this product’s technical data sheet."
    : sourceLabel
      ? "Source and conditions are summarized in this catalog field; use linked manufacturer documentation for full test details."
      : "Product-specific catalog value; verify conditions and limits in the linked manufacturer documentation.";
  provenance.setAttribute("aria-label", provenance.title);
  definition.append(provenance);
  fact.append(term, definition);
  const facts = section.querySelector(".product-detail-facts");
  (facts ?? section).append(fact);
}

function openProductDetail(product, match) {
  if (!productDetailDialog || !productDetailContent) return;
  productDetailTitle.textContent = product.name || "Product details";
  productDetailMaker.textContent = product.maker || "Manufacturer not reported";
  productDetailContent.replaceChildren();

  const overview = createDetailSection("Overview");
  const summary = document.createElement("p");
  summary.className = "product-detail-summary";
  summary.textContent = product.summary || "No product-specific summary is recorded.";
  overview.append(summary);
  const identity = document.createElement("div");
  identity.className = "product-detail-tags";
  [product.chemistry, product.cureFamily, product.cureDetail]
    .filter(Boolean)
    .forEach((value) => {
      const tag = document.createElement("span");
      tag.className = "application-pill";
      tag.textContent = value;
      identity.append(tag);
    });
  if (identity.childElementCount) overview.append(identity);
  const applications = dedupeList(product.applicationTags ?? []).map(applicationLabel);
  if (applications.length) {
    const applicationNote = document.createElement("p");
    applicationNote.className = "product-detail-note";
    applicationNote.textContent = `Applications: ${applications.join(" • ")}`;
    overview.append(applicationNote);
  }
  if (product.mcmaster) {
    const packageSummary = [formatMcMasterSummary(product.mcmaster), formatMcMasterChemistry(product.mcmaster)]
      .filter(Boolean)
      .join(" • ");
    if (packageSummary) {
      const packageNote = document.createElement("p");
      packageNote.className = "product-detail-note";
      packageNote.textContent = packageSummary;
      overview.append(packageNote);
    }
  }
  productDetailContent.append(overview);

  if (match) {
    const assessment = createDetailSection(
      "Current joint assessment",
      "This is screening guidance. Confirm suitability, surface preparation, test conditions, and service limits in the manufacturer’s documentation."
    );
    const selectedMaterials = [match.filters?.substrateA, match.filters?.substrateB].filter(
      (material) => material && material !== "any",
    );
    if (selectedMaterials.length) {
      selectedMaterials.forEach((material) => {
        const isProfileDerived = product.profileDerivedSubstrates?.includes(material);
        appendDetailFact(
          assessment,
          `${materialLabel(material)} material affinity`,
          formatFit(match.materialFits?.[material] ?? product.substrates?.[material] ?? 0),
          isProfileDerived,
        );
      });
    } else {
      const anyMaterial = document.createElement("p");
      anyMaterial.className = "product-detail-note";
      anyMaterial.textContent = "No material pair is selected.";
      assessment.append(anyMaterial);
    }
    const assessmentText = [
      ...(match.reasons ?? []),
      ...(match.unverifiedRequirements ?? []).map((requirement) => "Verify product-specific evidence for " + requirement + "."),
      ...(match.warnings ?? []),
    ];
    const uniqueAssessment = dedupeList(assessmentText);
    if (uniqueAssessment.length) {
      const list = document.createElement("ul");
      list.className = "product-detail-list";
      uniqueAssessment.forEach((text) => {
        const item = document.createElement("li");
        item.textContent = text;
        list.append(item);
      });
      assessment.append(list);
    }
    productDetailContent.append(assessment);
  }

  const specifications = createDetailSection(
    "Core specifications",
    "Values tagged “Profile guide” are chemistry-family defaults. Other values are product-specific catalog entries; the linked source and its test conditions remain authoritative."
  );
  const coreFields = [
    ["Service temperature", formatTemperatureRange(product.serviceMin, product.serviceMax), ["serviceMin", "serviceMax"]],
    ["Fixture time", formatMinutes(product.fixtureTime), ["fixtureTime"]],
    ["Pot life", formatMinutes(product.potLife), ["potLife"]],
    ["Gap fill", formatGap(product.gapFill), ["gapFill"]],
    ["Lap shear", formatLapShear(product.lapShear), ["lapShear"]],
    ["Viscosity", VISCOSITY_LABELS[product.viscosityClass] ?? "Not reported", ["viscosityClass"]],
    ["Thermal conductivity", Number.isFinite(product.thermalConductivity) ? formatThermal(product.thermalConductivity) : "Not reported", ["thermalConductivity"]],
    ["Clarity", product.clarity ? product.clarity.replaceAll("-", " ") : "Not reported", ["clarity"]],
    ["Mix ratio", product.mixRatio ? formatDetailValue(product.mixRatio) : "Not reported", []],
    ["Primary load guidance", Number.isFinite(product.stress?.[match?.filters?.stress ?? appState.stress]) ? `${product.stress[match?.filters?.stress ?? appState.stress]}/10` : "Not reported", []],
  ];
  coreFields.forEach(([label, value, fields]) => {
    const profileDerived = fields.some((field) => product.profileDerivedFields?.includes(field));
    appendDetailFact(specifications, label, value, profileDerived);
  });
  appendDetailFact(
    specifications,
    "Non-sag",
    product.thixotropic ? "Yes" : "No",
    product.profileDerivedFields?.includes("thixotropic"),
  );
  productDetailContent.append(specifications);

  const otherValues = DETAIL_EVIDENCE_FIELDS
    .map(([label, field]) => [label, field, formatDetailValue(product[field])])
    .filter(([, , value]) => value);
  if (otherValues.length) {
    const evidence = createDetailSection(
      "TDS evidence and test context",
      "Recorded source revision, methods, substrates, and conditions help interpret typical values. They are shown only when present in the product record."
    );
    otherValues.forEach(([label, field, value]) => {
      const tdsLinked = Boolean(safeSourceUrl(product.tdsUrl) || safeSourceUrl(product.referenceUrl));
      const provenanceLabel = field === "sourceRevisionDate"
        ? (tdsLinked ? "TDS source" : "Source note")
        : /Master Bond product page/i.test(value)
          ? "Related source note"
          : tdsLinked ? "TDS-linked note" : "Catalog note";
      appendDetailFact(evidence, label, value, false, provenanceLabel);
    });
    productDetailContent.append(evidence);
  }

  const commerce = createDetailSection("Price and package");
  appendDetailFact(commerce, "Unit price", formatPricing(product.pricing), false);
  if (product.pricing?.example) appendDetailFact(commerce, "Package", product.pricing.example, false);
  if (product.pricing?.basis) {
    const basis = document.createElement("p");
    basis.className = "product-detail-note";
    basis.textContent =
      product.pricing.basis === "estimated"
        ? "Price is an estimate, not a current supplier quote."
        : "Observed package price; availability and price can change.";
    commerce.append(basis);
  }
  productDetailContent.append(commerce);

  const cautions = dedupeList([...(product.cautions ?? []), ...(match?.warnings ?? [])]);
  if (cautions.length) {
    const cautionSection = createDetailSection("Cautions and limitations");
    const list = document.createElement("ul");
    list.className = "product-detail-list product-detail-cautions";
    cautions.forEach((warning) => {
      const item = document.createElement("li");
      item.textContent = warning;
      list.append(item);
    });
    cautionSection.append(list);
    productDetailContent.append(cautionSection);
  }

  const sources = createDetailSection(
    "Sources",
    "Use manufacturer documentation for final design decisions. Search results are discovery links, not evidence."
  );
  const sourceLinks = productSourceLinks(product);
  if (sourceLinks.length) {
    const linkList = document.createElement("div");
    linkList.className = "product-detail-sources";
    sourceLinks.forEach(({ url, label, ariaLabel }) => {
      const link = document.createElement("a");
      link.className = "action-secondary-link";
      link.href = url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = label;
      link.setAttribute("aria-label", ariaLabel);
      link.title = ariaLabel;
      linkList.append(link);
    });
    sources.append(linkList);
  } else {
    const noSources = document.createElement("p");
    noSources.className = "product-detail-note";
    noSources.textContent = "No source links are recorded.";
    sources.append(noSources);
  }
  productDetailContent.append(sources);

  if (typeof productDetailDialog.showModal === "function") {
    productDetailDialog.showModal();
  } else {
    productDetailDialog.setAttribute("open", "");
  }
}

function renderResults() {
  appState.renderFrame = 0;
  const filters = collectFilters();
  const inputErrors = validateTemperatureWindow(filters);
  showTemperatureValidation(inputErrors);
  if (inputErrors.length) {
    resultsTitle.textContent = "Check joint conditions";
    resultsCount.textContent = "Not ranked";
    resultsContext.textContent = "Correct the service temperature range to see candidates.";
    resultsBody.replaceChildren();
    resultsEmpty.classList.add("hidden");
    renderResultsPagination(0, 1);
    return;
  }
  const candidates = filters.savedOnly
    ? GLUES.filter((glue) => appState.savedIds.includes(glue.id))
    : GLUES;
  const query = resultsSearch?.value.trim().toLocaleLowerCase() ?? "";
  const matches = candidates
    .map((glue) => scoreProduct(glue, filters))
    .filter(Boolean)
    .filter((match) => !query || [match.product.name, match.product.maker, match.product.chemistry, match.product.cureFamily, ...(match.product.applicationTags ?? [])].filter(Boolean).join(" ").toLocaleLowerCase().includes(query))
    .sort((left, right) => {
      if (resultsSort?.value === "name") return left.product.name.localeCompare(right.product.name);
      if (resultsSort?.value === "price") {
        const a = left.product.pricing?.unitPrice, b = right.product.pricing?.unitPrice;
        if (Number.isFinite(a) && a > 0 && (!Number.isFinite(b) || b <= 0)) return -1;
        if (Number.isFinite(b) && b > 0 && (!Number.isFinite(a) || a <= 0)) return 1;
        return (a || Infinity) - (b || Infinity);
      }
      return right.score - left.score || (!right.product.profileDerivedFields?.includes("lapShear") && Number.isFinite(right.product.lapShear) ? right.product.lapShear : 0) - (!left.product.profileDerivedFields?.includes("lapShear") && Number.isFinite(left.product.lapShear) ? left.product.lapShear : 0);
    });

  const selectedMaterials = [filters.substrateA, filters.substrateB].filter(
    (material) => material && material !== "any",
  );
  if (selectedMaterials.length === 2) {
    resultsTitle.textContent = `This to That: ${materialLabel(selectedMaterials[0])} -> ${materialLabel(selectedMaterials[1])}`;
  } else if (selectedMaterials.length === 1) {
    resultsTitle.textContent = `${materialLabel(selectedMaterials[0])}`;
  } else {
    resultsTitle.textContent = "Matches";
  }
  fitAHeading.textContent = "Material fit";
  fitBHeading.textContent = "Secondary fit";

  const pageCount = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
  appState.resultPage = Math.min(appState.resultPage, pageCount);
  const pageStart = (appState.resultPage - 1) * PAGE_SIZE;
  const visibleMatches = matches.slice(pageStart, pageStart + PAGE_SIZE);
  resultsCount.textContent = `${matches.length} match${matches.length === 1 ? "" : "es"}`;
  resultsContext.textContent = matches.length
    ? `Showing ${pageStart + 1}–${Math.min(pageStart + PAGE_SIZE, matches.length)} of ${matches.length} • ${formatTemperature(filters.coldest)} to ${formatTemperature(filters.hottest)} • ${STRESS_LABELS[filters.stress]}`
    : filters.savedOnly && !appState.savedIds.length
      ? "No inventory yet. Star rows to add products."
      : "No matches. Relax fixture time, clarity, warning filters, or the material pair.";

  activeTags.replaceChildren(
    ...buildActiveTags(filters).map((tag) => {
      const chip = document.createElement("span");
      chip.className = "active-tag";
      chip.textContent = tag;
      return chip;
    }),
  );

  resultsBody.replaceChildren();
  resultsEmpty.classList.add("hidden");

  if (!matches.length) {
    resultsEmpty.classList.remove("hidden");
    renderResultsPagination(0, 1);
    renderSavedGlues(matches, filters);
    return;
  }

  const fragment = document.createDocumentFragment();
  visibleMatches.forEach((match, index) => {
    const saved = appState.savedIds.includes(match.product.id);
    const row = document.createElement("tr");
    const mcmasterSummary = formatMcMasterSummary(match.product.mcmaster);
    const mcmasterChemistry = formatMcMasterChemistry(match.product.mcmaster);
    const productLinks = productSourceLinks(match.product);

    const scoreCell = document.createElement("td");
    const scorePill = document.createElement("span");
    scorePill.className = "score-pill rank-pill";
    scorePill.textContent = `#${(appState.resultPage - 1) * PAGE_SIZE + index + 1}`;
    scoreCell.append(scorePill);

    const fitACell = document.createElement("td");
    fitACell.className = "fit-cell";
    const fitLines = [];
    if (filters.substrateA !== "any") {
      fitLines.push(
        `<span><small>${materialLabel(filters.substrateA)}${match.materialFitIsProfileDerived.includes(filters.substrateA) ? ' <em class="field-evidence">Profile guide</em>' : ""}</small><strong>${formatFit(match.materialFits[filters.substrateA] ?? match.product.substrates[filters.substrateA] ?? 0)}</strong></span>`,
      );
    }
    if (filters.substrateB !== "any") {
      fitLines.push(
        `<span><small>${materialLabel(filters.substrateB)}${match.materialFitIsProfileDerived.includes(filters.substrateB) ? ' <em class="field-evidence">Profile guide</em>' : ""}</small><strong>${formatFit(match.materialFits[filters.substrateB] ?? match.product.substrates[filters.substrateB] ?? 0)}</strong></span>`,
      );
    }
    fitACell.innerHTML = fitLines.length
      ? fitLines.join("")
      : '<span class="empty-text">Any material</span>';

    const fitBCell = document.createElement("td");
    fitBCell.className = "visually-hidden";

    const productCell = document.createElement("td");
    productCell.className = "product-cell";
    const makerLabel = document.createElement("p");
    makerLabel.className = "maker";
    makerLabel.textContent = match.product.maker;
    const detailTrigger = document.createElement("button");
    detailTrigger.type = "button";
    detailTrigger.className = "product-name product-detail-trigger";
    detailTrigger.textContent = match.product.name;
    detailTrigger.setAttribute("aria-haspopup", "dialog");
    detailTrigger.setAttribute("aria-controls", "product-detail-dialog");
    detailTrigger.setAttribute(
      "aria-label",
      `Open details for ${match.product.maker} ${match.product.name}`,
    );
    detailTrigger.addEventListener("click", () =>
      openProductDetail(match.product, { ...match, filters }),
    );
    productCell.append(makerLabel, detailTrigger);
    if (mcmasterSummary) {
      const packageNote = document.createElement("p");
      packageNote.className = "table-note";
      packageNote.textContent = mcmasterSummary;
      productCell.append(packageNote);
    }

    const chemistryCell = document.createElement("td");
    const applicationText = formatApplicationTags(match.product.applicationTags, 2);
    chemistryCell.innerHTML = `
      <div class="product-chemistry">${match.product.chemistry}</div>
      ${mcmasterChemistry ? `<div class="table-note">${mcmasterChemistry}</div>` : ""}
      ${applicationText ? `<div class="table-note">${applicationText}</div>` : ""}
      <div class="table-note">${VISCOSITY_LABELS[match.product.viscosityClass] ?? "Not reported"}${match.product.profileDerivedFields.includes("viscosityClass") ? ' <em class="field-evidence">Profile guide</em>' : ""} • fixtures ${formatMinutes(match.product.fixtureTime)}${match.product.profileDerivedFields.includes("fixtureTime") ? ' <em class="field-evidence">Profile guide</em>' : ""}</div>
    `;

    const fixtureCell = document.createElement("td");
    fixtureCell.innerHTML = `
      <div>${formatTemperatureRange(match.product.serviceMin, match.product.serviceMax)}${match.product.profileDerivedFields.some((field) => ["serviceMin", "serviceMax"].includes(field)) ? ' <em class="field-evidence">Profile guide</em>' : ""}</div>
      <div class="table-note">${formatGap(match.product.gapFill)} gap${match.product.profileDerivedFields.includes("gapFill") ? ' <em class="field-evidence">Profile guide</em>' : ""} • ${formatLapShear(match.product.lapShear)} lap${match.product.profileDerivedFields.includes("lapShear") ? ' <em class="field-evidence">Profile guide</em>' : ""}</div>
    `;

    const tempCell = document.createElement("td");
    tempCell.textContent = formatTemperatureRange(
      match.product.serviceMin,
      match.product.serviceMax,
    );

    const viscosityCell = document.createElement("td");
    viscosityCell.textContent = VISCOSITY_LABELS[match.product.viscosityClass];

    const gapCell = document.createElement("td");
    gapCell.innerHTML = `
      <div>${formatGap(match.product.gapFill)}</div>
      <div class="product-summary">${formatLapShear(match.product.lapShear)} lap${
        match.product.mcmaster?.peelStrength ? ` • ${match.product.mcmaster.peelStrength} peel` : ""
      }</div>
    `;

    const costCell = document.createElement("td");
    costCell.className = "cost-cell";
    const costDetail = formatPricingDetail(match.product.pricing);
    costCell.innerHTML = `
      <div class="cost-main">${formatPricing(match.product.pricing)}</div>
      ${costDetail ? `<div class="product-summary">${costDetail}</div>` : ""}
    `;

    const reasonCell = document.createElement("td");
    if (match.reasons.length) {
      const reasonList = document.createElement("div");
      reasonList.className = "compact-list";
      match.reasons.forEach((reason) => {
        const item = document.createElement("span");
        item.textContent = reason;
        reasonList.append(item);
      });
      reasonCell.append(reasonList);
    } else {
      reasonCell.innerHTML = '<span class="empty-text">General fit</span>';
    }

    const warningCell = document.createElement("td");
    if (match.warnings.length) {
      warningCell.innerHTML = match.warnings
        .map((warning) => `<div class="warning-text">${warning}</div>`)
        .join("");
    } else {
      warningCell.innerHTML = '<span class="empty-text">None</span>';
    }
    if (match.warnings.length) {
      const warningList = document.createElement("div");
      warningList.className = "warning-list";
      match.warnings.forEach((warning) => {
        const item = document.createElement("span");
        item.textContent = warning;
        warningList.append(item);
      });
      reasonCell.append(warningList);
    }

    if (match.unverifiedRequirements?.length) {
      const verify = document.createElement("p");
      verify.className = "verification-note";
      verify.textContent = "Verify product-specific evidence for: " + match.unverifiedRequirements.join(", ") + ".";
      reasonCell.prepend(verify);
    }

    const actionCell = document.createElement("td");
    const actionWrap = document.createElement("div");
    actionWrap.className = "row-actions";
    const saveButton = document.createElement("button");
    saveButton.type = "button";
    saveButton.className = "button button-secondary button-table compare-toggle";
    saveButton.classList.toggle("is-selected", saved);
    saveButton.setAttribute("aria-pressed", String(saved));
    saveButton.textContent = saved ? "Saved" : "Star";
    saveButton.addEventListener("click", () => toggleSavedGlue(match.product.id));
    actionWrap.append(saveButton);
    productLinks.forEach(({ url, label, ariaLabel, kind }) => {
      const sourceLink = document.createElement("a");
      sourceLink.className = `action-secondary-link source-link source-link-${kind}`;
      sourceLink.href = url;
      sourceLink.target = "_blank";
      sourceLink.rel = "noreferrer";
      sourceLink.textContent = label;
      sourceLink.setAttribute("aria-label", ariaLabel);
      sourceLink.title = ariaLabel;
      actionWrap.append(sourceLink);
    });
    actionCell.append(actionWrap);

    row.append(
      scoreCell,
      productCell,
      fitACell,
      fitBCell,
      chemistryCell,
      fixtureCell,
      costCell,
      reasonCell,
      actionCell,
    );

    fragment.append(row);
  });

  resultsBody.append(fragment);
  renderResultsPagination(matches.length, pageCount);
  renderSavedGlues(matches, filters);
}

function renderResultsPagination(total, pageCount) {
  if (!resultsPagination) return;
  if (total <= PAGE_SIZE) { resultsPagination.replaceChildren(); return; }
  const button = (label, page, disabled = false, current = false) => {
    const item = document.createElement("button"); item.type = "button"; item.textContent = label; item.dataset.page = String(page);
    item.disabled = disabled; item.setAttribute("aria-current", current ? "page" : "false"); item.className = "page-button"; return item;
  };
  const pages = new Set([1, pageCount, appState.resultPage - 1, appState.resultPage, appState.resultPage + 1].filter((n) => n >= 1 && n <= pageCount));
  const nodes = [button("Previous", Math.max(1, appState.resultPage - 1), appState.resultPage === 1)]; let previous = 0;
  [...pages].sort((a,b) => a-b).forEach((page) => { if (page > previous + 1) { const dots = document.createElement("span"); dots.textContent = "…"; dots.className = "page-ellipsis"; nodes.push(dots); } nodes.push(button(String(page), page, false, page === appState.resultPage)); previous = page; });
  nodes.push(button("Next", Math.min(pageCount, appState.resultPage + 1), appState.resultPage === pageCount)); resultsPagination.replaceChildren(...nodes);
}

function scheduleRenderResults() {
  if (appState.renderFrame) return;
  appState.renderFrame = requestAnimationFrame(renderResults);
}

function toggleSavedGlue(productId) {
  if (appState.savedIds.includes(productId)) {
    appState.savedIds = appState.savedIds.filter((id) => id !== productId);
  } else {
    appState.savedIds = [...appState.savedIds, productId];
  }
  writeSavedGlueIds();
  scheduleRenderResults();
}

function renderSavedGlues(matches, filters) {
  const selected = appState.savedIds
    .map((id) => {
      const visibleMatch = matches.find((match) => match.product.id === id);
      if (visibleMatch) return { ...visibleMatch, outsideFilters: false };

      const product = GLUES.find((glue) => glue.id === id);
      if (!product) return null;

      const rescored = scoreProduct(product, filters);
      if (rescored) return { ...rescored, outsideFilters: false };

      return {
        product,
        score: 0,
        outsideFilters: true,
      };
    })
    .filter(Boolean);

  compareState.replaceChildren();

  if (!selected.length) {
    compareState.innerHTML = "<p>No inventory yet.</p><p>Star a row to add it.</p>";
    return;
  }
  const shell = document.createElement("div");
  shell.className = "compare-table-shell";

  const table = document.createElement("table");
  table.className = "compare-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>Product</th>
        <th>Current filter status</th>
        <th>Temperature</th>
        <th>Fixture</th>
        <th>Cost</th>
        <th>Remove</th>
      </tr>
    </thead>
    <tbody></tbody>
  `;

  const tbody = table.querySelector("tbody");

  selected.forEach((match) => {
    const row = document.createElement("tr");
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "button button-ghost button-table";
    remove.textContent = "Remove";
    remove.addEventListener("click", () => toggleSavedGlue(match.product.id));

    row.innerHTML = `
      <td>
        <div class="maker">${match.product.maker}</div>
        <div class="product-name">${match.product.name}</div>
      </td>
      <td>${match.outsideFilters ? "Outside current filters" : "Not excluded by current filters"}</td>
      <td>${formatTemperatureRange(match.product.serviceMin, match.product.serviceMax)}</td>
      <td>${formatMinutes(match.product.fixtureTime)}</td>
      <td>${formatPricing(match.product.pricing)}</td>
      <td></td>
    `;
    row.lastElementChild.append(remove);
    tbody.append(row);
  });

  shell.append(table);
  compareState.append(shell);
}

function attachEvents() {
  document.querySelector("#catalog-toggle")?.addEventListener("click", () => setCatalogView(true));
  document.querySelector("#catalog-back")?.addEventListener("click", () => setCatalogView(false));
  productDetailClose?.addEventListener("click", () => {
    if (typeof productDetailDialog.close === "function") productDetailDialog.close();
    else productDetailDialog.removeAttribute("open");
  });
  productDetailDialog?.addEventListener("click", (event) => {
    if (event.target === productDetailDialog) {
      if (typeof productDetailDialog.close === "function") productDetailDialog.close();
      else productDetailDialog.removeAttribute("open");
    }
  });
  filterForm.addEventListener("input", () => { appState.resultPage = 1; scheduleRenderResults(); });
  filterForm.addEventListener("change", () => { appState.resultPage = 1; scheduleRenderResults(); });
  resultsSearch?.addEventListener("input", () => { appState.resultPage = 1; scheduleRenderResults(); });
  resultsSort?.addEventListener("change", () => { appState.resultPage = 1; scheduleRenderResults(); });
  resultsPagination?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-page]");
    if (!button) return;
    appState.resultPage = Number(button.dataset.page);
    renderResults();
    document.querySelector("#results-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  stressButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setStressMode(button.dataset.value);
      scheduleRenderResults();
    });
  });

  resetFiltersButton.addEventListener("click", () => {
    resetAllFilters();
    scheduleRenderResults();
  });

  resetHeroButton.addEventListener("click", () => {
    resetAllFilters();
    scheduleRenderResults();
  });

  presetButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const preset = PRESETS[button.dataset.preset];
      if (!preset) return;
      setFormValues(preset);
      scheduleRenderResults();
      document.querySelector("#lab").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  referenceSearch?.addEventListener("input", () => { appState.referencePage = 1; renderReferenceLibrary(); });
  referenceCategorySelect?.addEventListener("change", () => { appState.referencePage = 1; renderReferenceLibrary(); });
  referenceApplicationSelect?.addEventListener("change", () => { appState.referencePage = 1; renderReferenceLibrary(); });
  document.querySelector("#reference-pagination")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-reference-page]");
    if (!button) return;
    appState.referencePage = Number(button.dataset.referencePage);
    renderReferenceLibrary();
  });
}

async function loadSelectorCatalog() {
  try {
    const response = await fetch("./data/selector-catalog.json?v=tds-evidence-20260923");
    if (!response.ok) throw new Error(`Catalog request failed: ${response.status}`);
    const catalog = await response.json();
    ingestSelectorProducts(catalog.tdsProducts ?? []);
    ingestSelectorProducts(catalog.mcmasterProducts ?? []);
    MCMASTER_PIPELINE_STATS = catalog.mcmasterStats ?? MCMASTER_PIPELINE_STATS;
    TDS_MANUAL_STATS = catalog.tdsStats ?? TDS_MANUAL_STATS;
    repopulateCatalogFilters();
    populateReferenceFilters();
    renderReferenceLibrary();
    renderHeroStats();
    scheduleRenderResults();
  } catch (error) {
    console.warn(error);
    glueDensity.textContent = `${GLUES.length} products`;
  }
}

function scheduleCatalogLoad() {
  const load = () => loadSelectorCatalog();
  const loadAfterFirstPaint = () => {
    window.setTimeout(() => {
      if ("requestIdleCallback" in window) {
        window.requestIdleCallback(load, { timeout: 1200 });
        return;
      }
      load();
    }, 250);
  };

  if (document.readyState === "complete") {
    loadAfterFirstPaint();
    return;
  }
  window.addEventListener("load", loadAfterFirstPaint, { once: true });
}

function init() {
  populateFilters();
  populateReferenceFilters();
  renderReferenceLibrary();
  resetAllFilters();
  attachEvents();
  renderHeroStats();
  scheduleRenderResults();
  scheduleCatalogLoad();
}

init();
