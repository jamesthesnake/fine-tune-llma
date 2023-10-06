from hrd_models.dna_predictor.constants import HRD_METRIC
from hrd_models.dna_predictor.copy_number_calculations import calculate_loh_percent_exclusive
from hrd_models.dna_predictor.thresholds import thresholds
from hrd_models.rna_predictor.constants import HRD_SCORE_THRESHOLD
from hrd_models.rna_predictor.rna_predictor import RNAPredictor
import multiprocessing as mp
import os
import pandas as pd
from tdsu import build_connection



def get_dna_metadata(metadata):
    n = build_connection(os.environ.get("AWS_USER", ""), os.environ.get("AWS_PROFILE_DEVOPS", ""))

    dna_meta = pd.read_sql(
        f"""
    
    select distinct analysis_id
                  , case 
                        when cancer_cohort in {tuple(thresholds.cancer_cohort)} 
                        then cancer_cohort else 'Pan Cancer' end as cancer_cohort
                  , url
                  , assay
                  , match_type
    from src_bioinformatics.analysis_output ao
    inner join src_bioinformatics.analysis a
        on a.id = ao.analysis_id
    where type = 'dna_cnv_v2'
        and analysis_id in {tuple(metadata.bio_analysis_id)}
    
    """,
        n,
    ).merge(thresholds)

    dna_meta = dna_meta[dna_meta.hrd_metric == HRD_METRIC].reset_index(drop=True)

    return dna_meta


def get_rna_metadata(metadata):
    n = build_connection(os.environ.get("AWS_USER", ""), os.environ.get("AWS_PROFILE_DEVOPS", ""))

    rna_meta = pd.read_sql(
        f"""
    
    select distinct a.patient_id
                  , sample_id
                  , ao.analysis_id
                  , case 
                        when cancer_cohort in {tuple(thresholds.cancer_cohort)} 
                        then cancer_cohort else 'Pan Cancer' end as cancer_cohort
                  , url
                  , a.assay
                  , a.match_type
                  , 'rna' as hrd_metric
                  , {HRD_SCORE_THRESHOLD}    as threshold
    from src_bioinformatics.analysis_output ao
    inner join src_bioinformatics.analysis a
        on a.id = ao.analysis_id
    inner join clinical_mart_v1_2.vw_molecular_inventory_rna_analysis using (analysis_id)
    where type = 'rna_expression_abundance'
        and analysis_id in {tuple(metadata.bio_analysis_id)}
    
    """,
        n,
    )

    return rna_meta


def get_gw_loh(cnv_output):

    # Download CNV output
    cnv_output = cnv_output[0][1]
    cnv_file = pd.read_csv(cnv_output.url)

    # Run gwLOH function from copy_number_calculations
    try:
        loh_percent_exclusive = calculate_loh_percent_exclusive(cnv_file)
    except:
        loh_percent_exclusive = np.nan

    gw_loh = pd.DataFrame.from_dict(
        {
            "analysis_id": [cnv_output.analysis_id],
            "hrd_score": [loh_percent_exclusive],
            "analyte": ["dna"],
            "hrd_call": [
                "Positive" if loh_percent_exclusive > cnv_output.threshold else "Not Detected"
            ],
        }
    )

    return gw_loh


def get_rna_hrd(metadata):

    # Make RNA prediction
    abundance = pd.read_csv(metadata.url, sep="\t")
    rnap = RNAPredictor()
    prediction = rnap.predict(
        data=abundance,
        patient_id=metadata.patient_id,
        sample_id=metadata.sample_id,
        assay=metadata.assay,
    )

    rna = pd.DataFrame.from_dict(
        {
            "analysis_id": [metadata.analysis_id],
            "hrd_score": [prediction.analysis.hrd_score],
            "analyte": ["rna"],
            "hrd_call": [
                "Positive" if prediction.analysis.hrd_score > HRD_SCORE_THRESHOLD else "Not Detected"
            ],
        }
    )

    return rna


def main(metadata_file: str, output_file: str):

    metadata = pd.read_csv(metadata_file)
    dna_metadata = get_dna_metadata(metadata)
    rna_metadata = get_rna_metadata(metadata)

    pool = mp.Pool(mp.cpu_count())
    dna_hrd_scores = pool.map(get_gw_loh, zip(list(dna_metadata.iterrows())))
    pool.close()

    dna_hrd_scores = pd.concat(dna_hrd_scores).reset_index(drop=True)
    dna_hrd_scores = dna_metadata.merge(dna_hrd_scores)

    rna_hrd_scores = pd.DataFrame()
    for i, row in rna_metadata.iterrows():
        rna_hrd_scores = rna_hrd_scores.append(rna_metadata.merge(get_rna_hrd(row)))
    rna_hrd_scores = rna_hrd_scores.drop(columns=["patient_id", "sample_id"]).reset_index(drop=True)

    hrd_scores = dna_hrd_scores.append(rna_hrd_scores)
    hrd_scores.to_csv(output_file, index=False)

    print(dna_hrd_scores.shape)


if __name__ == "__main__":
    main(
        "/data/analysis/hrd/pharma/bms/Original PARP Cohort - BMS - Sheet1.csv",
        "/data/analysis/hrd/pharma/bms/hrd_scores.csv",
    )
