# hrd-models
This repo holds the scientific source code orchestrated by the `analyze-hrd-dna` node to determine the HRD status for HRD reports and data products. For more information on the data products generated, please see the [order-level](https://github.com/tempuslabs/data-products-service/blob/master/data-product-specs/hrd-dna-analysis) and [gene-level](https://github.com/tempuslabs/data-products-service/blob/master/data-product-specs/hrd-dna-analysis-gene-mutation) specs in the DPS repo. 

## Installation
Before you begin, you will need `python 3.7.1` installed. Once you have it installed make sure you also have poetry installed,
you can install poetry with python by using the command:
```
make init
```

Once you have poetry installed, run:
```
make install
```
To install all the dependencies for this repo.

## Code structure

### hrd-models
The hrd-models repo is meant to house all scientific code for all HRD models going forward. Today, this consists of an HRD predictor for DNA, `dna_predictor`. In the future, it will likely contain an `rna_predictor` as well. For now, the `hrd-models` repo contains a `dna_predictor` and `tests` (unit tests).

This directory is published to nexus [here](https://nexus.opstempus.com/#browse/browse:pypi-internal:hrd-models) and is available via pip:
```pip install --extra-index-url https://nexus.opstempus.com/repository/pypi-internal/simple hrd-models```

#### Tests
All tests can be run using the command:
```
make test
```

#### DNA Predictor
The DNA predictor of HRD is based on cancer cohort, BRCA ([interested_genes](https://github.com/tempuslabs/hrd-models/blob/42154b607b7770c69a74e79c20fe4defd18984d0/hrd_models/dna_predictor/constants.py#L5)) status, and genome-wide loss-of-heterozygosity (gwLOH) score. 
For the full experimental validation of this assay, please see [NGS.4.125](https://tempus.etq.com/prod/rel/#/app/system/document/DOCWORK/DOCWORK_DOCUMENT/638). Within `dna_predictor` are scripts for [copy number calculations](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py), [variant parsing](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/variant_parser.py) and a [unified script](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py) to compile all data to make an DNA-based HRD call. 

For an example of how to use the DNAPredictor class, please see the [test.py](https://github.com/tempuslabs/hrd-models/blob/develop/test.py) script. In short, the `reported-dna-variants` DP, `dna_variant` and `dna_cnv_v2` bioinformatics files are required. 

For a patient to be called HRD+, either:
1. The DNA analysis has evidence of two alterations in interested genes, described in detail [here](https://github.com/tempuslabs/hrd-models/blob/42154b607b7770c69a74e79c20fe4defd18984d0/hrd_models/dna_predictor/dna_predictor.py#L260).
2. The DNA analysis has a gwLOH greater than the cancer cohort-specific [threshold](https://github.com/tempuslabs/hrd-models/blob/42154b607b7770c69a74e79c20fe4defd18984d0/hrd_models/dna_predictor/thresholds.py#L24). 

#### Validation
The code in this directory was used for backfill and validation. Please ignore.

## Data Generated

### hrd-dna-analysis
This data is meant to summarize high level, `order_id` grain data for an HRD report. From this data, users can see why a patient was called HRD+/- based on their gwLOH, or mutation status of `interested_genes` (BRCA1/2). Other helpful information for pathologists signing out HRD reports is included. 

`cancer_cohort`: The cancer cohort given by pathology in LIMS during pathology review.  

`genome_wide_loh_proportion_inclusive` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py#L8)): Genome-wide LOH (inclusive of aneuploidy) for the given analysis. This metric is clinically validated and should be used primarily for any clinical applications.

`genome_wide_loh_proportion_exclusive` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py#L28)):  Genome-wide LOH (exclusive of aneuploidy) for the given analysis. This metric is clinically validated and should be used primarily for any clinical applications. 

`lost_chromosome_arms_count` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py#L82)): Integer value in range (0 -> 42) and represents the number of autosomal chromosome arms lost in the tumor. This metric is not validated.

`pathogenic_var_count` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L133)): The number of pathogenic SNPs / indels called on the report in reported genes

`single_hit_interested_genes` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L218)): Boolean whether there is a single-hit in any gene in interested genes (genes that trigger double-hit logic) 

`double_hit_interested_genes` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L217)): Boolean whether there is a double-hit in any gene in interested genes (genes that trigger double-hit logic)

`single_hit_reported_genes` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L220)): Boolean whether there is a single-hit in any gene in reported genes (genes that are on the HRD report)

`double_hit_reported_genes` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L219)): Boolean whether there is a double-hit in any gene in reported genes (genes that are on the HRD report)

`hrd_cohort` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L227)): Positive (two hits in any of the interested_genes), negative (no single hits in interested_genes and no double hits in reported_genes), or intermediate (single hit in interested_genes)

### hrd-dna-analysis-gene-mutation
This data is meant to summarize `order_id` + `gene` grain data for an HRD report. From this data, users can see which gene alterations are present or absent for a given order / gene combination. If users want to know which genes in the `hrd-dna-analysis` are responsible for a positive HRD call, this table can provide the underlying data that supports the overall call. If you are exploring other definitions for HRD+/- for other models or features besides BRCA double-hit vs. BRCA WT, this data can be used to help redefine your labels. If you have ideas for how to improve HRD labels for modeling, please reach out to one of the code owners.

`gene`: HGNC symbol for the reported gene

`somatic_pathogenic_count` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L151)): The number of pathogenic somatic mutations

`germline_pathogenic_count` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L155)): The number of pathogenic germline mutations

`somatic_vus_count` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L159)): The number of somatic mutations with unknown significance

`germline_vus_count` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L162)): The number of germline mutations with unknown significance

`loh_reported`: Copy loss was reported due to loss-of-heterozygosity in the given gene

`loh_reportable` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py#L206)): Copy loss was reportable due to loss-of-heterozygosity in the given gene, based on automated clinical science rules

`loh_proportion` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py#L128)): The percent of bases in the gene with evidence of loss-of-heterozygosity

`vaf_difference` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py#L254)): The maximum difference between the somatic and germline variant allele frequencies for a reported germline mutation

`deep_loss_reported` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/variant_parser.py#L48)): Copy loss was reported due to homozygous deletion in the given gene

`deep_loss_reportable` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py#L186)): Copy loss was reportable due to homozygous deletion in the given gene, based on automated clinical science rules

`deep_loss_proportion` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py#L167)): The percent of bases in the gene with evidence of homozygous deletion

`deep_loss_probes` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/copy_number_calculations.py#L171)): The number of probe regions in the gene with evidence of homozygous deletion

`interested_gene` ([list](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/constants.py#L4)): If the reported is also an 'interested_gene'. If a double-hit is detected in this gene, HRD+ will be flagged

`single_hit` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L290)): Binary - whether there is a single hit in the given gene - includes LOH / VUS / or a single pathogenic mutation

`double_hit` ([calculation](https://github.com/tempuslabs/hrd-models/blob/develop/hrd_models/dna_predictor/dna_predictor.py#L259)): Binary - whether the analyses meets the double-hit logic criteria in the given gene

`cancer_cohort`: LIMS cancer cohort

Note: ** For determining whether a specific gene / alteration pair should be reported, only the `_reported` values should be used. All other values are for informational purposes only. **
